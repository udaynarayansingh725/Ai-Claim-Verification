from sqlalchemy import Column, String, Float, Text, Boolean, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from sqlalchemy.orm import relationship
from app.db.database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    input_text = Column(Text, nullable=False)
    source_url = Column(Text, nullable=True)
    overall_score = Column(Float, nullable=True)
    ai_text_probability = Column(Float, nullable=True)
    created_at = Column(TIMESTAMP(timezone=False), server_default=func.now(), nullable=False)
    
    claims = relationship("Claim", back_populates="report", cascade="all, delete-orphan")

class Claim(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False)
    claim_text = Column(Text, nullable=False)
    verdict = Column(String(20), nullable=True) # "True", "False", "Partially True", "Unverifiable"
    confidence = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)
    sources = Column(JSONB, nullable=True) # array of {title, url, snippet}
    conflicting = Column(Boolean, default=False, nullable=True)

    report = relationship("Report", back_populates="claims")
