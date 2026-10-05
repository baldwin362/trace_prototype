"""Tests that common lookalikes are not reported: public CDNs, social links, generic headers and cookies, lookalike hostnames."""

import httpx
from bs4 import BeautifulSoup

from backend.domain.dns.ns_record_normalizer import normalize_ns_records
from backend.domain.html.tag_url_extractor import extract_tag_urls
from backend.domain.html.url_hostname_normalizer import normalize_url_hostnames
from backend.domain.http.cookie_extractor import extract_cookie_names
from backend.domain.http.header_extractor import extract_headers
from backend.domain.robots.robots_directive_parser import parse_robots_directives

PAGE_WITH_ONLY_PUBLIC_CDNS_AND_SOCIAL_LINKS = """
<link href="https://fonts.googleapis.com/css2?family=Inter" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<img src="https://www.facebook.com/acme/photo.png">
<iframe src="https://www.youtube.com/embed/abc123"></iframe>
<img src="https://www.linkedin.com/company/acme/logo.png">
"""


def test_public_cdns_and_social_links_give_nothing(html_detector):
    extracted_keys = normalize_url_hostnames(extract_tag_urls(BeautifulSoup(PAGE_WITH_ONLY_PUBLIC_CDNS_AND_SOCIAL_LINKS, "lxml")))

    assert html_detector.detect("example.com", extracted_keys) == []


def test_lookalike_nameserver_is_not_cloudflare(dns_detector):
    assert dns_detector.detect("example.com", normalize_ns_records(["ns1.evilcloudflare.com."])) == []


def test_generic_headers_and_session_cookies_give_nothing(http_detector):
    response = httpx.Response(
        200,
        headers=[("x-request-id", "abc"), ("server", "nginx/1.25"), ("set-cookie", "JSESSIONID=1"), ("set-cookie", "PHPSESSID=2")],
        request=httpx.Request("GET", "https://example.com/"),
    )

    assert http_detector.detect("example.com", [*extract_headers(response), *extract_cookie_names(response)]) == []


def test_generic_robots_paths_give_nothing(robots_detector):
    assert robots_detector.detect("example.com", parse_robots_directives("Disallow: /api/\nDisallow: /search\nDisallow: /admin")) == []
