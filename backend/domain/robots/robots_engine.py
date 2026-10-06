"""Entry point of the robots engine: fetches the well-known paths of a domain, parses them, and detects technologies.

Only answers with status 200 that are not HTML pages are read, because many sites answer every unknown path
with their homepage. A well-known file that is present (e.g. apple-app-site-association) can itself be a detection.
"""

import json
from pathlib import Path

import httpx
from loguru import logger

from backend.domain.errors.robots_errors import WellKnownPathUnreachable
from backend.domain.models.engine_error import EngineError
from backend.domain.models.extracted_key import ExtractedKey
from backend.domain.models.scan_result import ScanResult
from backend.domain.robots.ads_seller_parser import parse_ads_sellers
from backend.domain.robots.robots_detector import ENGINE_NAME, WELLKNOWN_PATH_SOURCE, RobotsDetector
from backend.domain.robots.robots_directive_parser import parse_robots_directives
from backend.domain.robots.security_contact_parser import parse_security_contacts
from backend.domain.robots.wellknown_path_fetcher import WellKnownPathFetcher
from backend.domain.rules.mapping_loader import load_mapping

MAPPINGS_DIRECTORY = Path(__file__).parent / "mappings"
ROBOTS_PATH = "/robots.txt"
SECURITY_PATH = "/.well-known/security.txt"
ADS_PATH = "/ads.txt"


class RobotsEngine:
    name = ENGINE_NAME

    def __init__(self, wellknown_path_fetcher: WellKnownPathFetcher):
        self.wellknown_path_fetcher = wellknown_path_fetcher
        wellknown_paths_mapping = load_mapping(MAPPINGS_DIRECTORY / "wellknown_paths.json")
        self.wellknown_paths = list(wellknown_paths_mapping.entries)
        self.robots_detector = RobotsDetector(
            path_prefix_mapping=load_mapping(MAPPINGS_DIRECTORY / "path_prefix.json"),
            security_contact_mapping=load_mapping(MAPPINGS_DIRECTORY / "security_contact.json"),
            ads_seller_mapping=load_mapping(MAPPINGS_DIRECTORY / "ads_seller.json"),
            wellknown_paths_mapping=wellknown_paths_mapping,
        )

    async def scan(self, domain: str) -> ScanResult:
        """Downloads the well-known files of a domain (robots.txt, ads.txt...) and returns the technologies they reveal.

        Args:
            domain: the domain to scan, for example "gymshark.com".

        Returns:
            A ScanResult with the detections and the raw files. If no file can be reached,
            the ScanResult has no detections and one error instead.

        Example:
            robots_engine = RobotsEngine(WellKnownPathFetcher())

            scan_result = await robots_engine.scan("gymshark.com")
            scan_result.detections[0]   # Detection(technology="Shopify", evidence="Allow: /collections/account", ...)
        """
        logger.info("{}  {:<7} engine started", domain, ENGINE_NAME)
        try:
            response_by_path = await self.wellknown_path_fetcher.fetch_paths(domain, self.wellknown_paths)
        except WellKnownPathUnreachable as robots_error:
            logger.warning("{}  {:<7} engine failed: {}", domain, ENGINE_NAME, robots_error.message)
            return ScanResult(domain=domain, errors=[EngineError(engine=ENGINE_NAME, message=robots_error.message)])

        readable_response_by_path = {path: response for path, response in response_by_path.items() if is_readable_file(response)}
        extracted_keys = [
            *parse_robots_directives(read_text(readable_response_by_path, ROBOTS_PATH)),
            *parse_security_contacts(read_text(readable_response_by_path, SECURITY_PATH)),
            *parse_ads_sellers(read_text(readable_response_by_path, ADS_PATH)),
            *[
                ExtractedKey(key=path, raw_value=f"{response.status_code} {response.url}", source=WELLKNOWN_PATH_SOURCE)
                for path, response in readable_response_by_path.items()
            ],
        ]
        detections = self.robots_detector.detect(domain, extracted_keys)
        logger.info("{}  {:<7} engine finished with {} detections", domain, ENGINE_NAME, len(detections))
        raw_wellknown_files = {
            path: {"status_code": response.status_code, "body": response.text if path in readable_response_by_path else ""}
            for path, response in response_by_path.items()
        }
        return ScanResult(
            domain=domain,
            detections=detections,
            raw_artifacts={"robots.json": json.dumps(raw_wellknown_files, indent=2)},
        )


def is_readable_file(response: httpx.Response) -> bool:
    """Tells whether a downloaded file is worth reading.

    Many sites answer a missing file with their homepage, so an HTML page is not counted as the file.

    Args:
        response: the response for one file, for example /robots.txt.

    Returns:
        True if the status is 200 and the content is not an HTML page. False otherwise.

    Example:
        is_readable_file(robots_txt_response)        # True  (200, text/plain)
        is_readable_file(missing_ads_txt_response)   # False (404)
    """
    return response.status_code == 200 and "html" not in response.headers.get("content-type", "")


def read_text(readable_response_by_path: dict[str, httpx.Response], path: str) -> str:
    """Returns the content of one downloaded file, or an empty text if it was not downloaded.

    Args:
        readable_response_by_path: the files worth reading, by path.
        path: the file wanted, for example "/robots.txt".

    Returns:
        The content of the file, for example "User-agent: *\\nDisallow: /checkouts/". An empty string if it is missing.

    Example:
        read_text(readable_response_by_path, "/robots.txt")   # "User-agent: *\\nDisallow: /checkouts/ ..."
        read_text(readable_response_by_path, "/ads.txt")      # ""
    """
    if path not in readable_response_by_path:
        return ""
    return readable_response_by_path[path].text
