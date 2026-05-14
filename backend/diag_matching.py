"""Diagnose the exact skill matching failure for the React resume."""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
os.environ.setdefault("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
os.environ.setdefault("OLLAMA_EMBED_MODEL", "nomic-embed-text")
os.environ.setdefault("OLLAMA_LLM_MODEL", "llama3.2:3b")
os.environ.setdefault("OLLAMA_TIMEOUT", "90.0")
os.environ.setdefault("OLLAMA_CONTEXT_LENGTH", "2048")
os.environ.setdefault("OLLAMA_EMBED_CONCURRENCY", "2")

from app.api.services.parser import normalize_skill_name, normalize_skill_list

# ── What's stored in DB for the React candidate (id=13) ──────────────────────
candidate_skills_in_db = [
    'express.js', '.net', 'html', 'node.js', 'github', 'mysql', 'redux',
    'bootstrap', 'typescript', 'mui', 'sql', 'javascript', 'reactjs',
    'aws', 'nodejs', 'java', 'css', 'azure', 'asp.net', 'mongodb',
    'jenkins', 'react', 'git'
]

# ── What a typical JD stores after extraction ─────────────────────────────────
jd_skills_variants = [
    ["react"],
    ["React"],
    ["react", "figma", "javascript"],
    ["ReactJS", "Node.js"],
    ["react developer"],
]

print("=== normalize_skill_name on candidate skills ===")
for s in candidate_skills_in_db:
    n = normalize_skill_name(s)
    if n != s.lower().replace(".", "").replace("-", ""):
        print(f"  {s!r:20} -> {n!r}")

print()
print("=== normalize_skill_list on candidate skills ===")
norm_cand = set(normalize_skill_list(candidate_skills_in_db))
print(f"  {sorted(norm_cand)}")

print()
print("=== intersection tests ===")
for jd in jd_skills_variants:
    norm_jd = set(normalize_skill_list(jd))
    matched = sorted(norm_cand & norm_jd)
    missing = sorted(norm_jd - norm_cand)
    score = round(len(matched) / len(norm_jd), 2) if norm_jd else 0
    print(f"  JD={jd}")
    print(f"    norm_jd={norm_jd}  matched={matched}  missing={missing}  score={score}")
    print()

# ── Simulate what extract_skills returns from raw resume text ─────────────────
print("=== extract_skills fallback scan on raw text ===")
raw_text = "ReactJS React.js React Developer MERN Stack Node.js JavaScript TypeScript"
text_lower = raw_text.lower()
text_lower = re.sub(r"[^a-z0-9\s\.\-]", " ", text_lower)
text_lower = re.sub(r"\s+", " ", text_lower).strip()

fallback_skills = [
    "react", "reactjs", "nodejs", "node.js", "javascript", "typescript",
    "redux", "vue", "angular", "bootstrap", "mui", "tailwind", "html", "css",
    "python", "java", "c#", ".net", "asp.net", "sql", "mysql", "postgresql",
    "mongodb", "redis", "aws", "azure", "docker", "kubernetes", "git",
    "jenkins", "ci/cd", "microservices", "rest api", "figma", "adobe xd",
    "ui/ux", "ux design"
]
found = [s for s in fallback_skills if s in text_lower]
print(f"  raw text: {raw_text!r}")
print(f"  found:    {found}")
print(f"  after normalize: {sorted(set(normalize_skill_list(found)))}")
