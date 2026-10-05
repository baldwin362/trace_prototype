"""Tests that the generator meta tag is read and lowercased, and that pages without one give nothing."""

from bs4 import BeautifulSoup

from backend.domain.html.generator_meta_extractor import extract_generator_meta


def test_generator_content_is_lowercased_in_key_and_unchanged_in_evidence():
    document = BeautifulSoup('<meta name="generator" content="WordPress 6.4.2">', "lxml")

    extracted_keys = extract_generator_meta(document)

    assert extracted_keys[0].key == "wordpress 6.4.2"
    assert extracted_keys[0].raw_value == "WordPress 6.4.2"


def test_page_without_generator_gives_nothing():
    assert extract_generator_meta(BeautifulSoup('<meta name="description" content="hello">', "lxml")) == []
