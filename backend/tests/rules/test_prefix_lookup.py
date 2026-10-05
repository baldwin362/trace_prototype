"""Tests that the prefix lookup matches keys that start with an entry, preferring the longest entry."""

from backend.domain.rules.prefix_lookup import PrefixLookup


def test_key_starting_with_an_entry_matches():
    assert PrefixLookup(["server|nginx"]).find_matching_entry_keys("server|nginx/1.18.0") == ["server|nginx"]


def test_longest_matching_entry_wins():
    assert PrefixLookup(["/a", "/a/b"]).find_matching_entry_keys("/a/b/c") == ["/a/b"]


def test_key_not_starting_with_any_entry_does_not_match():
    assert PrefixLookup(["server|nginx"]).find_matching_entry_keys("x-server|nginx") == []
