"""Tests that the substring scanner finds every pattern present in a block of text."""

from backend.domain.rules.substring_scanner import SubstringScanner


def test_every_present_pattern_is_found():
    substring_scanner = SubstringScanner(["fbq('init'", "_hsq.push", "absent"])

    assert substring_scanner.find_matching_entry_keys("fbq('init', 1); _hsq.push([]);") == ["fbq('init'", "_hsq.push"]


def test_matching_is_case_sensitive():
    assert SubstringScanner(["Sentry.init"]).find_matching_entry_keys("sentry.init()") == []
