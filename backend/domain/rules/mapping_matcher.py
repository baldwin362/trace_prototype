"""Matches one extracted key against one mapping file and turns every hit into a Detection.

The mapping file declares which lookup strategy to use and how confident a match is.
Every detection is logged the moment it is found. An entry whose value is null is recognized but never reported.
"""

from typing import Literal, Protocol

from loguru import logger

from backend.domain.models.detection import Detection
from backend.domain.models.extracted_key import ExtractedKey
from backend.domain.models.lookup_strategy import LookupStrategy
from backend.domain.models.mapping import Mapping
from backend.domain.rules.exact_lookup import ExactLookup
from backend.domain.rules.prefix_lookup import PrefixLookup
from backend.domain.rules.substring_scanner import SubstringScanner
from backend.domain.rules.suffix_lookup import SuffixLookup

EngineName = Literal["dns", "http", "html", "robots"]


class EntryKeyLookup(Protocol):
    def find_matching_entry_keys(self, key: str) -> list[str]:
        """What every lookup must have: a method that takes a value and returns the JSON lines that fit it.

        Args:
            key: the value found on the website, for example "aspmx.l.google.com".

        Returns:
            The left side of each JSON line that fits, for example ["aspmx.l.google.com"]. An empty list if none fits.

        Example:
            ExactLookup, PrefixLookup, SuffixLookup and SubstringScanner all have this method,
            so the MappingMatcher can use any of them.
        """


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

    def match(
        self, domain: str, engine_name: EngineName, extracted_key: ExtractedKey
    ) -> list[Detection]:
        """Checks one value found on a website against the lines of one JSON rule file.

        Args:
            domain: the domain being scanned, used in the logs, for example "gymshark.com".
            engine_name: the engine that found the value, used in the logs, for example "dns".
            extracted_key: the value found on the website, for example an MX record.

        Returns:
            A list with one Detection per JSON line that fits the value.
            An empty list if no line fits, or if the line that fits is set to null.

        Example:
            mx_matcher = MappingMatcher(load_mapping(Path("backend/domain/dns/mappings/mx.json")))
            mx_record = ExtractedKey(key="aspmx.l.google.com", raw_value="10 aspmx.l.google.com.", source="dns:MX")

            mx_matcher.match("gymshark.com", "dns", mx_record)
            # [Detection(technology='Google Workspace', evidence='10 aspmx.l.google.com.', source='dns:MX', confidence='high')]
        """
        matching_entry_keys = self.lookup.find_matching_entry_keys(extracted_key.key)
        if not matching_entry_keys:
            logger.debug(
                "{}  {:<7} unknown key in {}: {}",
                domain,
                engine_name,
                self.mapping.name,
                extracted_key.key[:120],
            )
            return []

        detections = []
        for matching_entry_key in matching_entry_keys:
            technology = self.mapping.entries[matching_entry_key]
            if technology is None:
                logger.debug(
                    "{}  {:<7} known key suppressed in {}: {}",
                    domain,
                    engine_name,
                    self.mapping.name,
                    matching_entry_key,
                )
                continue
            detection = Detection(
                technology=technology,
                evidence=self.pick_evidence(extracted_key, matching_entry_key),
                source=extracted_key.source,
                confidence=self.mapping.confidence,
            )
            logger.info(
                "{}  {:<7} {:<26} {}",
                domain,
                engine_name,
                detection.technology,
                detection.evidence,
            )
            detections.append(detection)
        return detections

    def pick_evidence(
        self, extracted_key: ExtractedKey, matching_entry_key: str
    ) -> str:
        """Returns the text to show as proof of a detection.

        Args:
            extracted_key: the value found on the website.
            matching_entry_key: the JSON line that fits it.

        Returns:
            The value exactly as the website gave it, for example "10 aspmx.l.google.com.".
            For a text search (substring rule files), the matched rule instead, for example "fbq('init'",
            because the value found on the website is a whole page of text.
        """
        if self.mapping.lookup_strategy == LookupStrategy.SUBSTRING:
            return matching_entry_key
        return extracted_key.raw_value
