"""Tests the DNS detector against saved real records and against the real mapping files."""

from backend.domain.dns.cname_record_normalizer import normalize_cname_records
from backend.domain.dns.mx_record_normalizer import normalize_mx_records
from backend.domain.dns.ns_record_normalizer import normalize_ns_records
from backend.domain.dns.spf_record_normalizer import normalize_spf_records
from backend.domain.dns.txt_token_normalizer import normalize_txt_tokens


def detect_from_records(dns_detector, records_by_type):
    extracted_keys = [
        *normalize_mx_records(records_by_type.get("MX", [])),
        *normalize_ns_records(records_by_type.get("NS", [])),
        *normalize_spf_records(records_by_type.get("TXT", [])),
        *normalize_txt_tokens(records_by_type.get("TXT", [])),
    ]
    return dns_detector.detect("example.com", extracted_keys)


def test_gymshark_fixture_gives_expected_technologies(dns_detector, gymshark_dns_records):
    detections = detect_from_records(dns_detector, gymshark_dns_records)
    detected_technologies = {detection.technology for detection in detections}

    assert {"Proofpoint", "AWS Route 53", "Microsoft 365", "Atlassian", "OneTrust", "Jamf"} <= detected_technologies


def test_evidence_is_the_raw_record_not_the_normalized_key(dns_detector):
    detections = detect_from_records(dns_detector, {"MX": ["10 aspmx.l.google.com."]})

    assert detections[0].technology == "Google Workspace"
    assert detections[0].evidence == "10 aspmx.l.google.com."


def test_any_cloudflare_nameserver_matches_the_suffix_entry(dns_detector):
    detections = detect_from_records(dns_detector, {"NS": ["kate.ns.cloudflare.com."]})

    assert [detection.technology for detection in detections] == ["Cloudflare"]


def test_aws_nameserver_matches_through_its_tld_entry(dns_detector):
    detections = detect_from_records(dns_detector, {"NS": ["ns-1622.awsdns-10.co.uk."]})

    assert [detection.technology for detection in detections] == ["AWS Route 53"]


def test_null_entry_is_recognized_but_not_reported(dns_detector):
    assert detect_from_records(dns_detector, {"TXT": ["yandex-verification=123abc"]}) == []


def test_cname_to_shopify_is_detected(dns_detector):
    extracted_keys = normalize_cname_records("shop.example.com", ["shops.myshopify.com."])

    detections = dns_detector.detect("example.com", extracted_keys)

    assert detections[0].technology == "Shopify"
    assert detections[0].evidence == "shop.example.com CNAME shops.myshopify.com."
