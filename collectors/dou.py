from urllib.parse import quote_plus
from collectors.base import BaseCollector
from collectors.browser import Browser
from models import Vacancy

class DOUCollector(BaseCollector):
    source="DOU"
    def collect(self, terms):
        out=[]
        with Browser() as b:
            page=b.browser.new_page()
            for term in terms:
                url=f"https://jobs.dou.ua/vacancies/?search={quote_plus(term)}&remote="
                try:
                    page.goto(url,wait_until="domcontentloaded",timeout=30000); page.wait_for_timeout(1000)
                    cards=page.locator("li.l-vacancy, .vacancy-list .l-vacancy").all()
                    for c in cards[:50]:
                        a=c.locator("a.vt, a[href*='/vacancies/']").first
                        title=(a.inner_text() or "").strip(); href=a.get_attribute("href") or ""
                        if title and href: out.append(Vacancy(title=title,url=href,source=self.source,remote=True,category="Core/Adjacent BI & Data"))
                except Exception: continue
        return out
