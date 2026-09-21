from urllib.parse import quote

from collectors.base import (
    BaseCollector,
    clean_text,
    infer_employment,
)
from collectors.browser import Browser
from models import Vacancy


API_SEARCH_HOSTS = ("api.robota.ua", "ua-api.robota.ua", "api.rabota.ua")
API_DETAIL_PATH = "/vacancy"
API_PAGE_SIZE = 50
API_MAX_PAGES = 5
REMOTE_SCHEDULE_ID = 3

REMOTE_LABELS = {
    "віддалена робота",
    "remote",
    "remote work",
    "remotely",
    "дистанційна робота",
    "дистанційно",
    "віддалено",
}


def normalize_whitespace(text: str) -> str:
    return clean_text(text)


def is_power_bi_title(title: str) -> bool:
    value = normalize_whitespace(title).lower()
    return "power bi" in value or "powerbi" in value


def clean_title(title: str) -> str:
    title = normalize_whitespace(title)
    if not title:
        return ""

    prefixes = (
        "Віддалена робота ",
        "Remote work ",
        "Remote ",
        "Віддалено ",
        "Дистанційна робота ",
    )

    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if title.lower().startswith(prefix.lower()):
                title = title[len(prefix):].strip()
                changed = True

    if title.lower() in REMOTE_LABELS:
        return ""

    return title[:300]


def fetch_api_json(page, url: str):
    try:
        response = page.request.get(
            url,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
                "Origin": "https://robota.ua",
                "Referer": "https://robota.ua/",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            },
            timeout=30000,
        )
    except Exception:
        return None

    if not response.ok:
        return None

    try:
        return response.json()
    except Exception:
        return None


def build_vacancy_from_api(page, document: dict) -> Vacancy | None:
    vacancy_id = document.get("id")
    if not vacancy_id:
        return None

    detail = None
    for host in API_SEARCH_HOSTS:
        detail = fetch_api_json(
            page,
            f"https://{host}{API_DETAIL_PATH}?id={vacancy_id}",
        )
        if isinstance(detail, dict):
            break

    if not isinstance(detail, dict):
        return None

    if str(detail.get("id")) != str(vacancy_id):
        return None

    if detail.get("isActive") is False:
        return None

    title = clean_title(
        detail.get("name")
        or document.get("name")
        or ""
    )

    if not title or not is_power_bi_title(title):
        return None

    description = clean_text(
        detail.get("description") or ""
    )

    company = clean_text(
        detail.get("companyName") or ""
    )

    salary = ""
    salary_from = detail.get("salaryFrom")
    salary_to = detail.get("salaryTo")
    salary_exact = detail.get("salary")

    if salary_from and salary_to:
        salary = f"{salary_from}–{salary_to} ₴"
    elif salary_from:
        salary = f"{salary_from} ₴"
    elif salary_to:
        salary = f"{salary_to} ₴"
    elif salary_exact:
        salary = f"{salary_exact} ₴"

    schedule_id = detail.get("scheduleId")

    # scheduleId=3 is Robota's remote-work filter.
    # The search request itself is also restricted to scheduleId=3.
    remote = (
        str(schedule_id) == str(REMOTE_SCHEDULE_ID)
        or schedule_id is None
    )

    employment = ""
    try:
        schedule = int(schedule_id)
        if schedule == 1:
            employment = "Full-time"
        elif schedule == 2:
            employment = "Part-time"
    except (TypeError, ValueError):
        employment = infer_employment(description)

    company_id = (
        document.get("notebookId")
        or detail.get("notebookId")
        or ""
    )

    if company_id:
        url = (
            f"https://robota.ua/company{company_id}"
            f"/vacancy{vacancy_id}"
        )
    else:
        url = f"https://robota.ua/vacancy{vacancy_id}"

    return Vacancy(
        title=title,
        company=company,
        url=url,
        source="robota.ua",
        description=description[:12000],
        employment_type=employment,
        remote=remote,
        salary=salary,
        location=clean_text(detail.get("cityName") or ""),
        posted=clean_text(detail.get("date") or ""),
        category="Power BI",
    )


