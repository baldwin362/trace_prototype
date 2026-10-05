"""Tests that each header gives a name key and a name|value key, with the header as received as evidence."""

import httpx

from backend.domain.http.header_extractor import extract_headers


def build_response(headers):
    return httpx.Response(200, headers=headers, request=httpx.Request("GET", "https://example.com/"))


def test_header_gives_name_key_and_name_value_key():
    extracted_keys = extract_headers(build_response([("Powered-By", "Shopify")]))

    assert {(extracted_key.source, extracted_key.key) for extracted_key in extracted_keys} == {
        ("http:header_name", "powered-by"),
        ("http:header_value", "powered-by|shopify"),
    }


def test_evidence_is_the_header_as_received():
    extracted_keys = extract_headers(build_response([("powered-by", "Shopify")]))

    assert {extracted_key.raw_value for extracted_key in extracted_keys} == {"powered-by: Shopify"}


def test_set_cookie_headers_are_left_to_the_cookie_extractor():
    assert extract_headers(build_response([("set-cookie", "_shopify_y=abc")])) == []


def test_headers_of_every_redirect_hop_are_read(gymshark_response):
    raw_headers = {extracted_key.raw_value for extracted_key in extract_headers(gymshark_response)}

    assert "powered-by: Shopify" in raw_headers
