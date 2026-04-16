from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class JobBase(BaseModel):
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    required_skills: List[str] = []
    min_experience: Optional[int] = None
    required_education: Optional[str] = None
    description_text: str


class JobCreate(JobBase):
    pass


class JobResponse(JobBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
