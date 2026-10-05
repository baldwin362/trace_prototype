"""Tests that CNAME targets become clean hostnames while the evidence keeps the queried name and the raw target."""

from backend.domain.dns.cname_record_normalizer import normalize_cname_records


def test_target_becomes_a_clean_hostname():
    extracted_keys = normalize_cname_records("www.gymshark.com", ["Shops.MyShopify.com."])

    assert extracted_keys[0].key == "shops.myshopify.com"
    assert extracted_keys[0].source == "dns:CNAME"


def test_evidence_contains_the_raw_target_unmodified():
    extracted_keys = normalize_cname_records("www.gymshark.com", ["Shops.MyShopify.com."])

    assert extracted_keys[0].raw_value == "www.gymshark.com CNAME Shops.MyShopify.com."
