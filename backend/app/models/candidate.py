"""
Candidate model for storing resume and candidate information.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class Candidate(Base):
    """
    Candidate model representing a job applicant.
    
    Attributes:
        id: Primary key
        name: Candidate's full name
        email: Candidate's email address (unique)
        resume_text: Full text content of the resume
        skills: Comma-separated list of skills
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    resume_text = Column(Text, nullable=False)
    skills = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<Candidate(id={self.id}, name='{self.name}', email='{self.email}')>"
