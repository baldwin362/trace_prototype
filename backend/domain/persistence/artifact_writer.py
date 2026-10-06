"""Writes the raw data fetched during a scan (DNS records, headers, HTML, well-known files) to disk."""

from loguru import logger

from backend.domain.models.scan_result import ScanResult
from backend.domain.persistence.artifact_paths import ArtifactPaths


class ArtifactWriter:
    def __init__(self, artifact_paths: ArtifactPaths):
        self.artifact_paths = artifact_paths

    def write(self, scan_result: ScanResult) -> None:
        """Saves the raw data of a scan (dns.json, http.json, html.html, robots.json) in its own folder.

        Args:
            scan_result: the result of the scan, holding the raw data in raw_artifacts.

        Example:
            artifact_writer = ArtifactWriter(ArtifactPaths(Path("artifacts")))

            artifact_writer.write(scan_result)
            # writes artifacts/raw/gymshark.com/2026-10-05T14-23-01/dns.json, http.json, html.html, robots.json
        """
        raw_directory = self.artifact_paths.raw_directory(scan_result.domain, scan_result.scanned_at)
        raw_directory.mkdir(parents=True, exist_ok=True)
        for artifact_file_name, artifact_content in scan_result.raw_artifacts.items():
            (raw_directory / artifact_file_name).write_text(artifact_content, encoding="utf-8")
        logger.info("{}  saved {} raw artifacts to {}", scan_result.domain, len(scan_result.raw_artifacts), raw_directory)
