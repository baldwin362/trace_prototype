"""Tests that the scanner merges engine results, and that a crashing or hanging engine never stops the others from reporting."""

import asyncio

import pytest

from backend.domain.models.confidence import Confidence
from backend.domain.models.detection import Detection
from backend.domain.models.scan_result import ScanResult
from backend.domain.scanner import Scanner


class WorkingEngine:
    def __init__(self, name: str, technology: str):
        self.name = name
        self.technology = technology

    async def scan(self, domain: str) -> ScanResult:
        detection = Detection(technology=self.technology, evidence=f"{self.name} evidence", source=f"{self.name}:test", confidence=Confidence.HIGH)
        return ScanResult(domain=domain, detections=[detection], raw_artifacts={f"{self.name}.json": "{}"})


class CrashingEngine:
    name = "crashing"

    async def scan(self, domain: str) -> ScanResult:
        raise RuntimeError("unexpected bug")


class HangingEngine:
    name = "hanging"

    async def scan(self, domain: str) -> ScanResult:
        await asyncio.sleep(10)
        return ScanResult(domain=domain)


@pytest.mark.asyncio
async def test_detections_of_all_engines_are_merged_and_sorted():
    scanner = Scanner([WorkingEngine("dns", "Zendesk"), WorkingEngine("http", "Cloudflare")])

    scan_result = await scanner.scan("example.com")

    assert [detection.technology for detection in scan_result.detections] == ["Cloudflare", "Zendesk"]
    assert set(scan_result.raw_artifacts) == {"dns.json", "http.json"}
    assert scan_result.errors == []


@pytest.mark.asyncio
async def test_failing_engines_become_errors_and_the_others_still_report():
    scanner = Scanner([WorkingEngine("dns", "Zendesk"), CrashingEngine(), HangingEngine()], engine_timeout_seconds=0.2)

    scan_result = await scanner.scan("example.com")

    assert [detection.technology for detection in scan_result.detections] == ["Zendesk"]
    error_message_by_engine = {engine_error.engine: engine_error.message for engine_error in scan_result.errors}
    assert error_message_by_engine == {
        "crashing": "RuntimeError: unexpected bug",
        "hanging": "timed out after 0.2 seconds",
    }


@pytest.mark.asyncio
async def test_same_technology_from_two_engines_keeps_both_evidences():
    scanner = Scanner([WorkingEngine("dns", "Shopify"), WorkingEngine("http", "Shopify")])

    scan_result = await scanner.scan("example.com")

    assert [detection.evidence for detection in scan_result.detections] == ["dns evidence", "http evidence"]
