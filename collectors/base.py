from abc import ABC, abstractmethod
from html import unescape
import json
import re
from typing import Any

from models import Vacancy


REMOTE_MARKERS = (
    "full remote",
    "fully remote",
    "100% remote",
    "remote work",
    "remote position",
    "remote role",
    "remote job",
    "remote -",
    "remote —",
    "remote/",
    "remote or",
    "remote або",
    "remote",
    "віддалена робота",
    "віддалено",
    "дистанційно",
    "дистанційна робота",
    "робота дистанційно",
)

NON_REMOTE_MARKERS = (
    "hybrid",
    "гібрид",
    "гібридна робота",
    "on-site",
    "on site",
    "onsite",
    "office-based",
    "office based",
    "office only",
    "on-site only",
    "onsite only",
    "офісна робота",
    "робота в офісі",
    "в офісі",
)

PART_TIME_MARKERS = (
    "part-time",
    "part time",
    "неповна зайнятість",
    "часткова зайнятість",
)

FULL_TIME_MARKERS = (
    "full-time",
    "full time",
    "повна зайнятість",
)


def clean_text(value: Any) -> str:
    """
    Convert arbitrary value to normalized plain text.
    """
    if value is None:
        return ""

    text = unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def first_nonempty(*values: Any) -> str:
    """
    Return the first non-empty normalized value.
    """
    for value in values:
        value = clean_text(value)
        if value:
            return value

    return ""


def infer_employment(text: str) -> str:
    """
    Infer employment type from vacancy text.
    """
    t = clean_text(text).lower()

    if any(marker in t for marker in PART_TIME_MARKERS):
        return "Part-time"

    if any(marker in t for marker in FULL_TIME_MARKERS):
        return "Full-time"

    return ""


def has_explicit_non_remote(text: str) -> bool:
    """
    Detect explicit evidence that a vacancy is not fully remote.

    This is intentionally separate from infer_remote() because a vacancy
    can contain both remote-related and office-related wording.
    """
    t = clean_text(text).lower()

    return any(marker in t for marker in NON_REMOTE_MARKERS)


def infer_remote(
    text: str,
    job_posting: dict[str, Any] | None = None,
) -> bool:
    """
    Infer whether a vacancy is remote.

    Priority:
    1. JSON-LD jobLocationType = TELECOMMUTE / REMOTE
    2. Explicit remote markers in text

    Explicit non-remote markers are checked first.
    """
    t = clean_text(text).lower()

    if has_explicit_non_remote(t):
        return False

    if job_posting:
        location_type = clean_text(
            job_posting.get("jobLocationType")
        ).upper()

        if location_type in {"TELECOMMUTE", "REMOTE"}:
            return True

    return any(marker in t for marker in REMOTE_MARKERS)


def format_number(value: Any) -> str:
    """
    Format numeric salary values safely.

    JSON-LD can contain both numbers and strings, so we do not assume
    that minValue/maxValue are numeric.
    """
    if value is None:
        return ""

    if isinstance(value, bool):
        return str(value)

    if isinstance(value, (int, float)):
        if isinstance(value, float) and value.is_integer():
            return f"{int(value):,}".replace(",", " ")

        return f"{value:g}".replace(",", " ")

    text = clean_text(value)

    # Try to normalize numeric strings such as "5000.0"
    try:
        number = float(text)

        if number.is_integer():
            return f"{int(number):,}".replace(",", " ")

        return f"{number:g}".replace(",", " ")
    except (ValueError, TypeError):
        return text


