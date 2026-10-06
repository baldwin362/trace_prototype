"""Sends each HTTP lookup key (header name, header value, cookie, redirect hostname) to its mapping file and collects the detections."""

from backend.domain.http.cookie_extractor import COOKIE_SOURCE
from backend.domain.http.header_extractor import HEADER_NAME_SOURCE, HEADER_VALUE_SOURCE
from backend.domain.http.redirect_chain_extractor import REDIRECT_SOURCE
from backend.domain.models.detection import Detection
from backend.domain.models.extracted_key import ExtractedKey
from backend.domain.models.mapping import Mapping
from backend.domain.rules.mapping_matcher import MappingMatcher

ENGINE_NAME = "http"


class HttpDetector:
    def __init__(self, header_name_mapping: Mapping, header_value_mapping: Mapping, cookie_name_mapping: Mapping, redirect_hostname_mapping: Mapping):
        self.matcher_by_source = {
            HEADER_NAME_SOURCE: MappingMatcher(header_name_mapping),
            HEADER_VALUE_SOURCE: MappingMatcher(header_value_mapping),
            COOKIE_SOURCE: MappingMatcher(cookie_name_mapping),
            REDIRECT_SOURCE: MappingMatcher(redirect_hostname_mapping),
        }

    def detect(self, domain: str, extracted_keys: list[ExtractedKey]) -> list[Detection]:
        """Checks each HTTP value against the JSON rule file for its kind.

        Args:
            domain: the domain being scanned, used in the logs, for example "gymshark.com".
            extracted_keys: the values made by the extractors. Cookie names go to cookie_name.json, header names to
                header_name.json, and so on.

        Returns:
            Every Detection found. An empty list if no value fits any rule.

        Example:
            cookie = ExtractedKey(key="cart_currency", raw_value="cookie: cart_currency", source="http:cookie")

            http_detector.detect("gymshark.com", [cookie])
            # [Detection(technology="Shopify", evidence="cookie: cart_currency", source="http:cookie", confidence="high")]
        """
        detections = []
        for extracted_key in extracted_keys:
            matcher = self.matcher_by_source[extracted_key.source]
            detections.extend(matcher.match(domain, ENGINE_NAME, extracted_key))
        return detections
