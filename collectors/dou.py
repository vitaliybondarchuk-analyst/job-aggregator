from urllib.parse import quote_plus

from collectors.base import BaseCollector
from collectors.browser import Browser
from models import Vacancy


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

            # DOU search results provide the title and URL, but
            # important metadata such as company, salary, employment
            # and the full description lives on the detail page.
            enriched = self.enrich(
                detail,
                candidates,
                limit=100,
            )

            return [
                vacancy
                for vacancy in enriched
                if vacancy.remote
            ]
