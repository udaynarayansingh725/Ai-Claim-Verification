from pydantic import BaseModel
from typing import List

class WSRequest(BaseModel):
    content: str

class SourceSchema(BaseModel):
    title: str
    url: str
    snippet: str

class VerificationResult(BaseModel):
    verdict: str
    confidence: float
    reasoning: str
    conflicting_sources: bool
    best_source_url: str = ""

class ClaimResult(BaseModel):
    claim_id: str
    text: str
    verdict: str
    confidence: float
    reasoning: str
    conflicting: bool
    sources: List[SourceSchema]

class FinalReport(BaseModel):
    report_id: str
    overall_score: float
    ai_text_probability: float
    total_claims: int
    true_claims: int
    false_claims: int
    partial_claims: int
    unverifiable_claims: int

class DetectionResult(BaseModel):
    result: str
    confidence: float
    signals: List[str]
    processing_time_ms: int

class TextRequest(BaseModel):
    text: str
