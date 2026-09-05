from config import EXCLUDE_TERMS
from collectors import DjinniCollector, DOUCollector, RobotaCollector, WorkUACollector
from dedupe import dedupe
from scoring import score

def excluded(v):
    text=f"{v.title} {v.description} {v.employment_type} {v.location}".lower()
    return any(term in text for term in EXCLUDE_TERMS)

def run(terms):
    collectors=[DjinniCollector(),DOUCollector(),RobotaCollector(),WorkUACollector()]
    all_v=[]
    errors=[]
    for c in collectors:
        try: all_v.extend(c.collect(terms))
        except Exception as e: errors.append(f"{c.source}: {e}")
    filtered=[v for v in all_v if v.remote and not excluded(v)]
    unique=dedupe(filtered)
    return sorted((score(v) for v in unique), key=lambda x:x.score, reverse=True), errors
