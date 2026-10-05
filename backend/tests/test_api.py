"""Tests the HTTP API with a stand-in scanner, so no network is used."""

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.scan_route import get_scanner
from backend.domain.models.confidence import Confidence
from backend.domain.models.detection import Detection
from backend.domain.models.scan_result import ScanResult


class StandInScanner:
    async def scan(self, domain: str) -> ScanResult:
        detection = Detection(technology="Shopify", evidence="powered-by: Shopify", source="http:header_value", confidence=Confidence.MEDIUM)
        return ScanResult(domain=domain, detections=[detection], raw_artifacts={"html.html": "<html></html>"})


app.dependency_overrides[get_scanner] = StandInScanner
api_client = TestClient(app)


def test_health_answers_ok():
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scan_returns_detections_with_evidence_and_no_raw_artifacts():
    response = api_client.post("/scan", json={"domain": "Gymshark.com"})

    assert response.status_code == 200
    response_body = response.json()
    assert response_body["domain"] == "gymshark.com"
    assert response_body["detections"] == [
        {"technology": "Shopify", "evidence": "powered-by: Shopify", "source": "http:header_value", "confidence": "medium"}
    ]
    assert "raw_artifacts" not in response_body


def test_scan_rejects_something_that_is_not_a_domain():
    response = api_client.post("/scan", json={"domain": "not a domain"})

    assert response.status_code == 422
