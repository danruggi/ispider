import json
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from bs4 import BeautifulSoup

from ispider_core.seo.base import SeoIssue

import html
from typing import Any, Optional

class ResponseCrawlabilityCheck:
    name = "response_crawlability"

    def __init__(self, timeout_threshold_s=10):
        self.timeout_threshold_s = timeout_threshold_s

    def run(self, resp: dict):
        issues = []
        status = resp.get("status_code")
        url = resp.get("url", "")

        if status is None:
            return []
        if status >= 500:
            issues.append(SeoIssue("HTTP_5XX", "high", f"Server error {status}", self.name, url))
        elif status >= 400:
            issues.append(SeoIssue("HTTP_4XX", "high", f"Client error {status}", self.name, url))
        elif 300 <= status < 400:
            issues.append(SeoIssue("HTTP_3XX", "low", f"Redirect response {status}", self.name, url))

        redirects = resp.get("num_redirects", 0) or 0
        if redirects > 1:
            issues.append(
                SeoIssue(
                    "REDIRECT_CHAIN",
                    "medium",
                    f"Redirect chain length is {redirects}",
                    self.name,
                    url,
                    details={"num_redirects": redirects},
                )
            )

        if resp.get("is_timeout"):
            issues.append(SeoIssue("REQUEST_TIMEOUT", "high", "Request timed out", self.name, url))

        return issues


class IndexabilityCanonicalCheck:
    name = "indexability_canonical"

    def run(self, resp: dict):
        if resp.get("status_code") != 200:
            return []

        content = resp.get("content")
        if not content:
            return []

        url = resp.get("url", "")
        parsed_url = urlparse(url)
        site_home = f"{parsed_url.scheme}://{parsed_url.netloc}/"

        soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "lxml")

        issues = []
        canonical_tag = soup.find("link", attrs={"rel": lambda v: v and "canonical" in [x.lower() for x in (v if isinstance(v, list) else [v])]})
        canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""

        if not canonical:
            issues.append(SeoIssue("CANONICAL_MISSING", "medium", "Canonical tag missing", self.name, url))
        else:
            if canonical.rstrip("/") == site_home.rstrip("/") and parsed_url.path not in ["", "/"]:
                issues.append(SeoIssue("CANONICAL_TO_HOMEPAGE", "high", "Canonical points to homepage", self.name, url))
            if canonical.rstrip("/") != url.rstrip("/"):
                issues.append(SeoIssue("CANONICAL_NOT_SELF", "low", "Canonical is not self-referential", self.name, url))

        robots_meta = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
        robots_value = (robots_meta.get("content", "") if robots_meta else "").lower()
        x_robots = str(resp.get("x_robots_tag", "")).lower()

        if "noindex" in robots_value or "noindex" in x_robots:
            issues.append(SeoIssue("NOINDEX_DETECTED", "high", "Page is marked noindex", self.name, url))

        return issues


