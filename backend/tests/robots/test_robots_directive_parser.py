"""Tests that Disallow and Allow paths are pulled out of robots.txt, and everything else is ignored."""

from backend.domain.robots.robots_directive_parser import parse_robots_directives


def test_disallow_and_allow_paths_are_extracted():
    extracted_keys = parse_robots_directives("User-agent: *\nDisallow: /checkouts/\nAllow: /collections/\nSitemap: https://x.com/sitemap.xml")

    assert [(extracted_key.source, extracted_key.key) for extracted_key in extracted_keys] == [
        ("robots:disallow", "/checkouts/"),
        ("robots:allow", "/collections/"),
    ]


def test_evidence_is_the_line_as_written_and_comments_are_dropped_from_the_key():
    extracted_keys = parse_robots_directives("Disallow: /cdn-cgi/  # cloudflare")

    assert extracted_keys[0].key == "/cdn-cgi/"
    assert extracted_keys[0].raw_value == "Disallow: /cdn-cgi/  # cloudflare"


def test_empty_disallow_and_repeated_paths_are_skipped():
    extracted_keys = parse_robots_directives("Disallow:\nDisallow: /a\nDisallow: /a")

    assert [extracted_key.key for extracted_key in extracted_keys] == ["/a"]


def test_fixture_robots_contains_shopify_checkout_path(gymshark_robots_text):
    paths = {extracted_key.key for extracted_key in parse_robots_directives(gymshark_robots_text)}

    assert "/checkouts/" in paths
