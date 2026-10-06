"""Decides where scan files live on disk. This is the only place that knows the folder layout:

    <root>/raw/<domain>/<timestamp>/        the raw data fetched for one scan
    <root>/results/<domain>/<timestamp>.json the result of that scan

Folders are per domain first, so every past scan of a domain sits in one place and can be replayed against new rules.
"""

from datetime import datetime
from pathlib import Path

TIMESTAMP_FORMAT = "%Y-%m-%dT%H-%M-%S"


class ArtifactPaths:
    def __init__(self, root_directory: Path):
        self.root_directory = root_directory

    def raw_directory(self, domain: str, scanned_at: datetime) -> Path:
        """Returns the folder where the raw data of one scan is saved.

        Args:
            domain: the scanned domain, for example "gymshark.com".
            scanned_at: when the scan was made.

        Returns:
            The folder path: <root>/raw/<domain>/<date and time>.

        Example:
            artifact_paths = ArtifactPaths(Path("artifacts"))

            artifact_paths.raw_directory("gymshark.com", datetime(2026, 10, 5, 14, 23, 1))
            # Path("artifacts/raw/gymshark.com/2026-10-05T14-23-01")
        """
        return self.root_directory / "raw" / domain / scanned_at.strftime(TIMESTAMP_FORMAT)

    def result_file(self, domain: str, scanned_at: datetime) -> Path:
        """Returns the file where the result of one scan is saved.

        Args:
            domain: the scanned domain, for example "gymshark.com".
            scanned_at: when the scan was made.

        Returns:
            The file path: <root>/results/<domain>/<date and time>.json.

        Example:
            artifact_paths = ArtifactPaths(Path("artifacts"))

            artifact_paths.result_file("gymshark.com", datetime(2026, 10, 5, 14, 23, 1))
            # Path("artifacts/results/gymshark.com/2026-10-05T14-23-01.json")
        """
        return self.root_directory / "results" / domain / f"{scanned_at.strftime(TIMESTAMP_FORMAT)}.json"
