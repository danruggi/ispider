from ispider_core.seo.base import SeoIssue


class HttpStatus503Check:
    name = "http_status_503"

    def run(self, resp: dict):
        if resp.get("status_code") == 503:
            return [
                SeoIssue(
                    code="HTTP_503",
                    severity="high",
                    message="Service unavailable (503)",
                    check=self.name,
                    url=resp.get("url", ""),
                )
            ]
        return []


class BrokenLinkCheck:
    name = "broken_links"

    def run(self, resp: dict):
        status_code = resp.get("status_code")
        if status_code is None or status_code < 400:
            return []

        return [
            SeoIssue(
                code="BROKEN_LINK",
                severity="medium",
                message=f"URL returned status {status_code}",
                check=self.name,
                url=resp.get("url", ""),
                details={"status_code": status_code},
            )
        ]
