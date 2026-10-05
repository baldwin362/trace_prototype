"""Entry point of the HTML engine: downloads the homepage, parses it, extracts keys, and detects technologies.

It also reports whether the page looks client-side rendered, since such pages reveal less without a browser.
"""

from pathlib import Path

from loguru import logger

from backend.domain.errors.html_errors import HtmlFetchFailed, HtmlParseFailed
from backend.domain.html.client_side_rendering_detector import is_client_side_rendered
from backend.domain.html.generator_meta_extractor import extract_generator_meta
from backend.domain.html.html_detector import DOCUMENT_SOURCE, ENGINE_NAME, HtmlDetector
from backend.domain.html.html_document_parser import parse_html_document
from backend.domain.html.html_request_client import HtmlRequestClient
from backend.domain.html.inline_script_extractor import extract_inline_scripts
from backend.domain.html.tag_url_extractor import extract_tag_urls
from backend.domain.html.url_hostname_normalizer import normalize_url_hostnames
from backend.domain.models.engine_error import EngineError
from backend.domain.models.extracted_key import ExtractedKey
from backend.domain.models.scan_result import ScanResult
from backend.domain.rules.mapping_loader import load_mapping

MAPPINGS_DIRECTORY = Path(__file__).parent / "mappings"


class HtmlEngine:
    name = ENGINE_NAME

    def __init__(self, html_request_client: HtmlRequestClient):
        self.html_request_client = html_request_client
        self.html_detector = HtmlDetector(
            hostname_mapping=load_mapping(MAPPINGS_DIRECTORY / "hostname.json"),
            hostname_path_mapping=load_mapping(MAPPINGS_DIRECTORY / "hostname_path.json"),
            generator_mapping=load_mapping(MAPPINGS_DIRECTORY / "generator.json"),
            inline_fingerprints_mapping=load_mapping(MAPPINGS_DIRECTORY / "inline_fingerprints.json"),
            framework_markers_mapping=load_mapping(MAPPINGS_DIRECTORY / "framework_markers.json"),
        )

    async def scan(self, domain: str) -> ScanResult:
        logger.info("{}  {:<7} engine started", domain, ENGINE_NAME)
        try:
            raw_html = await self.html_request_client.fetch_homepage_html(domain)
            document = parse_html_document(raw_html)
        except (HtmlFetchFailed, HtmlParseFailed) as html_error:
            logger.warning("{}  {:<7} engine failed: {}", domain, ENGINE_NAME, html_error.message)
            return ScanResult(domain=domain, errors=[EngineError(engine=ENGINE_NAME, message=html_error.message)])

        extracted_keys = [
            *normalize_url_hostnames(extract_tag_urls(document)),
            *extract_generator_meta(document),
            *extract_inline_scripts(document),
            ExtractedKey(key=raw_html, raw_value=raw_html, source=DOCUMENT_SOURCE),
        ]
        detections = self.html_detector.detect(domain, extracted_keys)

        client_side_rendered = is_client_side_rendered(document)
        if client_side_rendered:
            logger.info("{}  {:<7} page looks client-side rendered, HTML analysis is limited", domain, ENGINE_NAME)
        logger.info("{}  {:<7} engine finished with {} detections", domain, ENGINE_NAME, len(detections))
        return ScanResult(
            domain=domain,
            detections=detections,
            client_side_rendered=client_side_rendered,
            raw_artifacts={"html.html": raw_html},
        )
