from urllib.parse import quote_plus
from collectors.base import BaseCollector
from collectors.browser import Browser
from models import Vacancy

class DjinniCollector(BaseCollector):
    source = "Djinni"
    def collect(self, terms):
        out=[]
        with Browser() as b:
            page=b.browser.new_page()
            for term in terms:
                url=f"https://djinni.co/jobs/?search={quote_plus(term)}&location=Ukraine&primary_keyword={quote_plus(term)}"
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(1200)
                    cards=page.locator("a.job-item__title, a.job-list-item__title, a[href*='/jobs/']").all()
                    seen=set()
                    for a in cards[:50]:
                        title=(a.inner_text() or "").strip()
                        href=a.get_attribute("href") or ""
                        if not title or not href or href in seen: continue
                        seen.add(href)
                        if href.startswith("/"): href="https://djinni.co"+href
                        out.append(Vacancy(title=title,url=href,source=self.source,remote=True,category="Core/Adjacent BI & Data"))
                except Exception:
                    continue
        return out
