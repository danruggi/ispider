import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ispider_core.seo.base import SeoIssue


class TitleMetaQualityCheck:
    name = "title_meta_quality"

    def __init__(self, title_min=30, title_max=60, description_min=70, description_max=160):
        self.title_min = title_min
        self.title_max = title_max
        self.description_min = description_min
        self.description_max = description_max

    def run(self, resp: dict):
        if resp.get("status_code") != 200:
            return []
        content = resp.get("content")
        if not content:
            return []

        soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "lxml")
        title = (soup.title.get_text(" ", strip=True) if soup.title else "").strip()
        desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        description = (desc_tag.get("content", "") if desc_tag else "").strip()
        h1 = soup.find("h1")
        h1_text = h1.get_text(" ", strip=True) if h1 else ""

        issues = []

        if not title:
            issues.append(SeoIssue("TITLE_MISSING", "high", "Missing <title>", self.name, resp.get("url", "")))
        else:
            if len(title) < self.title_min or len(title) > self.title_max:
                issues.append(
                    SeoIssue(
                        "TITLE_LENGTH",
                        "medium",
                        f"Title length is {len(title)} chars (recommended {self.title_min}-{self.title_max})",
                        self.name,
                        resp.get("url", ""),
                        details={"length": len(title)},
                    )
                )
            if h1_text and title == h1_text:
                issues.append(
                    SeoIssue(
                        "TITLE_EQUALS_H1",
                        "low",
                        "Title is identical to H1 (no SERP differentiation)",
                        self.name,
                        resp.get("url", ""),
                    )
                )

        if not description:
            issues.append(
                SeoIssue("META_DESCRIPTION_MISSING", "medium", "Missing meta description", self.name, resp.get("url", ""))
            )
        elif len(description) < self.description_min or len(description) > self.description_max:
            issues.append(
                SeoIssue(
                    "META_DESCRIPTION_LENGTH",
                    "low",
                    f"Meta description length is {len(description)} chars (recommended {self.description_min}-{self.description_max})",
                    self.name,
                    resp.get("url", ""),
                    details={"length": len(description)},
                )
            )

        return issues


class HeadingStructureCheck:
    name = "heading_structure"

    def run(self, resp: dict):
        if resp.get("status_code") != 200:
            return []

        content = resp.get("content")
        if not content:
            return []

        soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "lxml")
        headings = soup.find_all(re.compile(r"^h[1-6]$", re.I))

        h1_count = sum(1 for h in headings if h.name.lower() == "h1")
        h2_count = sum(1 for h in headings if h.name.lower() == "h2")

        issues = []
        if h1_count == 0:
            issues.append(SeoIssue("H1_MISSING", "high", "No H1 tag found", self.name, resp.get("url", "")))
        elif h1_count > 1:
            issues.append(
                SeoIssue(
                    "H1_MULTIPLE",
                    "high",
                    f"Found {h1_count} H1 tags",
                    self.name,
                    resp.get("url", ""),
                    details={"h1_count": h1_count, "h2_count": h2_count},
                )
            )

        levels = [int(h.name[1]) for h in headings]
        for prev, curr in zip(levels, levels[1:]):
            if curr - prev > 1:
                issues.append(
                    SeoIssue(
                        "HEADING_ORDER_SKIP",
                        "low",
                        f"Heading level jumps from h{prev} to h{curr}",
                        self.name,
                        resp.get("url", ""),
                    )
                )
                break

        return issues


class UrlHygieneCheck:
    name = "url_hygiene"

    def __init__(self, max_length=120, news_path_regex=r"^/\d{4}/\d{2}/\d{2}/[a-z0-9-]+/?$"):
        self.max_length = max_length
        self.news_path_regex = re.compile(news_path_regex)

    def run(self, resp: dict):
        url = resp.get("url", "")
        if not url:
            return []

        parsed = urlparse(url)
        path = parsed.path or "/"
        issues = []

        if len(url) > self.max_length:
            issues.append(SeoIssue("URL_TOO_LONG", "low", f"URL length is {len(url)}", self.name, url))

        if any(ch.isupper() for ch in path):
            issues.append(SeoIssue("URL_UPPERCASE", "low", "URL path contains uppercase letters", self.name, url))

        if parsed.query:
            issues.append(SeoIssue("URL_HAS_PARAMETERS", "low", "URL contains query parameters", self.name, url))

        if re.search(r"[^a-zA-Z0-9\-/_]", path):
            issues.append(SeoIssue("URL_SPECIAL_CHARS", "low", "URL path contains special characters", self.name, url))

        if not self.news_path_regex.match(path):
            issues.append(
                SeoIssue(
                    "URL_NEWS_PATTERN_MISMATCH",
                    "medium",
                    "URL does not match expected /yyyy/mm/dd/slug/ pattern",
                    self.name,
                    url,
                )
            )

        return issues


class ContentLengthCheck:
    name = "content_length"

    def __init__(self, min_words=250):
        self.min_words = min_words

    def run(self, resp: dict):
        if resp.get("status_code") != 200:
            return []

        content = resp.get("content")
        if not content:
            return []

        soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "lxml")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(" ", strip=True)
        words = [w for w in re.split(r"\s+", text) if w]
        word_count = len(words)

        if word_count < self.min_words:
            return [
                SeoIssue(
                    "CONTENT_TOO_THIN",
                    "medium",
                    f"Content has {word_count} words (minimum {self.min_words})",
                    self.name,
                    resp.get("url", ""),
                    details={"word_count": word_count, "min_words": self.min_words},
                )
            ]
        return []
