from ispider_core.seo.checks.headings import H1TooLongCheck
from ispider_core.seo.checks.http_status import BrokenLinkCheck, HttpStatus503Check


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
        }

        enabled = self.conf.get("SEO_ENABLED_CHECKS")
        disabled = set(self.conf.get("SEO_DISABLED_CHECKS", []))

        if not enabled:
            selected = set(available.keys())
        else:
            selected = set(enabled)

        active_names = [name for name in available if name in selected and name not in disabled]
        self.logger.info(f"SEO checks enabled: {', '.join(active_names)}")
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
