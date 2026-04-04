"""
Quick verification script to check if the setup is correct.
Run this after installing dependencies to verify everything works.
"""
import sys


def verify_imports():
    """Verify all required packages can be imported."""
    print("Checking imports...")
    
    try:
        import fastapi
        print("✓ FastAPI installed")
    except ImportError:
        print("✗ FastAPI not found")
        return False
    
    try:
        import sqlalchemy
        print("✓ SQLAlchemy installed")
    except ImportError:
        print("✗ SQLAlchemy not found")
        return False
    
    try:
        import pydantic_settings
        print("✓ Pydantic Settings installed")
    except ImportError:
        print("✗ Pydantic Settings not found")
        return False
    
    return True


def verify_config():
    """Verify configuration loads correctly."""
    print("\nChecking configuration...")
    
    try:
        from app.config import settings
        print(f"✓ Configuration loaded")
        print(f"  - Database URL: {settings.database_url}")
        print(f"  - API Title: {settings.api_title}")
        print(f"  - Debug Mode: {settings.debug}")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False


def verify_database():
    """Verify database connection and models."""
    print("\nChecking database...")
    
    try:
        from app.db.database import engine, init_db
        from app.models import Candidate
        
        # Initialize database
        init_db()
        print("✓ Database initialized")
        print("✓ Models loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 50)
    print("Resume Matching System - Setup Verification")
    print("=" * 50)
    
    checks = [
        verify_imports(),
        verify_config(),
        verify_database()
    ]
    
    print("\n" + "=" * 50)
    if all(checks):
        print("✓ All checks passed! Setup is complete.")
        print("Run: uvicorn app.main:app --reload")
        sys.exit(0)
    else:
        print("✗ Some checks failed. Please review the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
