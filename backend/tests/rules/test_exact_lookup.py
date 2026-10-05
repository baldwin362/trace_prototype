"""Tests that the exact lookup only matches keys that are exactly equal to an entry."""

from backend.domain.rules.exact_lookup import ExactLookup


def test_equal_key_matches():
    assert ExactLookup(["docusign", "ms"]).find_matching_entry_keys("docusign") == ["docusign"]


def test_longer_or_shorter_key_does_not_match():
    exact_lookup = ExactLookup(["docusign"])

    assert exact_lookup.find_matching_entry_keys("docusign-x") == []
    assert exact_lookup.find_matching_entry_keys("docu") == []
