"""The shape of the JSON the API returns. These are kept separate from the internal models so either can change alone."""

from datetime import datetime

from pydantic import BaseModel

from backend.domain.models.confidence import Confidence
from backend.domain.models.scan_result import ScanResult


class DetectionResponse(BaseModel):
    technology: str
    evidence: str
    source: str
    confidence: Confidence


class EngineErrorResponse(BaseModel):
    engine: str
    message: str


class ScanResponse(BaseModel):
    domain: str
    detections: list[DetectionResponse]
    errors: list[EngineErrorResponse]
    scanned_at: datetime
    client_side_rendered: bool

    @classmethod
    def from_scan_result(cls, scan_result: ScanResult) -> "ScanResponse":
        """Turns the scanner's ScanResult into the response the API sends back. The raw data is left out.

        Args:
            scan_result: the result of the scan.

        Returns:
            The ScanResponse, with the same domain, detections, errors, scan time and client_side_rendered flag.

        Example:
            ScanResponse.from_scan_result(scan_result).domain   # "gymshark.com"
        """
        return cls.model_validate(scan_result.model_dump())


class HealthResponse(BaseModel):
    status: str
