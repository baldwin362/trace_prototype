"""Tests that each URL gives a hostname key and a hostname|path key, with the URL as evidence."""

from backend.domain.html.url_hostname_normalizer import normalize_url_hostnames
from backend.domain.models.extracted_key import ExtractedKey


def url_key(url):
    return ExtractedKey(key=url, raw_value=url, source="html:tag_url")


def test_url_gives_hostname_and_hostname_path_keys():
    extracted_keys = normalize_url_hostnames([url_key("https://www.facebook.com/tr?id=1&ev=PageView")])

    assert [(extracted_key.source, extracted_key.key) for extracted_key in extracted_keys] == [
        ("html:url_hostname", "www.facebook.com"),
        ("html:url_hostname_path", "www.facebook.com|/tr"),
    ]
    assert all(extracted_key.raw_value == "https://www.facebook.com/tr?id=1&ev=PageView" for extracted_key in extracted_keys)


def test_each_hostname_is_kept_once_with_its_first_url_as_evidence():
    extracted_keys = normalize_url_hostnames([url_key("https://images.ctfassets.net/a.png"), url_key("https://images.ctfassets.net/b.png")])
    hostname_keys = [extracted_key for extracted_key in extracted_keys if extracted_key.source == "html:url_hostname"]

    assert len(hostname_keys) == 1
    assert hostname_keys[0].raw_value == "https://images.ctfassets.net/a.png"


def test_malformed_url_is_skipped():
    assert normalize_url_hostnames([url_key("https://[broken/x.js")]) == []
