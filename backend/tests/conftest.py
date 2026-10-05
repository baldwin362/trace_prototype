"""Shared test setup: saved real responses from disk, and detectors built from the real mapping files.

Nothing here touches the network. Matching is tested only against data that was fetched once and saved under fixtures/.
"""

import json
from pathlib import Path

import httpx
import pytest
from bs4 import BeautifulSoup

from backend.domain.dns.dns_detector import DnsDetector
from backend.domain.dns.dns_engine import MAPPINGS_DIRECTORY as DNS_MAPPINGS_DIRECTORY
from backend.domain.html.html_detector import HtmlDetector
from backend.domain.html.html_engine import MAPPINGS_DIRECTORY as HTML_MAPPINGS_DIRECTORY
from backend.domain.http.http_detector import HttpDetector
from backend.domain.http.http_engine import MAPPINGS_DIRECTORY as HTTP_MAPPINGS_DIRECTORY
from backend.domain.robots.robots_detector import RobotsDetector
from backend.domain.robots.robots_engine import MAPPINGS_DIRECTORY as ROBOTS_MAPPINGS_DIRECTORY
from backend.domain.rules.mapping_loader import load_mapping

FIXTURES_DIRECTORY = Path(__file__).parent / "fixtures"


def read_fixture(relative_path: str) -> str:
    return (FIXTURES_DIRECTORY / relative_path).read_text(encoding="utf-8")


def build_response(url: str, status_code: int = 200, headers: list[tuple[str, str]] | None = None) -> httpx.Response:
    return httpx.Response(status_code, headers=headers or [], request=httpx.Request("GET", url))


def build_response_chain(hops: list[dict]) -> httpx.Response:
    hop_responses = [
        build_response(hop["url"], hop["status_code"], [(header_name, header_value) for header_name, header_value in hop["headers"]])
        for hop in hops
    ]
    final_response = hop_responses[-1]
    final_response.history = hop_responses[:-1]
    return final_response


@pytest.fixture
def gymshark_dns_records() -> dict[str, list[str]]:
    return json.loads(read_fixture("dns/gymshark_records.json"))


@pytest.fixture
def gymshark_response() -> httpx.Response:
    return build_response_chain(json.loads(read_fixture("http/gymshark_response.json")))


@pytest.fixture
def gymshark_html() -> str:
    return read_fixture("html/gymshark_homepage.html")


@pytest.fixture
def gymshark_document(gymshark_html: str) -> BeautifulSoup:
    return BeautifulSoup(gymshark_html, "lxml")


@pytest.fixture
def gymshark_robots_text() -> str:
    return read_fixture("robots/gymshark_robots.txt")


@pytest.fixture
def dns_detector() -> DnsDetector:
    return DnsDetector(
        mx_mapping=load_mapping(DNS_MAPPINGS_DIRECTORY / "mx.json"),
        ns_mapping=load_mapping(DNS_MAPPINGS_DIRECTORY / "ns.json"),
        cname_mapping=load_mapping(DNS_MAPPINGS_DIRECTORY / "cname.json"),
        spf_mapping=load_mapping(DNS_MAPPINGS_DIRECTORY / "txt_spf.json"),
        txt_token_mapping=load_mapping(DNS_MAPPINGS_DIRECTORY / "txt_token.json"),
    )


@pytest.fixture
def http_detector() -> HttpDetector:
    return HttpDetector(
        header_name_mapping=load_mapping(HTTP_MAPPINGS_DIRECTORY / "header_name.json"),
        header_value_mapping=load_mapping(HTTP_MAPPINGS_DIRECTORY / "header_value.json"),
        cookie_name_mapping=load_mapping(HTTP_MAPPINGS_DIRECTORY / "cookie_name.json"),
        redirect_hostname_mapping=load_mapping(HTTP_MAPPINGS_DIRECTORY / "redirect_hostname.json"),
    )


@pytest.fixture
def html_detector() -> HtmlDetector:
    return HtmlDetector(
        hostname_mapping=load_mapping(HTML_MAPPINGS_DIRECTORY / "hostname.json"),
        hostname_path_mapping=load_mapping(HTML_MAPPINGS_DIRECTORY / "hostname_path.json"),
        generator_mapping=load_mapping(HTML_MAPPINGS_DIRECTORY / "generator.json"),
        inline_fingerprints_mapping=load_mapping(HTML_MAPPINGS_DIRECTORY / "inline_fingerprints.json"),
        framework_markers_mapping=load_mapping(HTML_MAPPINGS_DIRECTORY / "framework_markers.json"),
    )


@pytest.fixture
def robots_detector() -> RobotsDetector:
    return RobotsDetector(
        path_prefix_mapping=load_mapping(ROBOTS_MAPPINGS_DIRECTORY / "path_prefix.json"),
        security_contact_mapping=load_mapping(ROBOTS_MAPPINGS_DIRECTORY / "security_contact.json"),
        ads_seller_mapping=load_mapping(ROBOTS_MAPPINGS_DIRECTORY / "ads_seller.json"),
        wellknown_paths_mapping=load_mapping(ROBOTS_MAPPINGS_DIRECTORY / "wellknown_paths.json"),
    )
