"""Entry point of the HTTP engine: requests the homepage, then detects technologies from headers, cookies and redirects.

The page body is not read here; the HTML engine does that.
"""

import json
from pathlib import Path

import httpx
from loguru import logger

from backend.domain.errors.http_errors import HttpConnectionFailed, HttpTimeout, HttpTooManyRedirects
from backend.domain.http.cookie_extractor import extract_cookie_names
from backend.domain.http.header_extractor import extract_headers
from backend.domain.http.http_detector import ENGINE_NAME, HttpDetector
from backend.domain.http.http_request_client import HttpRequestClient
from backend.domain.http.redirect_chain_extractor import extract_redirect_hostnames
from backend.domain.models.engine_error import EngineError
from backend.domain.models.scan_result import ScanResult
from backend.domain.rules.mapping_loader import load_mapping

MAPPINGS_DIRECTORY = Path(__file__).parent / "mappings"


class HttpEngine:
    name = ENGINE_NAME

    def __init__(self, http_request_client: HttpRequestClient):
        self.http_request_client = http_request_client
        self.http_detector = HttpDetector(
            header_name_mapping=load_mapping(MAPPINGS_DIRECTORY / "header_name.json"),
            header_value_mapping=load_mapping(MAPPINGS_DIRECTORY / "header_value.json"),
            cookie_name_mapping=load_mapping(MAPPINGS_DIRECTORY / "cookie_name.json"),
            redirect_hostname_mapping=load_mapping(MAPPINGS_DIRECTORY / "redirect_hostname.json"),
        )

    async def scan(self, domain: str) -> ScanResult:
        logger.info("{}  {:<7} engine started", domain, ENGINE_NAME)
        try:
            response = await self.http_request_client.fetch_homepage(domain)
        except (HttpConnectionFailed, HttpTimeout, HttpTooManyRedirects) as http_error:
            logger.warning("{}  {:<7} engine failed: {}", domain, ENGINE_NAME, http_error.message)
            return ScanResult(domain=domain, errors=[EngineError(engine=ENGINE_NAME, message=http_error.message)])

        extracted_keys = [
            *extract_headers(response),
            *extract_cookie_names(response),
            *extract_redirect_hostnames(response),
        ]
        detections = self.http_detector.detect(domain, extracted_keys)
        logger.info("{}  {:<7} engine finished with {} detections", domain, ENGINE_NAME, len(detections))
        return ScanResult(
            domain=domain,
            detections=detections,
            raw_artifacts={"http.json": json.dumps(describe_redirect_chain(response), indent=2)},
        )


def describe_redirect_chain(response: httpx.Response) -> list[dict]:
    return [
        {
            "url": str(hop_response.url),
            "status_code": hop_response.status_code,
            "headers": hop_response.headers.multi_items(),
        }
        for hop_response in [*response.history, response]
    ]
