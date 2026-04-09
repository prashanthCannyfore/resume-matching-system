from sqlalchemy import Column, Integer, String, Text, Float, DateTime, func
from sqlalchemy.dialects.postgresql import ARRAY
from app.core.database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    location = Column(String(100))
    
    # Structured data
    skills = Column(ARRAY(String), default=list)
    experience_years = Column(Integer)
    education = Column(String(200))
    certifications = Column(ARRAY(String), default=list)
    
    # Raw resume text for embedding
    resume_text = Column(Text)
    
    # AI Embedding (vector)
    embedding = Column(Text)  # Will store JSON string of vector for MVP
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())