# Personal Job Aggregator — MVP

Purpose:
- Search Djinni, DOU, robota.ua and Work.ua.
- Remote-only.
- Two search tracks: Core/Adjacent BI & Data and Side Income.
- Full-time, part-time, contract/freelance.
- No salary or language filter.
- Exclude: Junior, Intern/Internship, Trainee, office-only, unpaid/volunteer, commission-only sales, physical-presence roles.
- Deduplicate the same vacancy across sources.
- Produce a relevance score without exposing the scoring explanation.

## Run

Python 3.11+ is recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
streamlit run app.py
```

The first run opens each source in a real Chromium browser. This is intentional: several job sites render content dynamically and may reject simple HTTP requests.

## Important

This MVP is designed as a maintainable foundation, not as a guarantee that every site will always permit automated collection. Site HTML, anti-bot measures and terms can change. Each source has its own adapter so one site's change does not require rewriting the whole aggregator.

## Current architecture

- `config.py` — candidate profile, search terms and exclusion rules.
- `models.py` — normalized vacancy model.
- `collectors/` — source-specific collectors.
- `dedupe.py` — exact + fuzzy duplicate detection.
- `scoring.py` — relevance scoring.
- `pipeline.py` — collection -> filtering -> dedupe -> scoring.
- `app.py` — simple Streamlit interface.

## Output

The UI shows:
- category
- match score
- title
- company
- employment type
- remote status
- salary
- short description
- source
- vacancy link

The score explanation is intentionally not displayed, per the agreed specification.
