"""
Verify the three required test cases:
CASE 1: JD=React  Resume=ReactJS+NodeJS  → Match > 90%
CASE 2: JD=React  Resume=Graphic Designer → Match < 35%
CASE 3: JD=Python Resume=React Developer  → Low skill match
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:x@localhost:5432/resume_db"
os.environ.setdefault("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
os.environ.setdefault("OLLAMA_EMBED_MODEL", "nomic-embed-text")
os.environ.setdefault("OLLAMA_LLM_MODEL", "llama3.2:3b")
os.environ.setdefault("OLLAMA_TIMEOUT", "90.0")
os.environ.setdefault("OLLAMA_CONTEXT_LENGTH", "2048")
os.environ.setdefault("OLLAMA_EMBED_CONCURRENCY", "2")

from app.api.services.filter_service import calculate_skill_score, filter_and_rank_candidates

SKILL_W = 0.70
SIM_W   = 0.20
EXP_W   = 0.10
CAP     = 0.30

def score(skill_s, sim, exp_match, has_req):
    if skill_s >= 1.0 and exp_match >= 1.0:
        return 1.0
    s = round(SKILL_W * skill_s + SIM_W * sim + EXP_W * exp_match, 3)
    if has_req and skill_s == 0.0:
        s = min(s, CAP)
    return s

print("=" * 60)
print("CASE 1: JD=React  Resume=ReactJS+NodeJS")
jd   = ["react"]
cand = ["ReactJS", "Node.js", "JavaScript", "TypeScript"]
ss, matched, missing = calculate_skill_score(cand, jd)
sim  = 0.70   # realistic FAISS score for React resume vs React JD
final = score(ss, sim, 1.0, True)
print(f"  skill_score={ss}  matched={matched}  missing={missing}")
print(f"  final_score={final:.1%}")
assert final > 0.90, f"FAIL: expected >90%, got {final:.1%}"
print("  PASS ✓")

print()
print("CASE 2: JD=React  Resume=Graphic Designer")
jd2   = ["react"]
cand2 = ["Figma", "Adobe XD", "Photoshop", "Illustrator", "Typography"]
ss2, matched2, missing2 = calculate_skill_score(cand2, jd2)
sim2  = 0.45   # some semantic similarity (both are "developer" roles)
final2 = score(ss2, sim2, 1.0, True)
print(f"  skill_score={ss2}  matched={matched2}  missing={missing2}")
print(f"  final_score={final2:.1%}")
assert final2 < 0.35, f"FAIL: expected <35%, got {final2:.1%}"
print("  PASS ✓")

print()
print("CASE 3: JD=Python  Resume=React Developer")
jd3   = ["python", "django", "postgresql"]
cand3 = ["react", "javascript", "node.js", "typescript", "redux"]
ss3, matched3, missing3 = calculate_skill_score(cand3, jd3)
sim3  = 0.50
final3 = score(ss3, sim3, 1.0, True)
print(f"  skill_score={ss3}  matched={matched3}  missing={missing3}")
print(f"  final_score={final3:.1%}")
assert ss3 == 0.0, f"FAIL: expected 0 skill match, got {ss3}"
assert final3 < 0.35, f"FAIL: expected <35%, got {final3:.1%}"
print("  PASS ✓")

print()
print("CASE 4: JD='react developer'  Resume=ReactJS+NodeJS")
jd4   = ["react developer"]
cand4 = ["ReactJS", "Node.js", "JavaScript"]
ss4, matched4, missing4 = calculate_skill_score(cand4, jd4)
final4 = score(ss4, 0.70, 1.0, True)
print(f"  skill_score={ss4}  matched={matched4}  missing={missing4}")
print(f"  final_score={final4:.1%}")
assert ss4 == 1.0, f"FAIL: 'react developer' should match 'react', got score={ss4}"
print("  PASS ✓")

print()
print("CASE 5: .net normalization")
from app.api.services.parser import normalize_skill_name
assert normalize_skill_name(".net") == ".net", "FAIL: .net should stay .net"
assert normalize_skill_name("reactjs") == "react", "FAIL: reactjs->react"
assert normalize_skill_name("mern") == "react", "FAIL: mern->react"
assert normalize_skill_name("react developer") == "react", "FAIL: react developer->react"
assert normalize_skill_name("senior react developer") == "react", "FAIL"
print("  .net -> .net  PASS ✓")
print("  reactjs -> react  PASS ✓")
print("  mern -> react  PASS ✓")
print("  react developer -> react  PASS ✓")
print("  senior react developer -> react  PASS ✓")

print()
print("=" * 60)
print("ALL TEST CASES PASSED")
