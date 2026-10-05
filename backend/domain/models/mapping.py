"""A detection rule file loaded from JSON: how to match it, how confident a match is, and its entries.

An entry whose value is null is a key we recognize and deliberately do not report.
"""

from pydantic import BaseModel

from backend.domain.models.confidence import Confidence
from backend.domain.models.lookup_strategy import LookupStrategy


class Mapping(BaseModel):
    name: str
    lookup_strategy: LookupStrategy
    confidence: Confidence
    entries: dict[str, str | None]
