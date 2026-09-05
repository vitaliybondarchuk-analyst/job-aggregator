from config import CORE_TERMS, SIDE_INCOME_TERMS

def score(v):
    text=f"{v.title} {v.description}".lower()
    core=sum(1 for x in CORE_TERMS if x in text)
    side=sum(1 for x in SIDE_INCOME_TERMS if x in text)
    v.score=min(100, 35 + core*9 + side*8 + (12 if v.remote else 0))
    if side and not core: v.category="Side Income"
    elif not v.category: v.category="Core/Adjacent BI & Data"
    return v
