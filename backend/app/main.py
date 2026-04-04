"""
Main FastAPI application entry point.
Configures the API, middleware, and initializes the database.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import init_db

# Initialize FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    debug=settings.debug
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    init_db()


@app.get("/", tags=["Health"])
def root():
    """
    Root endpoint for health check.
    
    Returns:
        dict: Welcome message and API status
    """
    return {
        "message": "Resume Matching System is running! 🚀",
        "version": settings.api_version,
        "status": "healthy"
    }