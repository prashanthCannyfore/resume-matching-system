# Resume Matching System

AI-powered resume matching system using RAG (Retrieval-Augmented Generation) and intelligent filtering.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy
- **Frontend**: Vue.js
- **Vector Search**: FAISS
- **Database**: SQLite (development), PostgreSQL (production-ready)

## Features

- Resume upload and parsing
- AI-powered candidate matching
- Intelligent candidate ranking
- Feedback and rating system

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── db/          # Database configuration
│   │   ├── models/      # SQLAlchemy models
│   │   ├── routes/      # API endpoints
│   │   ├── services/    # Business logic
│   │   ├── utils/       # Helper functions
│   │   ├── config.py    # Application settings
│   │   └── main.py      # FastAPI application
│   ├── .env             # Environment variables
│   └── requirements.txt # Python dependencies
├── frontend/            # Vue.js application
└── docs/               # Documentation

```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

### Database Migrations

The database is automatically initialized on application startup. Tables are created based on SQLAlchemy models.

### Code Quality

- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Use type hints for better code clarity
- Keep functions focused and modular

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./resume_matching.db` |
| `API_TITLE` | API title | `Resume Matching System` |
| `API_VERSION` | API version | `1.0.0` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000,http://localhost:8080` |
| `DEBUG` | Debug mode | `True` |

## License

MIT