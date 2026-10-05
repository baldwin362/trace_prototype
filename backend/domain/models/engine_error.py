"""A failure reported by one engine during a scan, so the other engines can still report."""

from pydantic import BaseModel


class EngineError(BaseModel):
    engine: str
    message: str
