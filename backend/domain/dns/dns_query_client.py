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
        """Asks the DNS resolver for one type of record of one hostname.

        Args:
            hostname: the name to look up, for example "gymshark.com".
            record_type: the kind of record to ask for, for example "MX".

        Returns:
            One string per record, for example ["10 mx07-005a6901.pphosted.com.", "10 mx08-005a6901.pphosted.com."].
            An empty list if the hostname has no record of that type.

        Raises:
            DnsDomainNotFound: the hostname does not exist.
            DnsResolutionTimeout: the resolver did not answer in time.
            DnsResolverUnreachable: the resolver could not be contacted.

        Example:
            dns_query_client = DnsQueryClient()

            await dns_query_client.fetch_records("gymshark.com", "MX")    # ["10 mx07-005a6901.pphosted.com.", "10 mx08-005a6901.pphosted.com."]
            await dns_query_client.fetch_records("gymshark.com", "TXT")   # ["MS=ms54108504", "atlassian-domain-verification=...", ...]
        """
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
    """Turns one record returned by dnspython into a plain string.

    Args:
        record_data: one record from the resolver's answer.
        record_type: the kind of record, for example "MX" or "TXT".

    Returns:
        The record as text, for example "10 aspmx.l.google.com." for an MX record,
        or "MS=ms54108504" for a TXT record.

    Example:
        record_to_text(mx_record_data, "MX")    # "10 aspmx.l.google.com."
        record_to_text(txt_record_data, "TXT")  # "MS=ms54108504"
    """
    if record_type == "TXT":
        return b"".join(record_data.strings).decode("utf-8", errors="replace")
    return record_data.to_text()


def elapsed_milliseconds(started_at: float) -> float:
    """Returns how many milliseconds have passed since a start time, for the logs.

    Args:
        started_at: the start time, taken with time.perf_counter().

    Returns:
        The time passed in milliseconds, for example 42.7.

    Example:
        started_at = time.perf_counter()
        elapsed_milliseconds(started_at)   # 0.01
    """
    return (time.perf_counter() - started_at) * 1000
