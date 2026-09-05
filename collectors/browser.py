from playwright.sync_api import sync_playwright

class Browser:
    def __init__(self, headless=True):
        self.headless = headless
        self.pw = None
        self.browser = None

    def __enter__(self):
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=self.headless)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.browser:
            self.browser.close()
        if self.pw:
            self.pw.stop()
