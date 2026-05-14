import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:x@localhost:5432/resume_db"
os.environ.setdefault("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
os.environ.setdefault("OLLAMA_EMBED_MODEL", "nomic-embed-text")
os.environ.setdefault("OLLAMA_LLM_MODEL", "llama3.2:3b")
os.environ.setdefault("OLLAMA_TIMEOUT", "90.0")
os.environ.setdefault("OLLAMA_CONTEXT_LENGTH", "2048")
os.environ.setdefault("OLLAMA_EMBED_CONCURRENCY", "2")

from app.api.services.parser import normalize_skill_name

tests = [
    ".net", "asp.net", "node.js", "react developer",
    "senior react developer", "frontend react", "mern", "mern stack",
    "next.js", "react.js", "full stack", "fullstack", "full-stack",
    "react", "reactjs", "React.js",
]
print("=== normalize_skill_name edge cases ===")
for t in tests:
    print(f"  {t!r:35} -> {normalize_skill_name(t)!r}")
