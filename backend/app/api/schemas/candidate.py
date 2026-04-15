from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CandidateBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = []
    experience_years: Optional[int] = None
    education: Optional[str] = None
    certifications: List[str] = []
    resume_text: Optional[str] = None

class CandidateCreate(CandidateBase):
    pass

class CandidateResponse(CandidateBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True