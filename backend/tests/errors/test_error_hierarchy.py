"""Tests that every engine exception is a ScanError, and that a missing record type is never treated as an error."""

import pytest

from backend.domain.dns.dns_engine import DnsEngine
from backend.domain.errors import dns_errors, html_errors, http_errors, mapping_errors, robots_errors
from backend.domain.errors.scan_error import ScanError

ENGINE_EXCEPTIONS = [
    (dns_errors.DnsResolutionTimeout, "dns"),
    (dns_errors.DnsDomainNotFound, "dns"),
    (dns_errors.DnsResolverUnreachable, "dns"),
    (http_errors.HttpConnectionFailed, "http"),
    (http_errors.HttpTimeout, "http"),
    (http_errors.HttpTooManyRedirects, "http"),
    (html_errors.HtmlFetchFailed, "html"),
    (html_errors.HtmlParseFailed, "html"),
    (robots_errors.WellKnownPathUnreachable, "robots"),
    (mapping_errors.MappingFileNotFound, "mapping"),
    (mapping_errors.MappingFileMalformed, "mapping"),
]


class DnsQueryClientWithOnlyAnARecord:
    async def fetch_records(self, hostname: str, record_type: str) -> list[str]:
        if hostname == "example.com" and record_type == "A":
            return ["93.184.215.14"]
        return []


@pytest.mark.parametrize("exception_class, engine_name", ENGINE_EXCEPTIONS)
def test_every_engine_exception_is_a_scan_error_with_its_engine_name(exception_class, engine_name):
    raised_error = exception_class("something went wrong")

    assert isinstance(raised_error, ScanError)
    assert raised_error.engine == engine_name
    assert raised_error.message == "something went wrong"


def test_no_records_is_not_an_error_concept():
    assert not hasattr(dns_errors, "DnsNoRecords")


@pytest.mark.asyncio
async def test_domain_without_mx_gives_no_detection_and_no_error():
    scan_result = await DnsEngine(DnsQueryClientWithOnlyAnARecord()).scan("example.com")

    assert scan_result.detections == []
    assert scan_result.errors == []
