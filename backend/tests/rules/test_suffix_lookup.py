"""Tests that the suffix lookup matches whole hostname labels from the right, preferring the longest entry."""

from backend.domain.rules.suffix_lookup import SuffixLookup


def test_subdomain_of_an_entry_matches():
    assert SuffixLookup(["ns.cloudflare.com"]).find_matching_entry_keys("kate.ns.cloudflare.com") == ["ns.cloudflare.com"]


def test_hostname_equal_to_an_entry_matches():
    assert SuffixLookup(["myshopify.com"]).find_matching_entry_keys("myshopify.com") == ["myshopify.com"]


def test_partial_label_does_not_match():
    assert SuffixLookup(["cloudflare.com"]).find_matching_entry_keys("evilcloudflare.com") == []


def test_longest_matching_entry_wins():
    suffix_lookup = SuffixLookup(["cloudflare.com", "cdnjs.cloudflare.com"])

    assert suffix_lookup.find_matching_entry_keys("cdnjs.cloudflare.com") == ["cdnjs.cloudflare.com"]
    assert suffix_lookup.find_matching_entry_keys("www.cloudflare.com") == ["cloudflare.com"]


def test_parent_of_an_entry_does_not_match():
    assert SuffixLookup(["ns.cloudflare.com"]).find_matching_entry_keys("cloudflare.com") == []
