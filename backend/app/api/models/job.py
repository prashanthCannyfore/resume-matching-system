from sqlalchemy import Column, Integer, String, Text, Float, DateTime, func
from sqlalchemy.dialects.postgresql import ARRAY
from app.core.database import Base
from sqlalchemy.types import JSON
class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    company = Column(String(100))
    location = Column(String(100))
    required_skills = Column(JSON, default=list)
    min_experience = Column(Integer)
    required_education = Column(String(200))
    
    description_text = Column(Text)
    embedding = Column(Text)  # JSON string of embedding vector
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())