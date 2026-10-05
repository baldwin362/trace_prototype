"""Tests that every include: of an SPF record becomes its own key, and that other TXT records are ignored."""

from backend.domain.dns.spf_record_normalizer import normalize_spf_records


def test_three_includes_give_three_keys():
    spf_record = "v=spf1 include:_spf.google.com include:sendgrid.net include:servers.mcsv.net ~all"

    extracted_keys = normalize_spf_records([spf_record])

    assert [extracted_key.key for extracted_key in extracted_keys] == ["_spf.google.com", "sendgrid.net", "servers.mcsv.net"]


def test_raw_value_is_the_include_token_as_written():
    extracted_keys = normalize_spf_records(["v=spf1 include:_SPF.Google.com ~all"])

    assert extracted_keys[0].key == "_spf.google.com"
    assert extracted_keys[0].raw_value == "include:_SPF.Google.com"


def test_non_spf_records_are_ignored():
    assert normalize_spf_records(["docusign=abc", "google-site-verification=xyz"]) == []
