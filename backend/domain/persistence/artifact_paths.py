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
        return self.root_directory / "raw" / domain / scanned_at.strftime(TIMESTAMP_FORMAT)

    def result_file(self, domain: str, scanned_at: datetime) -> Path:
        return self.root_directory / "results" / domain / f"{scanned_at.strftime(TIMESTAMP_FORMAT)}.json"
