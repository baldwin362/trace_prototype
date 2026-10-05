"""Everything a scan found for one domain: detections, engine errors, and the raw data that was fetched.

Each engine returns one of these for its own part of the scan, and the scanner merges them into one.
Raw artifacts are kept out of the serialized output; they are only written to disk on request.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from backend.domain.models.detection import Detection
from backend.domain.models.engine_error import EngineError


class ScanResult(BaseModel):
    domain: str
    detections: list[Detection] = Field(default_factory=list)
    errors: list[EngineError] = Field(default_factory=list)
    scanned_at: datetime = Field(default_factory=datetime.now)
    client_side_rendered: bool = False
    raw_artifacts: dict[str, str] = Field(default_factory=dict, exclude=True)
