from urllib.parse import quote_plus
from collectors.base import BaseCollector
from collectors.browser import Browser
from models import Vacancy

class RobotaCollector(BaseCollector):
    source="robota.ua"
    def collect(self, terms):
        out=[]
        with Browser() as b:
            page=b.browser.new_page()
            for term in terms:
                url=f"https://robota.ua/zapros/{quote_plus(term)}/ukraine"
                try:
                    page.goto(url,wait_until="domcontentloaded",timeout=30000); page.wait_for_timeout(1500)
                    links=page.locator("a[href*='/company'], a[href*='/vacancy']").all()
                    seen=set()
                    for a in links[:100]:
                        title=(a.inner_text() or "").strip(); href=a.get_attribute("href") or ""
                        if not title or len(title)<4 or href in seen: continue
                        if href.startswith("/"): href="https://robota.ua"+href
                        if "/vacancy" not in href.lower(): continue
                        seen.add(href); out.append(Vacancy(title=title,url=href,source=self.source,remote=True,category="Core/Adjacent BI & Data"))
                except Exception: continue
        return out
