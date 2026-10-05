"""Failures of the HTML engine: the page could not be downloaded, or could not be parsed."""

from backend.domain.errors.scan_error import ScanError


class HtmlFetchFailed(ScanError):
    engine = "html"


class HtmlParseFailed(ScanError):
    engine = "html"
