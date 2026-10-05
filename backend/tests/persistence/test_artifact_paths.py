"""Tests that artifact paths are organized by domain first, then by scan time."""

from datetime import datetime
from pathlib import Path

from backend.domain.persistence.artifact_paths import ArtifactPaths

SCANNED_AT = datetime(2026, 10, 5, 14, 23, 1)


def test_raw_directory_is_domain_then_timestamp():
    raw_directory = ArtifactPaths(Path("artifacts")).raw_directory("gymshark.com", SCANNED_AT)

    assert raw_directory == Path("artifacts") / "raw" / "gymshark.com" / "2026-10-05T14-23-01"


def test_result_file_is_domain_then_timestamp_json():
    result_file = ArtifactPaths(Path("artifacts")).result_file("gymshark.com", SCANNED_AT)

    assert result_file == Path("artifacts") / "results" / "gymshark.com" / "2026-10-05T14-23-01.json"
