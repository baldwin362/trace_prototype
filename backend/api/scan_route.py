"""POST /scan: scans one domain and returns the technologies detected, with evidence."""

from functools import cache

from fastapi import APIRouter, Depends

from backend.api.request_schemas import ScanRequest
from backend.api.response_schemas import ScanResponse
from backend.domain.scanner import Scanner, build_scanner

scan_router = APIRouter()


@cache
def get_scanner() -> Scanner:
    """Returns the Scanner used by the API. It is created on the first request and reused after that.

    Returns:
        The Scanner.

    Example:
        get_scanner() is get_scanner()   # True, always the same Scanner
    """
    return build_scanner()


@scan_router.post("/scan")
async def scan_domain(scan_request: ScanRequest, scanner: Scanner = Depends(get_scanner)) -> ScanResponse:
    """Handles POST /scan: scans the domain in the request body and returns what was detected.

    Args:
        scan_request: the request body, for example {"domain": "gymshark.com"}.
        scanner: the Scanner, given by get_scanner.

    Returns:
        The domain, its detections with evidence, the engine errors, and when it was scanned.

    Example:
        POST /scan  {"domain": "gymshark.com"}
        # {"domain": "gymshark.com", "detections": [{"technology": "Shopify", "evidence": "powered-by: Shopify", ...}], ...}
    """
    scan_result = await scanner.scan(scan_request.domain.lower())
    return ScanResponse.from_scan_result(scan_result)
