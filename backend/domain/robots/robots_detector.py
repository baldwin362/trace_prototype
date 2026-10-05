"""Sends each robots lookup key (robots.txt path, security contact, ads seller, well-known file present) to its mapping file."""

from backend.domain.models.detection import Detection
from backend.domain.models.extracted_key import ExtractedKey
from backend.domain.models.mapping import Mapping
from backend.domain.robots.ads_seller_parser import ADS_SELLER_SOURCE
from backend.domain.robots.robots_directive_parser import ALLOW_SOURCE, DISALLOW_SOURCE
from backend.domain.robots.security_contact_parser import SECURITY_CONTACT_SOURCE
from backend.domain.rules.mapping_matcher import MappingMatcher

ENGINE_NAME = "robots"
WELLKNOWN_PATH_SOURCE = "robots:wellknown"


class RobotsDetector:
    def __init__(self, path_prefix_mapping: Mapping, security_contact_mapping: Mapping, ads_seller_mapping: Mapping, wellknown_paths_mapping: Mapping):
        path_prefix_matcher = MappingMatcher(path_prefix_mapping)
        self.matcher_by_source = {
            DISALLOW_SOURCE: path_prefix_matcher,
            ALLOW_SOURCE: path_prefix_matcher,
            SECURITY_CONTACT_SOURCE: MappingMatcher(security_contact_mapping),
            ADS_SELLER_SOURCE: MappingMatcher(ads_seller_mapping),
            WELLKNOWN_PATH_SOURCE: MappingMatcher(wellknown_paths_mapping),
        }

    def detect(self, domain: str, extracted_keys: list[ExtractedKey]) -> list[Detection]:
        detections = []
        for extracted_key in extracted_keys:
            matcher = self.matcher_by_source[extracted_key.source]
            detections.extend(matcher.match(domain, ENGINE_NAME, extracted_key))
        return detections
