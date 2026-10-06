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
        """Checks each value from the well-known files against the JSON rule file for its kind.

        Args:
            domain: the domain being scanned, used in the logs, for example "gymshark.com".
            extracted_keys: the values made by the parsers. robots.txt paths go to path_prefix.json, ads.txt sellers to
                ads_seller.json, and so on.

        Returns:
            Every Detection found. An empty list if no value fits any rule.

        Example:
            robots_detector.detect("gymshark.com", parse_robots_directives("Disallow: /checkouts/"))
            # [Detection(technology="Shopify", evidence="Disallow: /checkouts/", source="robots:disallow", confidence="medium")]
        """
        detections = []
        for extracted_key in extracted_keys:
            matcher = self.matcher_by_source[extracted_key.source]
            detections.extend(matcher.match(domain, ENGINE_NAME, extracted_key))
        return detections
