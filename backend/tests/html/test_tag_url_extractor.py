"""Tests that absolute URLs are collected from script, link, img and iframe tags, and relative ones are skipped."""

from bs4 import BeautifulSoup

from backend.domain.html.tag_url_extractor import extract_tag_urls


def extract_from(raw_html):
    return extract_tag_urls(BeautifulSoup(raw_html, "lxml"))


def test_urls_from_all_four_tags_are_collected():
    extracted_keys = extract_from(
        '<script src="https://a.com/x.js"></script><link href="https://b.com/y.css">'
        '<img src="https://c.com/z.png"><iframe src="https://d.com/frame"></iframe>'
    )

    assert [extracted_key.key for extracted_key in extracted_keys] == [
        "https://a.com/x.js",
        "https://b.com/y.css",
        "https://c.com/z.png",
        "https://d.com/frame",
    ]


def test_relative_urls_are_skipped():
    assert extract_from('<script src="/static/app.js"></script>') == []


def test_protocol_relative_url_gets_https_in_key_but_evidence_is_unchanged():
    extracted_keys = extract_from('<script src="//cdn.shopify.com/app.js"></script>')

    assert extracted_keys[0].key == "https://cdn.shopify.com/app.js"
    assert extracted_keys[0].raw_value == "//cdn.shopify.com/app.js"


def test_fixture_page_loads_shopify_assets(gymshark_document):
    urls = [extracted_key.key for extracted_key in extract_tag_urls(gymshark_document)]

    assert any("cdn.shopify.com" in url for url in urls)
