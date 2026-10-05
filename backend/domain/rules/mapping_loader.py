"""Reads mapping files from disk and validates them, failing loudly if a file is missing or malformed."""

import json
from functools import cache
from pathlib import Path

from loguru import logger
from pydantic import TypeAdapter, ValidationError

from backend.domain.errors.mapping_errors import MappingFileMalformed, MappingFileNotFound
from backend.domain.models.mapping import Mapping


def read_json_file(file_path: Path) -> object:
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise MappingFileNotFound(f"{file_path} does not exist")
    except json.JSONDecodeError as decode_error:
        raise MappingFileMalformed(f"{file_path} is not valid JSON: {decode_error}")


@cache
def load_mapping(file_path: Path) -> Mapping:
    file_content = read_json_file(file_path)
    if not isinstance(file_content, dict):
        raise MappingFileMalformed(f"{file_path} must contain a JSON object")
    try:
        mapping = Mapping.model_validate({"name": file_path.stem, **file_content})
    except ValidationError as validation_error:
        raise MappingFileMalformed(f"{file_path} has an invalid shape: {validation_error}")
    logger.info("loaded mapping {} with {} entries", file_path.name, len(mapping.entries))
    return mapping


@cache
def load_string_list(file_path: Path) -> list[str]:
    file_content = read_json_file(file_path)
    try:
        string_list = TypeAdapter(list[str]).validate_python(file_content)
    except ValidationError as validation_error:
        raise MappingFileMalformed(f"{file_path} must be a list of strings: {validation_error}")
    logger.info("loaded list {} with {} entries", file_path.name, len(string_list))
    return string_list
