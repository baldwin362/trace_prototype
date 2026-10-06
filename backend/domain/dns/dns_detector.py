"""Sends each DNS lookup key to the mapping file for its record type and collects the detections."""

from backend.domain.dns.cname_record_normalizer import CNAME_SOURCE
from backend.domain.dns.mx_record_normalizer import MX_SOURCE
from backend.domain.dns.ns_record_normalizer import NS_SOURCE
from backend.domain.dns.spf_record_normalizer import SPF_SOURCE
from backend.domain.dns.txt_token_normalizer import TXT_TOKEN_SOURCE
from backend.domain.models.detection import Detection
from backend.domain.models.extracted_key import ExtractedKey
from backend.domain.models.mapping import Mapping
from backend.domain.rules.mapping_matcher import MappingMatcher

ENGINE_NAME = "dns"


class DnsDetector:
    def __init__(self, mx_mapping: Mapping, ns_mapping: Mapping, cname_mapping: Mapping, spf_mapping: Mapping, txt_token_mapping: Mapping):
        self.matcher_by_source = {
            MX_SOURCE: MappingMatcher(mx_mapping),
            NS_SOURCE: MappingMatcher(ns_mapping),
            CNAME_SOURCE: MappingMatcher(cname_mapping),
            SPF_SOURCE: MappingMatcher(spf_mapping),
            TXT_TOKEN_SOURCE: MappingMatcher(txt_token_mapping),
        }

    def detect(self, domain: str, extracted_keys: list[ExtractedKey]) -> list[Detection]:
        """Checks each DNS value against the JSON rule file for its record type.

        Args:
            domain: the domain being scanned, used in the logs, for example "gymshark.com".
            extracted_keys: the values made by the normalizers. MX values go to mx.json, NS values to ns.json, and so on.

        Returns:
            Every Detection found. An empty list if no value fits any rule.

        Example:
            dns_detector.detect("gymshark.com", normalize_mx_records(["10 aspmx.l.google.com."]))
            # [Detection(technology="Google Workspace", evidence="10 aspmx.l.google.com.", source="dns:MX", confidence="high")]
        """
        detections = []
        for extracted_key in extracted_keys:
            matcher = self.matcher_by_source[extracted_key.source]
            detections.extend(matcher.match(domain, ENGINE_NAME, extracted_key))
        return detections
