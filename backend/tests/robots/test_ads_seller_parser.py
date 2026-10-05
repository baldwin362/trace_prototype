"""Tests that the seller domain of each ads.txt record is extracted once, and that non-records are skipped."""

from backend.domain.robots.ads_seller_parser import parse_ads_sellers


def test_seller_domain_is_the_first_field():
    extracted_keys = parse_ads_sellers("google.com, pub-123, DIRECT, f08c47fec0942fa0")

    assert extracted_keys[0].key == "google.com"
    assert extracted_keys[0].raw_value == "google.com, pub-123, DIRECT, f08c47fec0942fa0"


def test_each_seller_is_kept_once():
    extracted_keys = parse_ads_sellers("google.com, pub-1, DIRECT\ngoogle.com, pub-2, RESELLER\nopenx.com, 5, DIRECT")

    assert [extracted_key.key for extracted_key in extracted_keys] == ["google.com", "openx.com"]


def test_comments_and_short_lines_are_skipped():
    assert parse_ads_sellers("# ads.txt\ncontact=ads@acme.com\n<html>not found</html>") == []