def format_salary(
    value: Any,
    currency: str = "",
) -> str:
    """
    Convert JSON-LD baseSalary into a readable string.
    """
    if value is None:
        return ""

    if isinstance(value, dict):
        currency = first_nonempty(
            value.get("currency"),
            currency,
        )

        nested = value.get("value", value)

        if isinstance(nested, dict):
            minimum = nested.get("minValue")
            maximum = nested.get("maxValue")
            exact = nested.get("value")

            if minimum is not None and maximum is not None:
                return (
                    f"{format_number(minimum)}–"
                    f"{format_number(maximum)} "
                    f"{currency}"
                ).strip()

            if exact is not None:
                return (
                    f"{format_number(exact)} "
                    f"{currency}"
                ).strip()

        else:
            return (
                f"{format_number(nested)} "
                f"{currency}"
            ).strip()

    if isinstance(value, (int, float)):
        return (
            f"{format_number(value)} "
            f"{currency}"
        ).strip()

    if not isinstance(value, (list, dict)):
        return (
            f"{clean_text(value)} "
            f"{currency}"
        ).strip()

    return ""


def find_job_posting(
    raw: Any,
) -> dict[str, Any] | None:
    """
    Recursively find a JobPosting object inside JSON-LD.
    """
    if isinstance(raw, list):
        for item in raw:
            found = find_job_posting(item)

            if found:
                return found

        return None

    if not isinstance(raw, dict):
        return None

    types = raw.get("@type", [])

    if isinstance(types, str):
        types = [types]

    if any(
        str(item).lower() == "jobposting"
        for item in types
    ):
        return raw

    for value in raw.values():
        found = find_job_posting(value)

        if found:
            return found

    return None


def extract_json_ld(page) -> dict[str, Any] | None:
    """
    Extract JobPosting JSON-LD from a page.
    """
    try:
        scripts = page.locator(
            'script[type="application/ld+json"]'
        ).all_inner_texts()

    except Exception:
        return None

    for script in scripts:
        try:
            data = json.loads(script)

        except Exception:
            continue

        found = find_job_posting(data)

        if found:
            return found

    return None


def extract_location(
    job: dict[str, Any] | None,
) -> str:
    """
    Extract human-readable location from JSON-LD.
    """
    if not job:
        return ""

    location = job.get("jobLocation")

    if isinstance(location, list):
        location = location[0] if location else None

    if isinstance(location, dict):
        address = location.get("address", location)

        if isinstance(address, dict):
            parts = [
                address.get("addressLocality"),
                address.get("addressRegion"),
                address.get("addressCountry"),
            ]

            cleaned = [
                clean_text(value)
                for value in parts
                if clean_text(value)
            ]

            return ", ".join(cleaned)

    return clean_text(location)


def extract_salary_from_text(
    text: str,
) -> str:
    """
    Try to extract a salary range from ordinary page text
    when JSON-LD does not contain salary information.
    """
    if not text:
        return ""

    pattern = (
        r"(?:"
        r"\$|€|£|₴|грн\.?|USD|EUR"
        r")"
        r"\s?"
        r"\d[\d\s,.]*"
        r"(?:"
        r"\s?[–-]\s?"
        r"(?:\$|€|£|₴|грн\.?|USD|EUR)?"
        r"\s?\d[\d\s,.]*"
        r")?"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE,
    )

    if not match:
        return ""

    return clean_text(match.group(0))


