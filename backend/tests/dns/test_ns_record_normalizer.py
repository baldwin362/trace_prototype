"""Tests that NS records lose their trailing dot and are lowercased."""

from backend.domain.dns.ns_record_normalizer import normalize_ns_records


def test_trailing_dot_is_removed_and_key_lowercased():
    extracted_keys = normalize_ns_records(["ADI.NS.CloudFlare.com."])

    assert extracted_keys[0].key == "adi.ns.cloudflare.com"
    assert extracted_keys[0].raw_value == "ADI.NS.CloudFlare.com."


def test_one_key_per_record(gymshark_dns_records):
    extracted_keys = normalize_ns_records(gymshark_dns_records["NS"])

    assert len(extracted_keys) == len(gymshark_dns_records["NS"])
    assert [extracted_key.raw_value for extracted_key in extracted_keys] == gymshark_dns_records["NS"]
