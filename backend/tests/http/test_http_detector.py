"""Tests the HTTP detector against a saved real response and against the real mapping files."""

import httpx

from backend.domain.http.cookie_extractor import extract_cookie_names
from backend.domain.http.header_extractor import extract_headers
from backend.domain.http.redirect_chain_extractor import extract_redirect_hostnames
from backend.domain.models.extracted_key import ExtractedKey


def detect_from_response(http_detector, response):
    extracted_keys = [*extract_headers(response), *extract_cookie_names(response), *extract_redirect_hostnames(response)]
    return http_detector.detect("example.com", extracted_keys)


def test_gymshark_fixture_gives_shopify_and_cloudflare(http_detector, gymshark_response):
    detections = detect_from_response(http_detector, gymshark_response)
    evidence_by_technology = {(detection.technology, detection.evidence) for detection in detections}

    assert ("Shopify", "powered-by: Shopify") in evidence_by_technology
    assert ("Shopify", "cookie: cart_currency") in evidence_by_technology
    assert ("Cloudflare", "server: cloudflare") in evidence_by_technology


def test_header_value_with_version_matches_by_prefix(http_detector):
    response = httpx.Response(200, headers=[("x-powered-by", "Next.js 14.2")], request=httpx.Request("GET", "https://example.com/"))

    detections = detect_from_response(http_detector, response)

    assert [detection.technology for detection in detections] == ["Next.js"]


def test_intercom_cookie_with_workspace_suffix_matches_by_prefix(http_detector):
    extracted_keys = [ExtractedKey(key="intercom-session-abc123", raw_value="cookie: intercom-session-abc123", source="http:cookie")]

    detections = http_detector.detect("example.com", extracted_keys)

    assert [detection.technology for detection in detections] == ["Intercom"]


def test_redirect_to_myshopify_is_detected(http_detector):
    extracted_keys = [ExtractedKey(key="acme.myshopify.com", raw_value="redirect: https://acme.myshopify.com/", source="http:redirect")]

    detections = http_detector.detect("example.com", extracted_keys)

    assert detections[0].technology == "Shopify"
    assert detections[0].evidence == "redirect: https://acme.myshopify.com/"
