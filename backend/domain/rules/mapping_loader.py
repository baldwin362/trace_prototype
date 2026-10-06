"""Reads mapping files from disk and validates them, failing loudly if a file is missing or malformed."""

import json
from functools import cache
from pathlib import Path

from loguru import logger
from pydantic import TypeAdapter, ValidationError

from backend.domain.errors.mapping_errors import (
    MappingFileMalformed,
    MappingFileNotFound,
)
from backend.domain.models.mapping import Mapping


def read_json_file(file_path: Path) -> object:
    """Reads a JSON file and returns its content as Python data.

    Args:
        file_path: the JSON file to read, for example backend/domain/dns/mappings/mx.json.

    Returns:
        The content of the file: a dict for a JSON object, a list for a JSON array.

    Raises:
        MappingFileNotFound: the file does not exist.
        MappingFileMalformed: the file is not valid JSON.

    Example:
        read_json_file(Path("backend/domain/dns/mappings/subdomains.json"))   # ['www', 'help', 'support', ...]
    """
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise MappingFileNotFound(f"{file_path} does not exist")
    except json.JSONDecodeError as decode_error:
        raise MappingFileMalformed(f"{file_path} is not valid JSON: {decode_error}")


@cache
def load_mapping(file_path: Path) -> Mapping:
    """Reads a rule file and returns it as a Mapping. Each file is only read once, later calls reuse the result.

    Args:
        file_path: the rule file to read, for example backend/domain/dns/mappings/mx.json.

    Returns:
        A Mapping with the file name, its lookup strategy, its confidence and its entries.

    Raises:
        MappingFileNotFound: the file does not exist.
        MappingFileMalformed: the file is not valid JSON, or is missing lookup_strategy, confidence or entries.

    Example:
        mx_mapping = load_mapping(Path("backend/domain/dns/mappings/mx.json"))

        mx_mapping.name                               # 'mx'
        mx_mapping.lookup_strategy                    # LookupStrategy.SUFFIX
        mx_mapping.entries["aspmx.l.google.com"]      # 'Google Workspace'
    """
    file_content = read_json_file(file_path)
    if not isinstance(file_content, dict):
        raise MappingFileMalformed(f"{file_path} must contain a JSON object")
    try:
        mapping = Mapping.model_validate({"name": file_path.stem, **file_content})
    except ValidationError as validation_error:
        raise MappingFileMalformed(
            f"{file_path} has an invalid shape: {validation_error}"
        )
    logger.info(
        "loaded mapping {} with {} entries", file_path.name, len(mapping.entries)
    )
    return mapping


@cache
def load_string_list(file_path: Path) -> list[str]:
    """Reads a JSON file that holds a list of strings. Each file is only read once, later calls reuse the result.

    Args:
        file_path: the file to read, for example backend/domain/dns/mappings/subdomains.json.

    Returns:
        The list of strings in the file.

    Raises:
        MappingFileNotFound: the file does not exist.
        MappingFileMalformed: the file is not valid JSON, or is not a list of strings.

    Example:
        load_string_list(Path("backend/domain/dns/mappings/subdomains.json"))   # ['www', 'help', 'support', ...]
    """
    file_content = read_json_file(file_path)
    try:
        string_list = TypeAdapter(list[str]).validate_python(file_content)
    except ValidationError as validation_error:
        raise MappingFileMalformed(
            f"{file_path} must be a list of strings: {validation_error}"
        )
    logger.info("loaded list {} with {} entries", file_path.name, len(string_list))
    return string_list
