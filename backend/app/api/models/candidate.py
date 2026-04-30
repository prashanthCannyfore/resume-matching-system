from sqlalchemy import Column, Integer, String, Text, Float, DateTime, func
from sqlalchemy.dialects.postgresql import ARRAY
from app.core.database import Base
from sqlalchemy.types import JSON


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=True)  # Allow NULL emails
    phone = Column(String(20), nullable=True)
    location = Column(String(100), nullable=True)
    skills = Column(JSON, default=list)
    experience_years = Column(Integer, default=0)
    education = Column(String(200), nullable=True)
    certifications = Column(JSON, default=list)
    resume_text = Column(Text)
    # AI Embedding
    # Using sentence-transformers/all-MiniLM-L6-v2 → 384 dimension vector
    # Stored as JSON string for MVP (converted using json.dumps)
    # AI Embedding (vector)
    embedding = Column(Text)  # Will store JSON string of vector for MVP

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
