"""Matches one extracted key against one mapping file and turns every hit into a Detection.

The mapping file declares which lookup strategy to use and how confident a match is.
Every detection is logged the moment it is found. An entry whose value is null is recognized but never reported.
"""

from typing import Protocol

from loguru import logger

from backend.domain.models.detection import Detection
from backend.domain.models.extracted_key import ExtractedKey
from backend.domain.models.lookup_strategy import LookupStrategy
from backend.domain.models.mapping import Mapping
from backend.domain.rules.exact_lookup import ExactLookup
from backend.domain.rules.prefix_lookup import PrefixLookup
from backend.domain.rules.substring_scanner import SubstringScanner
from backend.domain.rules.suffix_lookup import SuffixLookup


class EntryKeyLookup(Protocol):
    def find_matching_entry_keys(self, key: str) -> list[str]: ...


LOOKUP_CLASS_BY_STRATEGY = {
    LookupStrategy.EXACT: ExactLookup,
    LookupStrategy.PREFIX: PrefixLookup,
    LookupStrategy.SUFFIX: SuffixLookup,
    LookupStrategy.SUBSTRING: SubstringScanner,
}


class MappingMatcher:
    def __init__(self, mapping: Mapping):
        self.mapping = mapping
        lookup_class = LOOKUP_CLASS_BY_STRATEGY[mapping.lookup_strategy]
        self.lookup: EntryKeyLookup = lookup_class(list(mapping.entries))

    def match(self, domain: str, engine_name: str, extracted_key: ExtractedKey) -> list[Detection]:
        matching_entry_keys = self.lookup.find_matching_entry_keys(extracted_key.key)
        if not matching_entry_keys:
            logger.debug("{}  {:<7} unknown key in {}: {}", domain, engine_name, self.mapping.name, extracted_key.key[:120])
            return []

        detections = []
        for matching_entry_key in matching_entry_keys:
            technology = self.mapping.entries[matching_entry_key]
            if technology is None:
                logger.debug("{}  {:<7} known key suppressed in {}: {}", domain, engine_name, self.mapping.name, matching_entry_key)
                continue
            detection = Detection(
                technology=technology,
                evidence=self.pick_evidence(extracted_key, matching_entry_key),
                source=extracted_key.source,
                confidence=self.mapping.confidence,
            )
            logger.info("{}  {:<7} {:<26} {}", domain, engine_name, detection.technology, detection.evidence)
            detections.append(detection)
        return detections

    def pick_evidence(self, extracted_key: ExtractedKey, matching_entry_key: str) -> str:
        if self.mapping.lookup_strategy == LookupStrategy.SUBSTRING:
            return matching_entry_key
        return extracted_key.raw_value
