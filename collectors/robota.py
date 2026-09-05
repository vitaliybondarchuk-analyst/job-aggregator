from urllib.parse import quote_plus

from collectors.base import (
    BaseCollector,
    clean_text,
    infer_employment,
)
from collectors.browser import Browser
from models import Vacancy


REMOTE_HINTS = (
    "віддалена робота",
    "віддалено",
    "дистанційно",
    "дистанційна робота",
    "remote",
    "remotely",
    "full remote",
    "fully remote",
    "remote work",
)

NON_REMOTE_HINTS = (
    "hybrid",
    "гібрид",
    "гібридна робота",
    "гібридний формат",
    "гібридний",
    "on-site",
    "on site",
    "onsite",
    "office-based",
    "office based",
    "office only",
    "офіс",
    "офісна робота",
    "робота в офісі",
    "в офісі",
    "на місці",
    "робота на місці",
)

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


def extract_card_text(anchor) -> str:
    """
    Extract the visible vacancy-card text.

    This is used only for:
    - detecting remote status;
    - initial employment detection;
    - finding the vacancy URL.

    It is NOT used as the vacancy description.
    """

    try:

        return normalize_whitespace(
            anchor.evaluate(
                """
                (el) => {
                    let node = el;

                    for (let i = 0; i < 10 && node; i++) {

                        const text = (
                            node.innerText || ''
                        ).trim();

                        if (text.length >= 80) {
                            return text;
                        }

                        node = node.parentElement;
                    }

                    return (
                        el.innerText || ''
                    ).trim();
                }
                """
            )
        )

    except Exception:

        try:
            return normalize_whitespace(
                anchor.inner_text()
            )

        except Exception:
            return ""


def is_explicit_non_remote(
    text: str,
) -> bool:
    """
    Return True when the vacancy explicitly indicates
    office/on-site/hybrid work.

    Non-remote markers have priority over remote markers.
    """

    text = normalize_whitespace(
        text
    ).lower()

    if not text:
        return False

    return any(
        marker in text
        for marker in NON_REMOTE_HINTS
    )


def explicit_remote(
    text: str,
) -> bool:
    """
    Accept a vacancy only when remote work is explicitly
    indicated.

    Any explicit office/hybrid/on-site marker rejects it.
    """

    text = normalize_whitespace(
        text
    ).lower()

    if not text:
        return False

    if is_explicit_non_remote(
        text[:1500]
    ):
        return False

    return any(
        marker in text[:1500]
        for marker in REMOTE_HINTS
    )


def clean_title(
    title: str,
) -> str:
    """
    Clean a title extracted from Robota.ua.
    """

    title = normalize_whitespace(
        title
    )

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

            if title.lower().startswith(
                prefix.lower()
            ):

                title = title[
                    len(prefix):
                ].strip()

                changed = True

    if title.lower() in REMOTE_LABELS:
        return ""

    # Remove obvious card metadata accidentally appended
    # to the title.
    lower = title.lower()

    cut_markers = (
        " компанія з відзнаками",
        " company with awards",
        " відгукнутись",
        " відгукнутися",
        " respond ",
        " reply ",
    )

    positions = []

    for marker in cut_markers:

        position = lower.find(
            marker
        )

        if position > 0:
            positions.append(
                position
            )

    if positions:

        title = title[
            :min(positions)
        ].strip()

    return normalize_whitespace(
        title
    )[:300]


def extract_title_from_detail(
    page,
) -> str:
    """
    Extract the actual vacancy title from the detail page.

    h1 is the primary source.
    """

    try:

        locator = page.locator(
            "h1"
        )

        count = locator.count()

        for index in range(
            min(count, 5)
        ):

            try:

                value = normalize_whitespace(
                    locator.nth(
                        index
                    ).inner_text(
                        timeout=3000
                    )
                )

                value = clean_title(
                    value
                )

                if value:
                    return value

            except Exception:
                continue

    except Exception:
        pass

    # Fallback to headings.
    try:

        locator = page.locator(
            "h2, h3, h4"
        )

        count = locator.count()

        for index in range(
            min(count, 10)
        ):

            try:

                value = normalize_whitespace(
                    locator.nth(
                        index
                    ).inner_text(
                        timeout=2000
                    )
                )

                value = clean_title(
                    value
                )

                if value:
                    return value

            except Exception:
                continue

    except Exception:
        pass

    return ""


