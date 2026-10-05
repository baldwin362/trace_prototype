"""Tests that every hop of the redirect chain gives its hostname, with the full URL as evidence."""

from backend.domain.http.redirect_chain_extractor import extract_redirect_hostnames


def test_every_hop_gives_its_hostname(gymshark_response):
    extracted_keys = extract_redirect_hostnames(gymshark_response)

    assert [extracted_key.key for extracted_key in extracted_keys][0] == "gymshark.com"
    assert len(extracted_keys) == len(gymshark_response.history) + 1


def test_evidence_is_the_full_url(gymshark_response):
    extracted_keys = extract_redirect_hostnames(gymshark_response)

    assert extracted_keys[0].raw_value == "redirect: https://gymshark.com/"
