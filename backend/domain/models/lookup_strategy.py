"""The ways a mapping file can be matched against a key: exact, prefix, suffix or substring."""

from enum import Enum


class LookupStrategy(str, Enum):
    EXACT = "exact"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    SUBSTRING = "substring"
