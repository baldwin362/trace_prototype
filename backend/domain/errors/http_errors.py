"""Failures of the HTTP engine: the connection failed, timed out, or redirected too many times."""

from backend.domain.errors.scan_error import ScanError


class HttpConnectionFailed(ScanError):
    engine = "http"


class HttpTimeout(ScanError):
    engine = "http"


class HttpTooManyRedirects(ScanError):
    engine = "http"
