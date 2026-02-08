from ispider_core.seo.checks.content_quality import (
    ContentLengthCheck,
    HeadingStructureCheck,
    TitleMetaQualityCheck,
    UrlHygieneCheck,
)
from ispider_core.seo.checks.headings import H1TooLongCheck
from ispider_core.seo.checks.http_status import BrokenLinkCheck, HttpStatus503Check
from ispider_core.seo.checks.technical import (
    ImageOptimizationCheck,
    IndexabilityCanonicalCheck,
    InternalLinkingCheck,
    ResponseCrawlabilityCheck,
    SchemaNewsArticleCheck,
    SecurityHeadersCheck,
)


class SeoRunner:
    def __init__(self, conf, logger):
        self.conf = conf
        self.logger = logger
        self._checks = self._build_checks()

    def _build_checks(self):
        max_h1_chars = self.conf.get("SEO_H1_MAX_CHARS", 70)
        available = {
            "broken_links": BrokenLinkCheck(),
            "http_status_503": HttpStatus503Check(),
            "h1_too_long": H1TooLongCheck(max_chars=max_h1_chars),
            "response_crawlability": ResponseCrawlabilityCheck(),
            "title_meta_quality": TitleMetaQualityCheck(),
            "heading_structure": HeadingStructureCheck(),
            "indexability_canonical": IndexabilityCanonicalCheck(),
            "schema_news_article": SchemaNewsArticleCheck(),
            "image_optimization": ImageOptimizationCheck(),
            "internal_linking": InternalLinkingCheck(),
            "url_hygiene": UrlHygieneCheck(news_path_regex=r"^(?:/[a-z0-9-]+)*/\d{4}/\d{2}/\d{2}/[a-z0-9-]+/?$"),
            "content_length": ContentLengthCheck(),
            "security_headers": SecurityHeadersCheck(),
        }

        enabled = self.conf.get("SEO_ENABLED_CHECKS")
        disabled = set(self.conf.get("SEO_DISABLED_CHECKS", []))

        if not enabled:
            selected = set(available.keys())
        else:
            selected = set(enabled)

        active_names = [name for name in available if name in selected and name not in disabled]
        return [available[name] for name in active_names]

    def run(self, resp: dict):
        if not self.conf.get("SEO_CHECKS_ENABLED", True):
            return []

        issues = []
        for check in self._checks:
            try:
                check_issues = check.run(resp)
                if check_issues:
                    issues.extend([issue.to_dict() for issue in check_issues])
            except Exception as e:
                self.logger.debug(f"SEO check '{check.name}' failed for {resp.get('url')}: {e}")

        return issues
