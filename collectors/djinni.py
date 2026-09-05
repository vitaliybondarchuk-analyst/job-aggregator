from urllib.parse import urlencode
import re

from collectors.base import BaseCollector
from collectors.browser import Browser
from models import Vacancy


class DjinniCollector(BaseCollector):
    source = "Djinni"

    def collect(self, terms):
        candidates = []

        with Browser() as b:
            page = b.browser.new_page()
            detail = b.browser.new_page()

            for term in terms:
                params = [
                    ("all_keywords", term),
                    ("search_type", "basic-search"),
                    ("employment", "remote"),
                    ("region", "UKR"),
                ]

                url = "https://djinni.co/jobs/?" + urlencode(params)

                try:
                    page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=30000,
                    )
                    page.wait_for_timeout(1000)

                    links = page.locator("a[href*='/jobs/']").all()

                    for a in links[:80]:
                        href = a.get_attribute("href") or ""
                        title = (
                            a.inner_text() or ""
                        ).strip().splitlines()[0]

                        # Only real vacancy URLs:
                        # /jobs/846507-senior-power-bi-ms-fabric-developer/
                        if not re.search(r"/jobs/\d+-", href):
                            continue

                        if not title:
                            continue

                        if href.startswith("/"):
                            href = "https://djinni.co" + href

                        candidates.append(
                            Vacancy(
                                title=title,
                                url=href,
                                source=self.source,
                                category="Core/Adjacent BI & Data",
                            )
                        )

                except Exception:
                    continue

            enriched = self.enrich(
                detail,
                candidates,
                limit=100,
            )

            return [
                v
                for v in enriched
                if v.remote
            ]
            