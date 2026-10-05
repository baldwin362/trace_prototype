"""Sends DNS queries to a public resolver and returns each record as plain text.

A name with no record of the asked type is normal and returns an empty list.
A name that does not exist, a timeout, or an unreachable resolver raises a DNS error.
"""

import time

import dns.asyncresolver
import dns.resolver
from loguru import logger

from backend.domain.errors.dns_errors import DnsDomainNotFound, DnsResolutionTimeout, DnsResolverUnreachable


class DnsQueryClient:
    def __init__(self, resolver_address: str = "1.1.1.1", timeout_seconds: float = 10.0):
        self.resolver = dns.asyncresolver.Resolver(configure=False)
        self.resolver.nameservers = [resolver_address]
        self.resolver.lifetime = timeout_seconds

    async def fetch_records(self, hostname: str, record_type: str) -> list[str]:
        logger.debug("{}  dns     query {} sent", hostname, record_type)
        started_at = time.perf_counter()
        try:
            answer = await self.resolver.resolve(hostname, record_type)
        except (dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            logger.debug("{}  dns     query {} returned nothing in {:.0f} ms", hostname, record_type, elapsed_milliseconds(started_at))
            return []
        except dns.resolver.NXDOMAIN:
            raise DnsDomainNotFound(f"{hostname} does not exist")
        except dns.resolver.LifetimeTimeout:
            raise DnsResolutionTimeout(f"no answer for {hostname} {record_type} within {self.resolver.lifetime} seconds")
        except OSError as network_error:
            raise DnsResolverUnreachable(f"resolver {self.resolver.nameservers[0]} is unreachable: {network_error}")

        raw_records = [record_to_text(record_data, record_type) for record_data in answer]
        logger.debug("{}  dns     query {} returned {} records in {:.0f} ms", hostname, record_type, len(raw_records), elapsed_milliseconds(started_at))
        return raw_records


def record_to_text(record_data, record_type: str) -> str:
    if record_type == "TXT":
        return b"".join(record_data.strings).decode("utf-8", errors="replace")
    return record_data.to_text()


def elapsed_milliseconds(started_at: float) -> float:
    return (time.perf_counter() - started_at) * 1000
