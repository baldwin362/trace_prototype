"""Entry point of the DNS engine: queries a domain's DNS records, turns them into keys, and detects technologies.

The bare domain is queried for A, NS, MX and TXT, and a list of common subdomains is queried for CNAME, all at once.
A missing record is normal. Only a failure on the bare domain itself (it does not exist, or the resolver
does not answer) is reported as an engine error.
"""

import asyncio
import json
from pathlib import Path

from loguru import logger

from backend.domain.dns.cname_record_normalizer import normalize_cname_records
from backend.domain.dns.dns_detector import ENGINE_NAME, DnsDetector
from backend.domain.dns.dns_query_client import DnsQueryClient
from backend.domain.dns.mx_record_normalizer import normalize_mx_records
from backend.domain.dns.ns_record_normalizer import normalize_ns_records
from backend.domain.dns.spf_record_normalizer import normalize_spf_records
from backend.domain.dns.subdomain_candidates import load_subdomain_candidates
from backend.domain.dns.txt_token_normalizer import normalize_txt_tokens
from backend.domain.errors.dns_errors import (
    DnsDomainNotFound,
    DnsResolutionTimeout,
    DnsResolverUnreachable,
)
from backend.domain.models.engine_error import EngineError
from backend.domain.models.scan_result import ScanResult
from backend.domain.rules.mapping_loader import load_mapping

MAPPINGS_DIRECTORY = Path(__file__).parent / "mappings"
BARE_DOMAIN_RECORD_TYPES = ["A", "NS", "MX", "TXT"]


class DnsEngine:
    name = ENGINE_NAME

    def __init__(self, dns_query_client: DnsQueryClient):
        self.dns_query_client = dns_query_client
        self.subdomain_candidates = load_subdomain_candidates()
        self.dns_detector = DnsDetector(
            mx_mapping=load_mapping(MAPPINGS_DIRECTORY / "mx.json"),
            ns_mapping=load_mapping(MAPPINGS_DIRECTORY / "ns.json"),
            cname_mapping=load_mapping(MAPPINGS_DIRECTORY / "cname.json"),
            spf_mapping=load_mapping(MAPPINGS_DIRECTORY / "txt_spf.json"),
            txt_token_mapping=load_mapping(MAPPINGS_DIRECTORY / "txt_token.json"),
        )

    async def scan(self, domain: str) -> ScanResult:
        """Looks up the DNS records of a domain and returns the technologies they reveal.

        Args:
            domain: the domain to scan, for example "gymshark.com".

        Returns:
            A ScanResult with the detections and the raw records. If the domain does not exist or the
            resolver does not answer, the ScanResult has no detections and one error instead.

        Example:
            dns_engine = DnsEngine(DnsQueryClient())

            scan_result = await dns_engine.scan("gymshark.com")
            scan_result.detections[0].technology   # "Proofpoint"
            scan_result.detections[0].evidence     # "10 mx07-005a6901.pphosted.com."
        """
        logger.info("{}  {:<7} engine started", domain, ENGINE_NAME)
        try:
            records_by_type, cname_records_by_hostname = await asyncio.gather(
                self.fetch_bare_domain_records(domain),
                self.fetch_subdomain_cname_records(domain),
            )
        except (
            DnsDomainNotFound,
            DnsResolutionTimeout,
            DnsResolverUnreachable,
        ) as dns_error:
            logger.warning(
                "{}  {:<7} engine failed: {}", domain, ENGINE_NAME, dns_error.message
            )
            return ScanResult(
                domain=domain,
                errors=[EngineError(engine=ENGINE_NAME, message=dns_error.message)],
            )

        extracted_keys = [
            *normalize_mx_records(records_by_type["MX"]),
            *normalize_ns_records(records_by_type["NS"]),
            *normalize_spf_records(records_by_type["TXT"]),
            *normalize_txt_tokens(records_by_type["TXT"]),
        ]
        for queried_hostname, raw_cname_records in cname_records_by_hostname.items():
            extracted_keys.extend(
                normalize_cname_records(queried_hostname, raw_cname_records)
            )

        detections = self.dns_detector.detect(domain, extracted_keys)
        logger.info(
            "{}  {:<7} engine finished with {} detections",
            domain,
            ENGINE_NAME,
            len(detections),
        )
        raw_dns_records = {**records_by_type, "CNAME": cname_records_by_hostname}
        return ScanResult(
            domain=domain,
            detections=detections,
            raw_artifacts={"dns.json": json.dumps(raw_dns_records, indent=2)},
        )

    async def fetch_bare_domain_records(self, domain: str) -> dict[str, list[str]]:
        """Looks up the A, NS, MX and TXT records of the domain, all at the same time.

        Args:
            domain: the domain to look up, for example "gymshark.com".

        Returns:
            The records of each type, for example {"A": ["23.227.38.65"], "MX": ["10 mx07-005a6901.pphosted.com."], ...}.

        Raises:
            DnsDomainNotFound: the domain does not exist.
            DnsResolutionTimeout: the resolver did not answer in time.
            DnsResolverUnreachable: the resolver could not be contacted.

        Example:
            await dns_engine.fetch_bare_domain_records("gymshark.com")
            # {"A": ["23.227.38.65"], "NS": ["ns-947.awsdns-54.net.", ...], "MX": [...], "TXT": [...]}
        """
        raw_records_per_type = await asyncio.gather(
            *(
                self.dns_query_client.fetch_records(domain, record_type)
                for record_type in BARE_DOMAIN_RECORD_TYPES
            )
        )
        return dict(zip(BARE_DOMAIN_RECORD_TYPES, raw_records_per_type))

    async def fetch_subdomain_cname_records(self, domain: str) -> dict[str, list[str]]:
        """Looks up the CNAME record of each subdomain in subdomains.json, all at the same time.

        Args:
            domain: the domain to look up, for example "gymshark.com".

        Returns:
            The CNAME records of the subdomains that have one, for example
            {"www.gymshark.com": ["ingress.olympus.gymsharkapps.io."]}. Subdomains without a CNAME are left out.

        Example:
            await dns_engine.fetch_subdomain_cname_records("gymshark.com")
            # {"www.gymshark.com": ["ingress.olympus.gymsharkapps.io."], "autodiscover.gymshark.com": ["autodiscover.outlook.com."]}
        """
        candidate_hostnames = [
            f"{subdomain}.{domain}" for subdomain in self.subdomain_candidates
        ]
        raw_records_per_hostname = await asyncio.gather(
            *(
                self.fetch_cname_records_or_nothing(candidate_hostname)
                for candidate_hostname in candidate_hostnames
            )
        )
        return {
            candidate_hostname: raw_cname_records
            for candidate_hostname, raw_cname_records in zip(
                candidate_hostnames, raw_records_per_hostname
            )
            if raw_cname_records
        }

    async def fetch_cname_records_or_nothing(
        self, candidate_hostname: str
    ) -> list[str]:
        """Looks up the CNAME record of one subdomain, and returns nothing instead of failing.

        Args:
            candidate_hostname: the subdomain to look up, for example "support.gymshark.com".

        Returns:
            The CNAME records, for example ["support.olympus.gymsharkapps.io."].
            An empty list if the subdomain does not exist or the resolver did not answer in time.

        Example:
            await dns_engine.fetch_cname_records_or_nothing("autodiscover.gymshark.com")   # ["autodiscover.outlook.com."]
            await dns_engine.fetch_cname_records_or_nothing("jamf.gymshark.com")           # []
        """
        try:
            return await self.dns_query_client.fetch_records(
                candidate_hostname, "CNAME"
            )
        except (DnsDomainNotFound, DnsResolutionTimeout):
            return []
