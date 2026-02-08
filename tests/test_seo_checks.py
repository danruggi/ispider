import logging

from ispider_core.seo.checks.content_quality import (
    ContentLengthCheck,
    HeadingStructureCheck,
    TitleMetaQualityCheck,
    UrlHygieneCheck,
)
from ispider_core.seo.checks.technical import (
    ImageOptimizationCheck,
    IndexabilityCanonicalCheck,
    InternalLinkingCheck,
    ResponseCrawlabilityCheck,
    SchemaNewsArticleCheck,
    SecurityHeadersCheck,
)
from ispider_core.seo.runner import SeoRunner


def _resp(url="https://example.com/2026/02/07/test-article/", status=200, html=""):
    return {"url": url, "status_code": status, "content": html.encode("utf-8")}


def test_response_crawlability_flags_timeout_and_4xx():
    check = ResponseCrawlabilityCheck()
    issues = check.run({"url": "https://example.com/a", "status_code": 404, "is_timeout": True, "num_redirects": 2})
    codes = {i.code for i in issues}
    assert "HTTP_4XX" in codes
    assert "REQUEST_TIMEOUT" in codes
    assert "REDIRECT_CHAIN" in codes


def test_title_meta_quality_detects_missing_and_equal_h1():
    html = "<html><head><title>Headline</title></head><body><h1>Headline</h1></body></html>"
    issues = TitleMetaQualityCheck().run(_resp(html=html))
    codes = {i.code for i in issues}
    assert "TITLE_EQUALS_H1" in codes
    assert "META_DESCRIPTION_MISSING" in codes


def test_heading_structure_detects_multiple_h1_and_skip():
    html = "<h1>a</h1><h1>b</h1><h3>c</h3>"
    issues = HeadingStructureCheck().run(_resp(html=html))
    codes = {i.code for i in issues}
    assert "H1_MULTIPLE" in codes
    assert "HEADING_ORDER_SKIP" in codes


def test_indexability_canonical_flags_homepage_and_noindex():
    html = (
        '<head><link rel="canonical" href="https://example.com/" />'
        '<meta name="robots" content="noindex,follow"/></head>'
    )
    issues = IndexabilityCanonicalCheck().run(_resp(html=html))
    codes = {i.code for i in issues}
    assert "CANONICAL_TO_HOMEPAGE" in codes
    assert "NOINDEX_DETECTED" in codes


def test_schema_news_article_missing_required_fields():
    html = '<script type="application/ld+json">{"@type":"NewsArticle","headline":"x"}</script>'
    issues = SchemaNewsArticleCheck().run(_resp(html=html))
    assert issues and issues[0].code == "SCHEMA_REQUIRED_FIELDS_MISSING"


def test_image_optimization_flags_missing_attrs():
    html = '<img src="/hero.jpg" /><img src="/a.jpg" width="1" height="1" />'
    issues = ImageOptimizationCheck().run(_resp(html=html))
    codes = {i.code for i in issues}
    assert "IMAGE_DIMENSIONS_MISSING" in codes


def test_internal_linking_flags_none_and_weak_text():
    html = '<a href="https://outside.com">click here</a>'
    issues = InternalLinkingCheck().run(_resp(html=html))
    codes = {i.code for i in issues}
    assert "NO_INTERNAL_LINKS" in codes
    assert "WEAK_ANCHOR_TEXT" in codes


def test_url_hygiene_flags_pattern_uppercase_and_params():
    issues = UrlHygieneCheck().run(_resp(url="https://example.com/News/Today?x=1"))
    codes = {i.code for i in issues}
    assert "URL_UPPERCASE" in codes
    assert "URL_HAS_PARAMETERS" in codes
    assert "URL_NEWS_PATTERN_MISMATCH" in codes


def test_content_length_flags_thin_content():
    issues = ContentLengthCheck(min_words=10).run(_resp(html="<p>one two three</p>"))
    assert issues and issues[0].code == "CONTENT_TOO_THIN"


def test_security_headers_flags_missing_headers():
    issues = SecurityHeadersCheck().run({"url": "https://example.com", "status_code": 200})
    assert issues and issues[0].code == "SECURITY_HEADERS_MISSING"


def test_runner_includes_new_checks_and_runs():
    conf = {
        "SEO_CHECKS_ENABLED": True,
        "SEO_ENABLED_CHECKS": ["title_meta_quality", "security_headers"],
        "SEO_DISABLED_CHECKS": [],
    }
    runner = SeoRunner(conf, logging.getLogger("test"))
    result = runner.run(_resp(html="<html></html>"))
    codes = {i["code"] for i in result}
    assert "TITLE_MISSING" in codes
    assert "SECURITY_HEADERS_MISSING" in codes
