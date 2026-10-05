"""Failures of the DNS engine: the resolver timed out, the domain does not exist, or the resolver is unreachable."""

from backend.domain.errors.scan_error import ScanError


class DnsResolutionTimeout(ScanError):
    engine = "dns"


class DnsDomainNotFound(ScanError):
    engine = "dns"


class DnsResolverUnreachable(ScanError):
    engine = "dns"
