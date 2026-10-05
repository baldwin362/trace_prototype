"""Tests the robots detector against a saved real robots.txt and against the real mapping files."""

from backend.domain.models.extracted_key import ExtractedKey
from backend.domain.robots.ads_seller_parser import parse_ads_sellers
from backend.domain.robots.robots_detector import WELLKNOWN_PATH_SOURCE
from backend.domain.robots.robots_directive_parser import parse_robots_directives
from backend.domain.robots.security_contact_parser import parse_security_contacts


def test_gymshark_robots_fixture_gives_shopify(robots_detector, gymshark_robots_text):
    detections = robots_detector.detect("example.com", parse_robots_directives(gymshark_robots_text))

    assert {detection.technology for detection in detections} == {"Shopify"}
    assert "Disallow: /checkouts/" in {detection.evidence for detection in detections}


def test_bug_bounty_platform_in_security_txt(robots_detector):
    detections = robots_detector.detect("example.com", parse_security_contacts("Contact: https://hackerone.com/acme"))

    assert [detection.technology for detection in detections] == ["HackerOne"]


def test_ad_seller_in_ads_txt(robots_detector):
    detections = robots_detector.detect("example.com", parse_ads_sellers("google.com, pub-1, DIRECT, f08c47fec0942fa0"))

    assert [detection.technology for detection in detections] == ["Google Ad Manager"]


def test_null_path_entry_is_not_reported(robots_detector):
    assert robots_detector.detect("example.com", parse_robots_directives("Disallow: /api/private")) == []


def test_present_apple_app_site_association_is_an_ios_app(robots_detector):
    present_file = ExtractedKey(
        key="/.well-known/apple-app-site-association",
        raw_value="200 https://example.com/.well-known/apple-app-site-association",
        source=WELLKNOWN_PATH_SOURCE,
    )

    detections = robots_detector.detect("example.com", [present_file])

    assert [detection.technology for detection in detections] == ["iOS App"]