def enrich_vacancy(
    page,
    vacancy: Vacancy,
) -> Vacancy:
    """
    Enrich a vacancy using its detail page.

    Important behavior:
    - If the detail page cannot be opened, preserve the original vacancy.
    - If the detail page is empty, preserve the original vacancy.
    - If JSON-LD exists, use it as the primary structured source.
    - Never overwrite useful source-level data with empty strings.
    - Preserve source-level remote=True unless the detail page explicitly
      proves that the vacancy is non-remote.
    """

    try:
        page.goto(
            vacancy.url,
            wait_until="domcontentloaded",
            timeout=15000,
        )

        page.wait_for_timeout(250)

    except Exception:
        return vacancy

    job = extract_json_ld(page)

    try:
        body = clean_text(
            page.locator("body").inner_text(
                timeout=4000
            )
        )

    except Exception:
        body = ""

    # ---------------------------------------------------------
    # CASE 1: detail page returned no useful content
    # ---------------------------------------------------------

    if not job and not body:
        return vacancy

    # ---------------------------------------------------------
    # CASE 2: JSON-LD JobPosting is available
    # ---------------------------------------------------------

    if job:
        title = first_nonempty(
            job.get("title"),
            vacancy.title,
        )

        company_data = job.get(
            "hiringOrganization",
            {},
        )

        if isinstance(company_data, dict):
            company = company_data.get(
                "name",
                "",
            )
        else:
            company = company_data

        description = first_nonempty(
            job.get("description"),
            body,
            vacancy.description,
        )

        employment = job.get(
            "employmentType",
            "",
        )

        if isinstance(employment, list):
            employment = ", ".join(
                clean_text(item)
                for item in employment
                if clean_text(item)
            )

        employment = first_nonempty(
            employment,
            vacancy.employment_type,
            infer_employment(body),
        )

        salary = format_salary(
            job.get("baseSalary")
        )

        if not salary:
            salary = vacancy.salary

        if not salary:
            salary = extract_salary_from_text(body)

        posted = first_nonempty(
            job.get("datePosted"),
            vacancy.posted,
        )

        location = first_nonempty(
            extract_location(job),
            vacancy.location,
        )

    # ---------------------------------------------------------
    # CASE 3: no JSON-LD, but detail page contains text
    # ---------------------------------------------------------

    else:
        title = vacancy.title

        company = vacancy.company

        description = first_nonempty(
            vacancy.description,
            body,
        )

        employment = first_nonempty(
            vacancy.employment_type,
            infer_employment(body),
        )

        salary = vacancy.salary

        if not salary:
            salary = extract_salary_from_text(body)

        posted = vacancy.posted

        location = vacancy.location

    # ---------------------------------------------------------
    # Update vacancy fields without destroying existing data
    # ---------------------------------------------------------

    vacancy.title = clean_text(title)[:300]

    vacancy.company = clean_text(company)[:200]

    vacancy.description = clean_text(
        description
    )[:12000]

    vacancy.employment_type = clean_text(
        employment
    )[:100]

    vacancy.salary = clean_text(
        salary
    )[:150]

    vacancy.location = clean_text(
        location
    )[:200]

    vacancy.posted = clean_text(
        posted
    )[:50]

    # ---------------------------------------------------------
    # Remote detection
    # ---------------------------------------------------------

    detail_text = clean_text(
        f"{body} {description} {location}"
    )

    remote_detected = infer_remote(
        detail_text,
        job,
    )

    explicit_non_remote = has_explicit_non_remote(
        detail_text
    )

    if explicit_non_remote:
        # Detail page explicitly says hybrid/office/on-site.
        vacancy.remote = False

    elif remote_detected:
        # Detail page explicitly confirms remote.
        vacancy.remote = True

    # Otherwise:
    # preserve vacancy.remote as it was set by the
    # source-specific collector.

    return vacancy


class BaseCollector(ABC):
    """
    Base class for all job-source collectors.
    """

    source = ""

    @abstractmethod
    def collect(
        self,
        terms: list[str],
    ) -> list[Vacancy]:
        raise NotImplementedError

    def enrich(
        self,
        page,
        vacancies: list[Vacancy],
        limit: int = 50,
    ) -> list[Vacancy]:
        """
        Deduplicate vacancies by URL and enrich them.
        """

        unique = []
        seen = set()

        for vacancy in vacancies:
            key = vacancy.url.rstrip("/")

            if not key or key in seen:
                continue

            seen.add(key)
            unique.append(vacancy)

            if len(unique) >= limit:
                break

        result = []

        for vacancy in unique:
            try:
                result.append(
                    enrich_vacancy(
                        page,
                        vacancy,
                    )
                )

            except Exception:
                # Never lose a vacancy because enrichment failed.
                result.append(vacancy)

        return result