def extract_description_from_detail(
    page,
) -> str:
    """
    Extract the actual vacancy description.

    Robota.ua's <body> and <main> contain navigation,
    application UI and footer, so we deliberately avoid
    returning the entire body.

    We look for text blocks containing actual vacancy
    content and select the most meaningful one.
    """

    selectors = (
        '[class*="vacancy-description"]',
        '[class*="VacancyDescription"]',
        '[class*="description"]',
        '[class*="Description"]',
        '[data-testid*="description"]',
        '[data-qa*="description"]',
    )

    candidates = []

    for selector in selectors:

        try:

            locator = page.locator(
                selector
            )

            count = locator.count()

            for index in range(
                min(count, 20)
            ):

                try:

                    text = normalize_whitespace(
                        locator.nth(
                            index
                        ).inner_text(
                            timeout=2000
                        )
                    )

                    if len(text) >= 150:
                        candidates.append(
                            text
                        )

                except Exception:
                    continue

        except Exception:
            continue

    # --------------------------------------------------------
    # If a specific description container exists, use it.
    # --------------------------------------------------------

    if candidates:

        # Prefer the longest meaningful description.
        candidates.sort(
            key=len,
            reverse=True,
        )

        return candidates[0][:12000]

    # --------------------------------------------------------
    # Fallback: inspect paragraphs/list items.
    # --------------------------------------------------------

    try:

        locator = page.locator(
            "p, li"
        )

        count = locator.count()

        paragraphs = []

        for index in range(
            min(count, 300)
        ):

            try:

                text = normalize_whitespace(
                    locator.nth(
                        index
                    ).inner_text(
                        timeout=1000
                    )
                )

                if len(text) >= 40:
                    paragraphs.append(
                        text
                    )

            except Exception:
                continue

        if paragraphs:

            description = "\n".join(
                paragraphs
            )

            if len(description) >= 150:

                return description[
                    :12000
                ]

    except Exception:
        pass

    return ""


def extract_company_from_detail(
    page,
) -> str:
    """
    Extract company name from structured page data
    when available.

    JSON-LD is handled by BaseCollector, so this method
    is only a lightweight fallback.
    """

    selectors = (
        '[class*="company"]',
        '[class*="Company"]',
        '[data-testid*="company"]',
        '[data-qa*="company"]',
    )

    for selector in selectors:

        try:

            locator = page.locator(
                selector
            )

            count = locator.count()

            for index in range(
                min(count, 10)
            ):

                try:

                    text = normalize_whitespace(
                        locator.nth(
                            index
                        ).inner_text(
                            timeout=1000
                        )
                    )

                    if not text:
                        continue

                    if len(text) <= 150:
                        return text

                except Exception:
                    continue

        except Exception:
            continue

    return ""


def extract_location_from_detail(
    page,
) -> str:
    """
    Lightweight location extraction.

    JSON-LD remains the preferred source.
    """

    selectors = (
        '[class*="location"]',
        '[class*="Location"]',
        '[data-testid*="location"]',
        '[data-qa*="location"]',
    )

    for selector in selectors:

        try:

            locator = page.locator(
                selector
            )

            count = locator.count()

            for index in range(
                min(count, 10)
            ):

                try:

                    text = normalize_whitespace(
                        locator.nth(
                            index
                        ).inner_text(
                            timeout=1000
                        )
                    )

                    if text and len(text) <= 150:
                        return text

                except Exception:
                    continue

        except Exception:
            continue

    return ""


def enrich_robota_vacancy(
    page,
    vacancy: Vacancy,
) -> Vacancy:
    """
    Enrich vacancy from its detail page.
    """

    try:

        page.goto(
            vacancy.url,
            wait_until="domcontentloaded",
            timeout=20000,
        )

        page.wait_for_timeout(
            1000
        )

    except Exception:
        return vacancy

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    title = extract_title_from_detail(
        page
    )

    if title:
        vacancy.title = title

    # --------------------------------------------------------
    # Description
    # --------------------------------------------------------

    description = (
        extract_description_from_detail(
            page
        )
    )

    if description:
        vacancy.description = description

    # --------------------------------------------------------
    # Company
    # --------------------------------------------------------

    if not vacancy.company:

        company = (
            extract_company_from_detail(
                page
            )
        )

        if company:
            vacancy.company = company

    # --------------------------------------------------------
    # Location
    # --------------------------------------------------------

    if not vacancy.location:

        location = (
            extract_location_from_detail(
                page
            )
        )

        if location:
            vacancy.location = location

    # --------------------------------------------------------
    # Employment
    # --------------------------------------------------------

    detail_text = normalize_whitespace(
        description
    )

    if not vacancy.employment_type:

        vacancy.employment_type = (
            infer_employment(
                detail_text
            )
        )

    # --------------------------------------------------------
    # Remote status
    # --------------------------------------------------------

    # IMPORTANT:
    #
    # We check the whole relevant detail text for office/
    # hybrid markers before accepting remote.
    #
    if is_explicit_non_remote(
        detail_text
    ):
        vacancy.remote = False

    elif any(
        marker in detail_text.lower()
        for marker in REMOTE_HINTS
    ):
        vacancy.remote = True

    return vacancy