def collect_from_api(page, term: str) -> list[Vacancy]:
    result = []
    seen = set()

    for page_number in range(1, API_MAX_PAGES + 1):
        query = quote(term)

        payload = None

        for host in API_SEARCH_HOSTS:
            url = (
                f"https://{host}/vacancy/search"
                f"?keyWords={query}"
                f"&scheduleId={REMOTE_SCHEDULE_ID}"
                f"&count={API_PAGE_SIZE}"
                f"&page={page_number}"
            )
            payload = fetch_api_json(page, url)
            if isinstance(payload, dict):
                break

        if not isinstance(payload, dict):
            break

        documents = payload.get("documents") or []
        if not documents:
            break

        for document in documents:
            raw_title = normalize_whitespace(
                document.get("name") or ""
            ).lower()

            # Search API is broader than our final requirement.
            # Keep only vacancies whose TITLE contains Power BI.
            if "power bi" not in raw_title and "powerbi" not in raw_title:
                continue

            vacancy_id = document.get("id")
            if not vacancy_id:
                continue

            key = str(vacancy_id)
            if key in seen:
                continue

            seen.add(key)

            vacancy = build_vacancy_from_api(
                page,
                document,
            )

            if vacancy is not None and vacancy.remote:
                result.append(vacancy)

    return result


def extract_card_text(anchor) -> str:
    try:
        return normalize_whitespace(
            anchor.inner_text(timeout=2000)
        )
    except Exception:
        return ""


def enrich_html_vacancy(page, vacancy: Vacancy) -> Vacancy:
    try:
        page.goto(
            vacancy.url,
            wait_until="domcontentloaded",
            timeout=20000,
        )
        page.wait_for_timeout(1000)
    except Exception:
        return vacancy

    try:
        h1 = page.locator("h1").first.inner_text(
            timeout=3000
        )
        h1 = clean_title(h1)
        if h1:
            vacancy.title = h1
    except Exception:
        pass

    try:
        body = clean_text(
            page.locator("body").inner_text(timeout=4000)
        )
    except Exception:
        body = ""

    if body:
        vacancy.description = body[:12000]

    return vacancy


def collect_html_fallback(page, detail, term: str) -> list[Vacancy]:
    query = "-".join(
        term.strip().lower().split()
    )

    url = (
        "https://robota.ua/ua/zapros/"
        f"{query}/ukraine"
    )

    try:
        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )
        page.wait_for_timeout(2000)
    except Exception:
        return []

    candidates = []

    try:
        links = page.locator(
            "a[href*='/vacancy']"
        ).all()
    except Exception:
        return []

    for anchor in links[:100]:
        try:
            href = (
                anchor.get_attribute("href") or ""
            )

            if not href or "/vacancy" not in href.lower():
                continue

            if href.startswith("/"):
                href = "https://robota.ua" + href

            card_text = extract_card_text(anchor)
            lines = [
                normalize_whitespace(line)
                for line in card_text.splitlines()
                if normalize_whitespace(line)
            ]

            title = ""
            for line in lines:
                if is_power_bi_title(line):
                    title = clean_title(line)
                    break

            if not title:
                title = clean_title(
                    anchor.get_attribute("title") or ""
                )

            if not title:
                continue

            candidates.append(
                Vacancy(
                    title=title,
                    url=href,
                    source="robota.ua",
                    remote=True,
                    category="Power BI",
                )
            )

        except Exception:
            continue

    result = []
    seen = set()

    for vacancy in candidates:
        key = vacancy.url.rstrip("/")
        if not key or key in seen:
            continue

        seen.add(key)

        vacancy = enrich_html_vacancy(
            detail,
            vacancy,
        )

        if not is_power_bi_title(vacancy.title):
            continue

        if vacancy.remote:
            result.append(vacancy)

    return result


class RobotaCollector(BaseCollector):
    source = "robota.ua"

    def collect(self, terms: list[str]) -> list[Vacancy]:
        with Browser() as browser:
            api_page = browser.browser.new_page()

            for term in terms:
                api_result = collect_from_api(
                    api_page,
                    term,
                )

                if api_result:
                    return api_result

            # Fallback for temporary API failures.
            page = browser.browser.new_page()
            detail = browser.browser.new_page()

            result = []

            for term in terms:
                result.extend(
                    collect_html_fallback(
                        page,
                        detail,
                        term,
                    )
                )

            return result
