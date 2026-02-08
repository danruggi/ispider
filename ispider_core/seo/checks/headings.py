from bs4 import BeautifulSoup

from ispider_core.seo.base import SeoIssue


class H1TooLongCheck:
    name = "h1_too_long"

    def __init__(self, max_chars: int = 70):
        self.max_chars = max_chars

    def run(self, resp: dict):
        if resp.get("status_code") != 200:
            return []

        content = resp.get("content")
        if not content:
            return []

        try:
            html = content.decode("utf-8", errors="ignore")
        except Exception:
            return []

        soup = BeautifulSoup(html, "lxml")
        issues = []
        for h1 in soup.find_all("h1"):
            text = h1.get_text(" ", strip=True)
            if len(text) > self.max_chars:
                issues.append(
                    SeoIssue(
                        code="H1_TOO_LONG",
                        severity="low",
                        message=f"H1 has {len(text)} chars (max {self.max_chars})",
                        check=self.name,
                        url=resp.get("url", ""),
                        details={"length": len(text), "max_chars": self.max_chars},
                    )
                )
        return issues
