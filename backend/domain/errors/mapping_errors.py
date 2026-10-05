"""Configuration failures: a mapping file is missing or is not valid. These stop the program at startup."""

from backend.domain.errors.scan_error import ScanError


class MappingFileNotFound(ScanError):
    engine = "mapping"


class MappingFileMalformed(ScanError):
    engine = "mapping"
