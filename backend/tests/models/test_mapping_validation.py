"""Tests that a broken mapping file stops the program at load time instead of silently loading empty."""

import json

import pytest

from backend.domain.errors.mapping_errors import MappingFileMalformed, MappingFileNotFound
from backend.domain.models.confidence import Confidence
from backend.domain.models.lookup_strategy import LookupStrategy
from backend.domain.rules.mapping_loader import load_mapping


def test_valid_mapping_file_loads_with_its_strategy_and_confidence(tmp_path):
    mapping_file = tmp_path / "valid.json"
    mapping_file.write_text(json.dumps({"lookup_strategy": "suffix", "confidence": "high", "entries": {"a.com": "A", "b.com": None}}))

    mapping = load_mapping(mapping_file)

    assert mapping.name == "valid"
    assert mapping.lookup_strategy == LookupStrategy.SUFFIX
    assert mapping.confidence == Confidence.HIGH
    assert mapping.entries == {"a.com": "A", "b.com": None}


def test_invalid_json_raises_malformed(tmp_path):
    mapping_file = tmp_path / "broken.json"
    mapping_file.write_text('{"lookup_strategy": "exact", "entries": {')

    with pytest.raises(MappingFileMalformed):
        load_mapping(mapping_file)


def test_unknown_lookup_strategy_raises_malformed(tmp_path):
    mapping_file = tmp_path / "unknown_strategy.json"
    mapping_file.write_text(json.dumps({"lookup_strategy": "fuzzy", "confidence": "high", "entries": {}}))

    with pytest.raises(MappingFileMalformed):
        load_mapping(mapping_file)


def test_entries_that_are_not_strings_raise_malformed(tmp_path):
    mapping_file = tmp_path / "bad_entries.json"
    mapping_file.write_text(json.dumps({"lookup_strategy": "exact", "confidence": "high", "entries": {"a.com": ["A"]}}))

    with pytest.raises(MappingFileMalformed):
        load_mapping(mapping_file)


def test_missing_file_raises_not_found(tmp_path):
    with pytest.raises(MappingFileNotFound):
        load_mapping(tmp_path / "missing.json")