class SchemaNewsArticleCheck:
    name = "schema_news_article"
    required_fields = ["headline", "datePublished", "dateModified", "author", "image", "publisher"]
    news_types = {
        "NewsArticle",
        "ReportageNewsArticle",
        "AnalysisNewsArticle",
        "BackgroundNewsArticle",
        "OpinionNewsArticle",
    }

    def run(self, resp: dict):
        if resp.get("status_code") != 200:
            return []
        content = resp.get("content")
        if not content:
            return []

        soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "lxml")
        scripts = soup.find_all("script", attrs={"type": "application/ld+json"})

        payloads: list[Any] = []
        for script in scripts:
            raw = (script.string or script.get_text() or "").strip()
            if not raw:
                continue

            # Try normal parse first, but don't lose the raw string if it fails.
            try:
                payloads.append(json.loads(html.unescape(raw)))
            except Exception:
                payloads.append(raw)

        news_obj = self._find_news_article(payloads)
        if not news_obj:
            return [SeoIssue("SCHEMA_NEWSARTICLE_MISSING", "high", "NewsArticle schema not found", self.name, resp.get("url", ""))]

        missing = [f for f in self.required_fields if not self._has_field(news_obj, f)]
        if missing:
            return [
                SeoIssue(
                    "SCHEMA_REQUIRED_FIELDS_MISSING",
                    "high",
                    f"NewsArticle schema is missing required fields: {', '.join(missing)}",
                    self.name,
                    resp.get("url", ""),
                    details={"missing_fields": missing},
                )
            ]
        return []

    @staticmethod
    def _coerce_jsonld(obj: Any) -> Any:
        if isinstance(obj, (dict, list)):
            return obj

        if isinstance(obj, (bytes, bytearray)):
            obj = obj.decode("utf-8", "ignore")

        if isinstance(obj, str):
            s = html.unescape(obj).strip()
            if not s:
                return None

            dec = json.JSONDecoder()
            out = []
            i = 0
            while i < len(s):
                try:
                    val, j = dec.raw_decode(s, i)
                    out.append(val)
                    i = j
                    while i < len(s) and s[i] in " \t\r\n,":
                        i += 1
                except json.JSONDecodeError:
                    break

            if not out:
                return None
            return out[0] if len(out) == 1 else out

        return None

    def _is_news_type(self, typ: Any) -> bool:
        if typ is None:
            return False
        if isinstance(typ, str):
            t = typ.split(":")[-1].strip()  # schema:NewsArticle
            return t in self.news_types
        if isinstance(typ, list):
            return any(self._is_news_type(t) for t in typ)
        if isinstance(typ, dict) and "@id" in typ:
            return self._is_news_type(typ["@id"])
        return False

    def _walk_for_news(self, obj: Any, _seen: Optional[set[int]] = None):
        if _seen is None:
            _seen = set()

        obj = self._coerce_jsonld(obj)
        if obj is None:
            return None

        oid = id(obj)
        if oid in _seen:
            return None
        _seen.add(oid)

        if isinstance(obj, dict):
            if self._is_news_type(obj.get("@type")):
                return obj
            for v in obj.values():
                found = self._walk_for_news(v, _seen)
                if found:
                    return found

        elif isinstance(obj, list):
            for item in obj:
                found = self._walk_for_news(item, _seen)
                if found:
                    return found

        return None

    def _find_news_article(self, payloads):
        for obj in payloads:
            found = self._walk_for_news(obj)
            if found:
                return found
        return None

    def _has_field(self, obj: dict, field: str) -> bool:
        val = obj.get(field)
        if isinstance(val, str):
            return bool(val.strip())
        if isinstance(val, list):
            return len(val) > 0
        return val is not None


class ImageOptimizationCheck:
    name = "image_optimization"

    def __init__(self, max_image_size_bytes=102400):
        self.max_image_size_bytes = max_image_size_bytes

    def run(self, resp: dict):
        if resp.get("status_code") != 200:
            return []

        content = resp.get("content")
        if not content:
            return []

        soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "lxml")
        images = soup.find_all("img")
        if not images:
            return []

        issues = []
        alt_missing_reported = False
        for i, img in enumerate(images):
            alt = img.get("alt")
            if (alt is None or not str(alt).strip()) and not alt_missing_reported:
                issues.append(SeoIssue("IMAGE_ALT_MISSING", "low", "Image missing alt text", self.name, resp.get("url", "")))
                alt_missing_reported = True

            if i == 0:
                if (img.get("fetchpriority") or "").strip().lower() != "high":
                    issues.append(
                        SeoIssue(
                            "HERO_IMAGE_FETCHPRIORITY_MISSING",
                            "low",
                            "Hero image missing fetchpriority=high",
                            self.name,
                            resp.get("url", ""),
                        )
                    )
                src = img.get("src", "")
                if "size=" in src:
                    try:
                        size_value = int(re.search(r"size=(\d+)", src).group(1))
                        if size_value > self.max_image_size_bytes:
                            issues.append(SeoIssue("HERO_IMAGE_TOO_LARGE", "medium", "Hero image appears larger than 100KB", self.name, resp.get("url", "")))
                    except Exception:
                        pass
                continue

            loading = (img.get("loading") or "").strip().lower()
            if loading != "lazy":
                issues.append(
                    SeoIssue(
                        "IMAGE_LAZY_LOADING_MISSING",
                        "low",
                        "Non-hero images should use loading=lazy",
                        self.name,
                        resp.get("url", ""),
                    )
                )
                break

        return issues




