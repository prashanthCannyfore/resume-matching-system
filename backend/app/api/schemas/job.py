from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class JobBase(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    required_skills: Optional[List[str]] = []
    min_experience: Optional[int] = None
    required_education: Optional[str] = None
    description_text: Optional[str] = None


class JobCreate(JobBase):
    pass


class JobResponse(JobBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
