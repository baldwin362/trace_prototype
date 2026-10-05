"""Writes a finished ScanResult to disk as JSON."""

from loguru import logger

from backend.domain.models.scan_result import ScanResult
from backend.domain.persistence.artifact_paths import ArtifactPaths


class ResultWriter:
    def __init__(self, artifact_paths: ArtifactPaths):
        self.artifact_paths = artifact_paths

    def write(self, scan_result: ScanResult) -> None:
        result_file = self.artifact_paths.result_file(scan_result.domain, scan_result.scanned_at)
        result_file.parent.mkdir(parents=True, exist_ok=True)
        result_file.write_text(scan_result.model_dump_json(indent=2), encoding="utf-8")
        logger.info("{}  saved result to {}", scan_result.domain, result_file)