class RobotaCollector(
    BaseCollector
):

    source = "robota.ua"

    def collect(
        self,
        terms: list[str],
    ) -> list[Vacancy]:

        candidates = []

        with Browser() as browser:

            page = browser.browser.new_page()

            detail = browser.browser.new_page()

            for term in terms:

                query = quote_plus(
                    f"remote {term}"
                )

                url = (
                    "https://robota.ua/zapros/"
                    f"{query}/ukraine"
                )

                try:

                    page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=30000,
                    )

                    page.wait_for_timeout(
                        1000
                    )

                    links = page.locator(
                        "a[href*='/vacancy']"
                    ).all()

                    for anchor in links[:100]:

                        try:

                            href = (
                                anchor.get_attribute(
                                    "href"
                                )
                                or ""
                            )

                            if (
                                not href
                                or "/vacancy"
                                not in href.lower()
                            ):
                                continue

                            if href.startswith(
                                "/"
                            ):

                                href = (
                                    "https://robota.ua"
                                    + href
                                )

                            card_text = (
                                extract_card_text(
                                    anchor
                                )
                            )

                            if not card_text:
                                continue

                            # ------------------------------------------------
                            # Remote-only source filter.
                            # ------------------------------------------------

                            if not explicit_remote(
                                card_text
                            ):
                                continue

                            # ------------------------------------------------
                            # Initial title.
                            #
                            # We will replace this with the detail-page
                            # h1 during enrichment.
                            # ------------------------------------------------

                            title = ""

                            try:

                                anchor_title = (
                                    anchor.get_attribute(
                                        "title"
                                    )
                                    or ""
                                )

                                title = clean_title(
                                    anchor_title
                                )

                            except Exception:
                                pass

                            if not title:

                                try:

                                    aria = (
                                        anchor.get_attribute(
                                            "aria-label"
                                        )
                                        or ""
                                    )

                                    title = clean_title(
                                        aria
                                    )

                                except Exception:
                                    pass

                            # Do NOT use the whole card text as title.
                            #
                            # If we cannot get an initial title,
                            # we still keep the candidate because
                            # the detail page may provide h1.
                            #
                            employment = (
                                infer_employment(
                                    card_text
                                )
                            )

                            candidates.append(
                                Vacancy(
                                    title=title,
                                    company="",
                                    url=href,
                                    source=self.source,
                                    description="",
                                    employment_type=employment,
                                    remote=True,
                                    salary="",
                                    location="",
                                    posted="",
                                    category=(
                                        "Core/Adjacent BI & Data"
                                    ),
                                )
                            )

                        except Exception:
                            continue

                except Exception:
                    continue

            # ----------------------------------------------------
            # Deduplicate URLs before detail requests.
            # ----------------------------------------------------

            unique = []

            seen = set()

            for vacancy in candidates:

                key = vacancy.url.rstrip(
                    "/"
                )

                if not key:
                    continue

                if key in seen:
                    continue

                seen.add(key)

                unique.append(
                    vacancy
                )

                if len(unique) >= 100:
                    break

            # ----------------------------------------------------
            # Detail enrichment.
            # ----------------------------------------------------

            enriched = []

            for vacancy in unique:

                try:

                    enriched.append(
                        enrich_robota_vacancy(
                            detail,
                            vacancy,
                        )
                    )

                except Exception:

                    enriched.append(
                        vacancy
                    )

            # ----------------------------------------------------
            # Final validation.
            # ----------------------------------------------------

            result = []

            for vacancy in enriched:

                # Must have a real title.
                if not vacancy.title:
                    continue

                # Generic labels are invalid.
                if vacancy.title.lower() in REMOTE_LABELS:
                    continue

                # Explicit office/hybrid vacancies are invalid.
                combined = normalize_whitespace(
                    f"{vacancy.title} "
                    f"{vacancy.description} "
                    f"{vacancy.location}"
                ).lower()

                if is_explicit_non_remote(
                    combined
                ):
                    continue

                # Must remain remote.
                if not vacancy.remote:
                    continue

                result.append(
                    vacancy
                )

            return result