"""Tests the HTML detector against a saved real page and against the real mapping files."""

from bs4 import BeautifulSoup

from backend.domain.html.generator_meta_extractor import extract_generator_meta
from backend.domain.html.html_detector import DOCUMENT_SOURCE
from backend.domain.html.inline_script_extractor import extract_inline_scripts
from backend.domain.html.tag_url_extractor import extract_tag_urls
from backend.domain.html.url_hostname_normalizer import normalize_url_hostnames
from backend.domain.models.extracted_key import ExtractedKey


def detect_from_html(html_detector, raw_html):
    document = BeautifulSoup(raw_html, "lxml")
    extracted_keys = [
        *normalize_url_hostnames(extract_tag_urls(document)),
        *extract_generator_meta(document),
        *extract_inline_scripts(document),
        ExtractedKey(key=raw_html, raw_value=raw_html, source=DOCUMENT_SOURCE),
    ]
    return html_detector.detect("example.com", extracted_keys)


def test_gymshark_fixture_gives_shopify(html_detector, gymshark_html):
    detections = detect_from_html(html_detector, gymshark_html)

    assert "Shopify" in {detection.technology for detection in detections}


def test_public_cdn_is_not_reported(html_detector):
    raw_html = '<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>'

    assert detect_from_html(html_detector, raw_html) == []


def test_facebook_tracking_pixel_is_meta_pixel(html_detector):
    detections = detect_from_html(html_detector, '<img src="https://www.facebook.com/tr?id=1&ev=PageView">')

    assert [detection.technology for detection in detections] == ["Meta Pixel"]
    assert detections[0].evidence == "https://www.facebook.com/tr?id=1&ev=PageView"


def test_facebook_profile_link_is_not_reported(html_detector):
    assert detect_from_html(html_detector, '<img src="https://www.facebook.com/gymshark">') == []


def test_inline_pixel_snippet_is_meta_pixel(html_detector):
    detections = detect_from_html(html_detector, "<script>fbq('init', '123456');</script>")

    assert [detection.technology for detection in detections] == ["Meta Pixel"]
    assert detections[0].evidence == "fbq('init'"


def test_regional_vendor_subdomain_matches_by_suffix(html_detector):
    detections = detect_from_html(html_detector, '<script src="https://cdn-eu.hotjar.com/x.js"></script>')

    assert [detection.technology for detection in detections] == ["Hotjar"]


def test_generator_tag_is_detected(html_detector):
    detections = detect_from_html(html_detector, '<meta name="generator" content="Webflow">')

    assert [detection.technology for detection in detections] == ["Webflow"]
