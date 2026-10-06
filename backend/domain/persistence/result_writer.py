"""Writes a finished ScanResult to disk as JSON."""

from loguru import logger

from backend.domain.models.scan_result import ScanResult
from backend.domain.persistence.artifact_paths import ArtifactPaths


class ResultWriter:
    def __init__(self, artifact_paths: ArtifactPaths):
        self.artifact_paths = artifact_paths

    def write(self, scan_result: ScanResult) -> None:
        """Saves the result of a scan (detections and errors) as a JSON file.

        Args:
            scan_result: the result of the scan.

        Example:
            result_writer = ResultWriter(ArtifactPaths(Path("artifacts")))

            result_writer.write(scan_result)
            # writes artifacts/results/gymshark.com/2026-10-05T14-23-01.json
        """
        result_file = self.artifact_paths.result_file(scan_result.domain, scan_result.scanned_at)
        result_file.parent.mkdir(parents=True, exist_ok=True)
        result_file.write_text(scan_result.model_dump_json(indent=2), encoding="utf-8")
        logger.info("{}  saved result to {}", scan_result.domain, result_file)
