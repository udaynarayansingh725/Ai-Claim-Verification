from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Set
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
import json
from app.services.pipeline import run_pipeline
from app.core.logger import get_logger

logger = get_logger(__name__)

ws_router = APIRouter()

active_sessions: Set[str] = set()

@ws_router.websocket("/ws/verify")
async def verify_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    
    session_id = str(id(websocket))
    if session_id in active_sessions:
        logger.warning(f"Duplicate websocket session attempted: {session_id}")
        await websocket.send_json({"event": "error", "message": "Duplicate request"})
        await websocket.close()
        return
        
    active_sessions.add(session_id)
    logger.info(f"WebSocket session connected: {session_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"[{session_id}] Received WebSocket data: {data[:100]}...")
            try:
                payload = json.loads(data)
                content = payload.get("content", "")
                user_api_key = payload.get("api_key", None)
            except json.JSONDecodeError:
                content = data
                user_api_key = None
                
            async def emit(event_data: dict):
                try:
                    await websocket.send_json(event_data)
                except Exception:
                    pass # ignore close errors
                    
            await run_pipeline(db, content, emit, user_api_key)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket session disconnected: {session_id}")
    except Exception as e:
        logger.error(f"[{session_id}] WebSocket error: {str(e)}")
        try:
            await websocket.send_json({"event":"error","message":str(e)})
        except Exception:
            pass
    finally:
        active_sessions.discard(session_id)
        try:
            await websocket.close()
        except Exception:
            pass
