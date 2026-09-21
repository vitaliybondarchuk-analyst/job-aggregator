from urllib.parse import quote_plus

from collectors.base import (
    BaseCollector,
    clean_text,
    extract_salary_from_text,
    infer_employment,
)
from collectors.browser import Browser
from models import Vacancy


def extract_dou_company(page) -> str:
    try:
        links = page.locator('a[href*="/companies/"]').all()
        for link in links[:30]:
            href = link.get_attribute("href") or ""
            text = clean_text(link.inner_text() or "")
            if (
                "/companies/" in href
                and "/vacancies/" not in href
                and text
                and text.lower() not in {"компанії", "companies"}
            ):
                return text[:200]
    except Exception:
        pass
    return ""


def extract_dou_description(page) -> str:
    selectors = (
        ".vacancy-section",
        ".b-typo.vacancy-section",
        '[class*="vacancy-section"]',
        '[class*="vacancy-section__"]',
    )

    candidates = []

    for selector in selectors:
        try:
            locator = page.locator(selector)
            count = locator.count()

            for index in range(min(count, 10)):
                try:
                    text = clean_text(
                        locator.nth(index).inner_text(timeout=2000)
                    )
                    if len(text) >= 150:
                        candidates.append(text)
                except Exception:
                    continue
        except Exception:
            continue

    if candidates:
        return max(candidates, key=len)[:12000]

    return ""


def enrich_dou_vacancy(page, vacancy: Vacancy) -> Vacancy:
    try:
        page.goto(
            vacancy.url,
            wait_until="domcontentloaded",
            timeout=20000,
        )
        page.wait_for_timeout(700)
    except Exception:
        return vacancy

    company = extract_dou_company(page)
    description = extract_dou_description(page)

    try:
        body = clean_text(
            page.locator("body").inner_text(timeout=4000)
        )
    except Exception:
        body = ""

    # DOU detail pages expose the company and vacancy body
    # in ordinary HTML rather than reliably usable JobPosting JSON-LD.
    if company:
        vacancy.company = company

    if description:
        vacancy.description = description

    if not vacancy.employment_type:
        vacancy.employment_type = infer_employment(
            f"{description} {body}"
        )

    if not vacancy.salary:
        vacancy.salary = extract_salary_from_text(
            f"{description} {body}"
        )

    remote_text = f"{vacancy.title} {description} {body}".lower()

    if "віддалено" in remote_text or "remote" in remote_text:
        vacancy.remote = True

    return vacancy


class DOUCollector(BaseCollector):
    source = "DOU"

    def collect(self, terms):
        candidates = []

        with Browser() as b:
            page = b.browser.new_page()
            detail = b.browser.new_page()

            for term in terms:
                url = (
                    "https://jobs.dou.ua/vacancies/"
                    f"?search={quote_plus(term)}&remote="
                )

                try:
                    page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=30000,
                    )
                    page.wait_for_timeout(1000)

                    cards = page.locator(
                        "li.l-vacancy, .vacancy-list .l-vacancy"
                    ).all()

                    for card in cards[:50]:
                        anchor = card.locator(
                            "a.vt, a[href*='/vacancies/']"
                        ).first

                        title = (
                            anchor.inner_text() or ""
                        ).strip()

                        href = (
                            anchor.get_attribute("href") or ""
                        )

                        if not title or not href:
                            continue

                        candidates.append(
                            Vacancy(
                                title=title,
                                url=href,
                                source=self.source,
                                remote=True,
                                category="Power BI",
                            )
                        )

                except Exception:
                    continue

            enriched = []

            seen = set()

            for vacancy in candidates:
                key = vacancy.url.rstrip("/")
                if not key or key in seen:
                    continue

                seen.add(key)

                enriched.append(
                    enrich_dou_vacancy(
                        detail,
                        vacancy,
                    )
                )

                if len(enriched) >= 100:
                    break

            return [
                vacancy
                for vacancy in enriched
                if vacancy.remote
            ]
