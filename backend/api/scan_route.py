"""POST /scan: scans one domain and returns the technologies detected, with evidence."""

from functools import cache

from fastapi import APIRouter, Depends

from backend.api.request_schemas import ScanRequest
from backend.api.response_schemas import ScanResponse
from backend.domain.scanner import Scanner, build_scanner

scan_router = APIRouter()


@cache
def get_scanner() -> Scanner:
    return build_scanner()


@scan_router.post("/scan")
async def scan_domain(scan_request: ScanRequest, scanner: Scanner = Depends(get_scanner)) -> ScanResponse:
    scan_result = await scanner.scan(scan_request.domain.lower())
    return ScanResponse.from_scan_result(scan_result)
