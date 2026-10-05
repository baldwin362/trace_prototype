"""How sure we are that a detection is real: high, medium or low."""

from enum import Enum


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
