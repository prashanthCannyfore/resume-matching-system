from sqlalchemy import Column, Integer, String
from app.core.database import Base

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)