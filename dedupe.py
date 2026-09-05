import re
from rapidfuzz.fuzz import ratio

def norm(s):
    return re.sub(r"[^a-z0-9а-яіїєґ]+", " ", (s or "").lower()).strip()

def dedupe(vacancies, threshold=88):
    result=[]
    for v in vacancies:
        key=norm(v.title)+" "+norm(v.company)
        duplicate=False
        for existing in result:
            if v.url and existing.url and v.url.rstrip("/") == existing.url.rstrip("/"):
                duplicate=True; break
            other=norm(existing.title)+" "+norm(existing.company)
            if ratio(key,other)>=threshold:
                duplicate=True; break
        if not duplicate: result.append(v)
    return result
