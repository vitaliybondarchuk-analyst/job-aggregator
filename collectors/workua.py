from urllib.parse import quote_plus
from collectors.base import BaseCollector
from collectors.browser import Browser
from models import Vacancy

class WorkUACollector(BaseCollector):
    source="Work.ua"
    def collect(self, terms):
        out=[]
        with Browser() as b:
            page=b.browser.new_page()
            for term in terms:
                url=f"https://www.work.ua/jobs-{quote_plus(term)}/?search=1&remote=1"
                try:
                    page.goto(url,wait_until="domcontentloaded",timeout=30000); page.wait_for_timeout(1200)
                    cards=page.locator("div.job-link, .card-hover, .job-list__item").all()
                    for c in cards[:50]:
                        a=c.locator("a[href*='/jobs/']").first
                        title=(a.inner_text() or "").strip(); href=a.get_attribute("href") or ""
                        if title and href:
                            if href.startswith("/"): href="https://www.work.ua"+href
                            out.append(Vacancy(title=title,url=href,source=self.source,remote=True,category="Core/Adjacent BI & Data"))
                except Exception: continue
        return out
