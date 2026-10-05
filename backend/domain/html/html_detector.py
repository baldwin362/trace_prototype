"""Sends each HTML lookup key to its mapping file and collects the detections.

URL hostnames, URL hostname+path, generator tags, inline scripts and the whole document each have their own mapping file.
"""

from backend.domain.html.generator_meta_extractor import GENERATOR_SOURCE
from backend.domain.html.inline_script_extractor import INLINE_SCRIPT_SOURCE
from backend.domain.html.url_hostname_normalizer import URL_HOSTNAME_PATH_SOURCE, URL_HOSTNAME_SOURCE
from backend.domain.models.detection import Detection
from backend.domain.models.extracted_key import ExtractedKey
from backend.domain.models.mapping import Mapping
from backend.domain.rules.mapping_matcher import MappingMatcher

ENGINE_NAME = "html"
DOCUMENT_SOURCE = "html:document"


class HtmlDetector:
    def __init__(
        self,
        hostname_mapping: Mapping,
        hostname_path_mapping: Mapping,
        generator_mapping: Mapping,
        inline_fingerprints_mapping: Mapping,
        framework_markers_mapping: Mapping,
    ):
        self.matcher_by_source = {
            URL_HOSTNAME_SOURCE: MappingMatcher(hostname_mapping),
            URL_HOSTNAME_PATH_SOURCE: MappingMatcher(hostname_path_mapping),
            GENERATOR_SOURCE: MappingMatcher(generator_mapping),
            INLINE_SCRIPT_SOURCE: MappingMatcher(inline_fingerprints_mapping),
            DOCUMENT_SOURCE: MappingMatcher(framework_markers_mapping),
        }

    def detect(self, domain: str, extracted_keys: list[ExtractedKey]) -> list[Detection]:
        detections = []
        for extracted_key in extracted_keys:
            matcher = self.matcher_by_source[extracted_key.source]
            detections.extend(matcher.match(domain, ENGINE_NAME, extracted_key))
        return detections
