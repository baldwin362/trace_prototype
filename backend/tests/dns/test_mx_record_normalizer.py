"""Tests that MX records lose their priority and trailing dot, while the evidence keeps the record as received."""

from backend.domain.dns.mx_record_normalizer import normalize_mx_records


def test_priority_and_trailing_dot_are_removed():
    extracted_keys = normalize_mx_records(["10 aspmx.l.google.com."])

    assert extracted_keys[0].key == "aspmx.l.google.com"
    assert extracted_keys[0].raw_value == "10 aspmx.l.google.com."
    assert extracted_keys[0].source == "dns:MX"


def test_key_is_lowercased():
    extracted_keys = normalize_mx_records(["5 ALT1.ASPMX.L.GOOGLE.COM."])

    assert extracted_keys[0].key == "alt1.aspmx.l.google.com"


def test_every_raw_value_is_an_unmodified_fixture_record(gymshark_dns_records):
    extracted_keys = normalize_mx_records(gymshark_dns_records["MX"])

    assert [extracted_key.raw_value for extracted_key in extracted_keys] == gymshark_dns_records["MX"]