class InternalLinkingCheck:
    name = "internal_linking"

    def __init__(self, max_external_links=30):
        # Interpreted as max UNIQUE external domains
        self.max_external_links = max_external_links

        # common tracking params to drop
        self._tracking_keys = {
            "fbclid", "gclid", "dclid", "msclkid", "igshid", "mc_cid", "mc_eid"
        }

    def _norm_host(self, netloc: str) -> str:
        h = (netloc or "").lower()
        return h[4:] if h.startswith("www.") else h

    def _strip_tracking(self, href: str) -> str:
        p = urlparse(href)

        # remove utm_* and a few known tracking keys; also drop fragment
        q = [
            (k, v)
            for (k, v) in parse_qsl(p.query, keep_blank_values=True)
            if not (k.lower().startswith("utm_") or k.lower() in self._tracking_keys)
        ]

        return urlunparse((
            p.scheme,
            p.netloc,
            p.path,
            "",  # drop params
            urlencode(q, doseq=True),
            ""   # drop fragment
        ))

    def run(self, resp: dict):
        if resp.get("status_code") != 200:
            return []

        content = resp.get("content")
        url = resp.get("url", "")
        if not content or not url:
            return []

        soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "lxml")
        anchors = soup.find_all("a", href=True)

        page_host = self._norm_host(urlparse(url).netloc)

        internal_count = 0
        weak_anchor_count = 0

        external_raw = 0
        external_domains = set()   # unique domains
        # external_urls = set()    # (optional) unique normalized URLs

        for a in anchors:
            href = (a.get("href") or "").strip()
            if not href:
                continue

            text = a.get_text(" ", strip=True).lower()
            if text in {"click here", "read more", "more"}:
                weak_anchor_count += 1

            # internal relative
            if href.startswith("/"):
                internal_count += 1
                continue

            if href.startswith("//"):
                href = "https:" + href
                
            # absolute http(s)
            if href.startswith("http://") or href.startswith("https://"):
                href2 = self._strip_tracking(href)
                h = self._norm_host(urlparse(href2).netloc)

                if h == page_host or not h:
                    internal_count += 1
                else:
                    external_raw += 1
                    external_domains.add(h)
                    # external_urls.add(href2)
                continue

            # everything else ignored: mailto:, tel:, javascript:, #, etc.

        external_unique = len(external_domains)  # <-- use this for threshold

        issues = []
        if internal_count == 0:
            issues.append(
                SeoIssue("NO_INTERNAL_LINKS", "medium", "No internal links detected on page", self.name, url)
            )

        if weak_anchor_count > 0:
            issues.append(
                SeoIssue(
                    "WEAK_ANCHOR_TEXT",
                    "low",
                    f"Detected {weak_anchor_count} weak anchor texts",
                    self.name,
                    url,
                )
            )

        if external_unique > self.max_external_links:
            issues.append(
                SeoIssue(
                    "TOO_MANY_EXTERNAL_LINKS",
                    "low",
                    f"Detected {external_unique} unique external domains (raw links: {external_raw})",
                    self.name,
                    url,
                )
            )

        return issues



class SecurityHeadersCheck:
    name = "security_headers"

    def run(self, resp: dict):
        url = resp.get("url", "")
        headers = {
            "Strict-Transport-Security": resp.get("strict_transport_security"),
            "Content-Security-Policy": resp.get("content_security_policy"),
            "X-Frame-Options": resp.get("x_frame_options"),
        }

        missing = [header for header, value in headers.items() if not value]
        if not missing:
            return []

        return [
            SeoIssue(
                "SECURITY_HEADERS_MISSING",
                "low",
                f"Missing security headers: {', '.join(missing)}",
                self.name,
                url,
                details={"missing_headers": missing},
            )
        ]
