from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class JobBase(BaseModel):
    title: str  # REQUIRED
    description_text: str  # REQUIRED
    company: Optional[str] = None
    location: Optional[str] = None
    required_skills: Optional[List[str]] = []
    min_experience: Optional[int] = None
    required_education: Optional[str] = None


class JobCreate(JobBase):
    pass


class JobResponse(JobBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
