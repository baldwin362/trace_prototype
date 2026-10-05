"""Tests that the hostname of each security.txt Contact line is extracted, for URLs and for email addresses."""

from backend.domain.robots.security_contact_parser import parse_security_contacts


def test_url_contact_gives_its_hostname():
    extracted_keys = parse_security_contacts("Contact: https://hackerone.com/acme\nExpires: 2027-01-01T00:00:00Z")

    assert [extracted_key.key for extracted_key in extracted_keys] == ["hackerone.com"]
    assert extracted_keys[0].raw_value == "Contact: https://hackerone.com/acme"


def test_email_contact_gives_its_domain():
    extracted_keys = parse_security_contacts("Contact: mailto:security@Acme.com")

    assert [extracted_key.key for extracted_key in extracted_keys] == ["acme.com"]


def test_other_fields_are_ignored():
    assert parse_security_contacts("Policy: https://acme.com/policy\nPreferred-Languages: en") == []
