from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    name: str
    api_key: str | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_admin: bool
    api_key: str | None = None


class ApiKeyResponse(BaseModel):
    api_key: str


class ClaimRequest(BaseModel):
    claim: str = Field(min_length=10, max_length=1000)


class UrlVerificationRequest(BaseModel):
    url: str = Field(min_length=10, max_length=2083)


class TextDetectRequest(BaseModel):
    text: str = Field(min_length=30, max_length=20000)


class EvidenceItem(BaseModel):
    source: str
    title: str
    snippet: str
    url: str | None = None
    similarity: float
    stance: str = "NEUTRAL"


class SentenceAnalysisItem(BaseModel):
    text: str
    score: float
    is_ai: bool
    reasons: list[str] = []


class AnalysisResponse(BaseModel):
    id: int | None = None
    analysis_type: str
    verdict: str
    confidence: float
    signals: list[str]
    evidence: list[EvidenceItem] = []
    sentence_analysis: list[SentenceAnalysisItem] = []
    ela_heatmap: str | None = None


class BatchClaimRequest(BaseModel):
    claims: list[str] = Field(min_length=1, max_length=50)


class BatchAnalysisResponse(BaseModel):
    total_processed: int
    results: list[AnalysisResponse]
