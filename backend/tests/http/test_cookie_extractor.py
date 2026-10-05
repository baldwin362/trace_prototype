"""Tests that cookie names are pulled out of Set-Cookie headers across the redirect chain."""

import httpx

from backend.domain.http.cookie_extractor import extract_cookie_names


def build_response(headers):
    return httpx.Response(200, headers=headers, request=httpx.Request("GET", "https://example.com/"))


def test_cookie_name_is_the_key_and_evidence_names_the_cookie():
    extracted_keys = extract_cookie_names(build_response([("set-cookie", "_shopify_y=abc123; path=/; secure")]))

    assert extracted_keys[0].key == "_shopify_y"
    assert extracted_keys[0].raw_value == "cookie: _shopify_y"
    assert extracted_keys[0].source == "http:cookie"


def test_same_cookie_set_twice_is_kept_once():
    extracted_keys = extract_cookie_names(build_response([("set-cookie", "a=1"), ("set-cookie", "a=2"), ("set-cookie", "b=3")]))

    assert [extracted_key.key for extracted_key in extracted_keys] == ["a", "b"]


def test_fixture_cookies_are_found(gymshark_response):
    cookie_names = {extracted_key.key for extracted_key in extract_cookie_names(gymshark_response)}

    assert "cart_currency" in cookie_names
