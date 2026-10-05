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
from backend.domain.errors.dns_errors import DnsDomainNotFound, DnsResolutionTimeout, DnsResolverUnreachable
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
        logger.info("{}  {:<7} engine started", domain, ENGINE_NAME)
        try:
            records_by_type, cname_records_by_hostname = await asyncio.gather(
                self.fetch_bare_domain_records(domain),
                self.fetch_subdomain_cname_records(domain),
            )
        except (DnsDomainNotFound, DnsResolutionTimeout, DnsResolverUnreachable) as dns_error:
            logger.warning("{}  {:<7} engine failed: {}", domain, ENGINE_NAME, dns_error.message)
            return ScanResult(domain=domain, errors=[EngineError(engine=ENGINE_NAME, message=dns_error.message)])

        extracted_keys = [
            *normalize_mx_records(records_by_type["MX"]),
            *normalize_ns_records(records_by_type["NS"]),
            *normalize_spf_records(records_by_type["TXT"]),
            *normalize_txt_tokens(records_by_type["TXT"]),
        ]
        for queried_hostname, raw_cname_records in cname_records_by_hostname.items():
            extracted_keys.extend(normalize_cname_records(queried_hostname, raw_cname_records))

        detections = self.dns_detector.detect(domain, extracted_keys)
        logger.info("{}  {:<7} engine finished with {} detections", domain, ENGINE_NAME, len(detections))
        raw_dns_records = {**records_by_type, "CNAME": cname_records_by_hostname}
        return ScanResult(
            domain=domain,
            detections=detections,
            raw_artifacts={"dns.json": json.dumps(raw_dns_records, indent=2)},
        )

    async def fetch_bare_domain_records(self, domain: str) -> dict[str, list[str]]:
        raw_records_per_type = await asyncio.gather(
            *(self.dns_query_client.fetch_records(domain, record_type) for record_type in BARE_DOMAIN_RECORD_TYPES)
        )
        return dict(zip(BARE_DOMAIN_RECORD_TYPES, raw_records_per_type))

    async def fetch_subdomain_cname_records(self, domain: str) -> dict[str, list[str]]:
        candidate_hostnames = [f"{subdomain}.{domain}" for subdomain in self.subdomain_candidates]
        raw_records_per_hostname = await asyncio.gather(
            *(self.fetch_cname_records_or_nothing(candidate_hostname) for candidate_hostname in candidate_hostnames)
        )
        return {
            candidate_hostname: raw_cname_records
            for candidate_hostname, raw_cname_records in zip(candidate_hostnames, raw_records_per_hostname)
            if raw_cname_records
        }

    async def fetch_cname_records_or_nothing(self, candidate_hostname: str) -> list[str]:
        try:
            return await self.dns_query_client.fetch_records(candidate_hostname, "CNAME")
        except (DnsDomainNotFound, DnsResolutionTimeout):
            return []
