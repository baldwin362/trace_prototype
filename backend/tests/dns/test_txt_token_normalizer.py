"""Tests that verification TXT records become the name of the token, and that SPF records are left to the SPF normalizer."""

from backend.domain.dns.txt_token_normalizer import normalize_txt_tokens


def test_token_name_is_the_left_side_of_the_equals_sign():
    extracted_keys = normalize_txt_tokens(["docusign=abc"])

    assert extracted_keys[0].key == "docusign"
    assert extracted_keys[0].raw_value == "docusign=abc"


def test_token_name_is_lowercased():
    extracted_keys = normalize_txt_tokens(["MS=ms54108504"])

    assert extracted_keys[0].key == "ms"
    assert extracted_keys[0].raw_value == "MS=ms54108504"


def test_spf_records_are_skipped():
    assert normalize_txt_tokens(["v=spf1 include:_spf.google.com ~all"]) == []


def test_record_without_equals_sign_keeps_its_whole_text_as_key():
    extracted_keys = normalize_txt_tokens(["768A5D177E"])

    assert extracted_keys[0].key == "768a5d177e"
