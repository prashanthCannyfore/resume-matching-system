from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.api.routers import router

app = FastAPI(
    title="Resume Matching System (RMS)",
    description="AI-Powered Resume & Job Matching Platform",
    version="0.1.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "✅ Resume Matching System API is running successfully!"}

# Create database tables on startup (Development only)
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created (if not exist)")