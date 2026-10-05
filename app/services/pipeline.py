import asyncio
from typing import Callable, Any, Dict
from app.services.scraper import scrape_content, is_url
from app.services.claim_extractor import extract_claims
from app.services.search_agent import search_for_claim
from app.services.verifier import verify_claim
from app.services.ai_detector import detect_ai
from app.services.reporter import save_report
from app.schemas.api import ClaimResult, SourceSchema
from sqlalchemy.ext.asyncio import AsyncSession
import traceback
from app.core.logger import get_logger

logger = get_logger(__name__)

async def run_pipeline(
    db: AsyncSession,
    content: str,
    emit: Callable[[Dict[str, Any]], Any],
    api_key: str = None
):
    try:
        logger.info("Starting fact-checking pipeline execution")
        is_url_input = is_url(content)
        source_url = None
        
        if is_url_input:
            logger.debug("Input identified as URL. Starting scraping.")
            await emit({"event":"stage","stage":"scraping","progress":0.05})
            extracted_text = await asyncio.to_thread(scrape_content, content)
            import re
            match = re.search(r'https?://[^\s]+', content)
            source_url = match.group(0) if match else None
        else:
            extracted_text = content
            
        logger.debug("Finished scraping. Extracting claims.")
        await emit({"event":"stage","stage":"extracting","progress":0.15})
        
        # Run AI detection concurrently
        ai_task = asyncio.create_task(detect_ai(extracted_text, api_key))
        
        # Extract claims
        claims_text = await extract_claims(extracted_text, api_key)
        logger.info(f"Extracted {len(claims_text)} claims from content")
        
        claim_objects = []
        for i, text in enumerate(claims_text):
            c_id = f"c_{i+1:03d}"
            claim_objects.append({"id": c_id, "text": text})
            await emit({"event":"claim_found","claim_id":c_id,"text":text})
            
        if not claim_objects:
            logger.warning("No claims found in content. Pipeline aborting early.")
            ai_result = await ai_task
            await emit({"event":"report_done","report_id":"none","overall_score":0.0,
               "ai_text_probability":ai_result.get("ai_probability", 0.0),"total_claims":0,
               "true":0,"false":0,"partial":0,"unverifiable":0, "claims": []})
            return

        await emit({"event":"stage","stage":"searching","progress":0.35})
        
        verifying_emitted = False
        emit_lock = asyncio.Lock()
        
        async def process_claim(claim_obj: Dict[str, str]) -> ClaimResult:
            nonlocal verifying_emitted
            c_id = claim_obj["id"]
            text = claim_obj["text"]
            
            logger.debug(f"Processing claim: {c_id}")
            # Step 2: Search
            query, sources = await search_for_claim(text, api_key)
            await emit({
                "event":"search_done",
                "claim_id":c_id,
                "search_query":query,
                "sources_found":len(sources),
                "sources":[SourceSchema(**s).model_dump() for s in sources]
            })
            
            async with emit_lock:
                if not verifying_emitted:
                    await emit({"event":"stage","stage":"verifying","progress":0.5})
                    verifying_emitted = True
            
            # Step 3: Verify
            verification = await verify_claim(text, sources, api_key)
            source_schemas = [SourceSchema(**s) for s in sources]
            
            result = ClaimResult(
                claim_id=c_id,
                text=text,
                verdict=verification.get("verdict", "Unverifiable"),
                confidence=verification.get("confidence", 0.0),
                reasoning=verification.get("reasoning", ""),
                conflicting=verification.get("conflicting_sources", False),
                sources=source_schemas
            )
            
            logger.debug(f"Verified claim {c_id}: Verdict={result.verdict}, Conf={result.confidence:.2f}")
            
            await emit({
                "event":"claim_verified",
                "claim_id":c_id,
                "verdict":result.verdict,
                "confidence":result.confidence,
                "reasoning":result.reasoning,
                "conflicting":result.conflicting,
                "sources":[s.model_dump() for s in result.sources]
            })
            
            return result

        tasks = [process_claim(c) for c in claim_objects]
        claim_results = await asyncio.gather(*tasks)
        
        ai_result = await ai_task
        ai_prob = ai_result.get("ai_probability", 0.0)
        
        report_id = await save_report(db, extracted_text, source_url, ai_prob, claim_results)
        
        stats = {"True": 0, "False": 0, "Partially True": 0, "Unverifiable": 0}
        for r in claim_results:
            if r.verdict in stats:
                stats[r.verdict] += 1
            else:
                stats["Unverifiable"] += 1
                
        from app.services.reporter import calculate_score
        overall_score = calculate_score(claim_results)
        logger.info(f"Generated report {report_id} with Overall Score: {overall_score:.2f}")
        
        claims_payload = [{
            "claim_id": r.claim_id,
            "reasoning": r.reasoning,
            "true": 1 if r.verdict == "True" else 0,
            "false": 1 if r.verdict == "False" else 0,
            "partial": 1 if r.verdict == "Partially True" else 0,
            "unverifiable": 1 if r.verdict == "Unverifiable" else 0,
            "sources_found": len(r.sources)
        } for r in claim_results]

        await emit({
            "event":"report_done",
            "report_id":report_id,
            "overall_score":overall_score,
            "ai_text_probability":ai_prob,
            "total_claims":len(claim_results),
            "true":stats["True"],
            "false":stats["False"],
            "partial":stats["Partially True"],
            "unverifiable":stats["Unverifiable"],
            "claims": claims_payload
        })

    except Exception as e:
        logger.error(f"Error in run_pipeline: {str(e)}\n{traceback.format_exc()}")
        await emit({"event":"error","message":str(e)})
