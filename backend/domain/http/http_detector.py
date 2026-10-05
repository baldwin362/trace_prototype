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
        detections = []
        for extracted_key in extracted_keys:
            matcher = self.matcher_by_source[extracted_key.source]
            detections.extend(matcher.match(domain, ENGINE_NAME, extracted_key))
        return detections
