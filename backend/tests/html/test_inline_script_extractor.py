"""Tests that only scripts written in the page are collected, not scripts loaded from a URL."""

from bs4 import BeautifulSoup

from backend.domain.html.inline_script_extractor import extract_inline_scripts


def test_inline_scripts_are_joined_and_src_scripts_ignored():
    document = BeautifulSoup(
        "<script>fbq('init', '1');</script><script src='https://a.com/x.js'>ignored</script><script>var a = 1;</script>",
        "lxml",
    )

    extracted_keys = extract_inline_scripts(document)

    assert len(extracted_keys) == 1
    assert "fbq('init'" in extracted_keys[0].key
    assert "var a = 1;" in extracted_keys[0].key
    assert "ignored" not in extracted_keys[0].key


def test_page_without_inline_scripts_gives_nothing():
    assert extract_inline_scripts(BeautifulSoup("<p>hello</p>", "lxml")) == []
