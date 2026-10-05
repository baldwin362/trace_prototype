"""One piece of evidence that a domain uses a technology, with the exact raw string that proves it."""

from pydantic import BaseModel

from backend.domain.models.confidence import Confidence


class Detection(BaseModel):
    technology: str
    evidence: str
    source: str
    confidence: Confidence
