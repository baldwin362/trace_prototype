"""Failure of the robots engine: the site could not be reached at all for its well-known paths."""

from backend.domain.errors.scan_error import ScanError


class WellKnownPathUnreachable(ScanError):
    engine = "robots"
