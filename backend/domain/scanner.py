"""Runs every engine on a domain at the same time and merges what they report into one ScanResult.

Each engine has its own time limit, so a slow engine cannot hold the others. An engine that crashes or times out
becomes an error in the result; the other engines still report. The scanner knows nothing about how engines detect.
"""

import asyncio
from typing import Protocol

from loguru import logger

from backend.domain.dns.dns_engine import DnsEngine
from backend.domain.dns.dns_query_client import DnsQueryClient
from backend.domain.html.html_engine import HtmlEngine
from backend.domain.html.html_request_client import HtmlRequestClient
from backend.domain.http.http_engine import HttpEngine
from backend.domain.http.http_request_client import HttpRequestClient
from backend.domain.models.engine_error import EngineError
from backend.domain.models.scan_result import ScanResult
from backend.domain.robots.robots_engine import RobotsEngine
from backend.domain.robots.wellknown_path_fetcher import WellKnownPathFetcher


class Engine(Protocol):
    name: str

    async def scan(self, domain: str) -> ScanResult:
        """What every engine must have: a scan method that takes a domain and returns a ScanResult.

        Args:
            domain: the domain to scan, for example "gymshark.com".

        Returns:
            The ScanResult of this engine alone.

        Example:
            DnsEngine, HttpEngine, HtmlEngine and RobotsEngine all have this method, so the Scanner can run any of them.
        """


class Scanner:
    def __init__(self, engines: list[Engine], engine_timeout_seconds: float = 30.0):
        self.engines = engines
        self.engine_timeout_seconds = engine_timeout_seconds

    async def scan(self, domain: str) -> ScanResult:
        """Runs every engine on a domain at the same time and puts their results together.

        Args:
            domain: the domain to scan, for example "gymshark.com".

        Returns:
            One ScanResult with the detections of every engine, sorted by technology name.
            An engine that crashes or takes longer than engine_timeout_seconds adds an error instead.

        Example:
            scanner = build_scanner()

            scan_result = await scanner.scan("gymshark.com")
            scan_result.detections[0]   # Detection(technology="Adobe", evidence="adobe-idp-site-verification=...", ...)
            scan_result.errors          # []
        """
        engine_outcomes = await asyncio.gather(
            *(asyncio.wait_for(engine.scan(domain), timeout=self.engine_timeout_seconds) for engine in self.engines),
            return_exceptions=True,
        )

        merged_result = ScanResult(domain=domain)
        for engine, engine_outcome in zip(self.engines, engine_outcomes):
            if isinstance(engine_outcome, ScanResult):
                merged_result.detections.extend(engine_outcome.detections)
                merged_result.errors.extend(engine_outcome.errors)
                merged_result.raw_artifacts.update(engine_outcome.raw_artifacts)
                merged_result.client_side_rendered = merged_result.client_side_rendered or engine_outcome.client_side_rendered
            else:
                error_message = describe_unexpected_failure(engine_outcome, self.engine_timeout_seconds)
                logger.warning("{}  {:<7} engine failed: {}", domain, engine.name, error_message)
                merged_result.errors.append(EngineError(engine=engine.name, message=error_message))

        merged_result.detections.sort(key=lambda detection: detection.technology.lower())
        return merged_result


def describe_unexpected_failure(failure: BaseException, engine_timeout_seconds: float) -> str:
    """Turns an engine crash or timeout into a short message for the scan result.

    Args:
        failure: the exception the engine ended with.
        engine_timeout_seconds: the time limit each engine had, used in the timeout message.

    Returns:
        The message, for example "timed out after 30.0 seconds" or "RuntimeError: unexpected bug".

    Example:
        describe_unexpected_failure(TimeoutError(), 30.0)                 # "timed out after 30.0 seconds"
        describe_unexpected_failure(RuntimeError("unexpected bug"), 30.0)  # "RuntimeError: unexpected bug"
    """
    if isinstance(failure, TimeoutError):
        return f"timed out after {engine_timeout_seconds} seconds"
    return f"{type(failure).__name__}: {failure}"


def build_scanner(resolver_address: str = "1.1.1.1") -> Scanner:
    """Creates a Scanner with the four engines: DNS, HTTP, HTML and robots.

    Args:
        resolver_address: the DNS resolver the DNS engine asks, for example "8.8.8.8". Defaults to "1.1.1.1".

    Returns:
        A Scanner ready to use.

    Example:
        scanner = build_scanner()
        [engine.name for engine in scanner.engines]   # ["dns", "http", "html", "robots"]
    """
    return Scanner(
        engines=[
            DnsEngine(DnsQueryClient(resolver_address=resolver_address)),
            HttpEngine(HttpRequestClient()),
            HtmlEngine(HtmlRequestClient()),
            RobotsEngine(WellKnownPathFetcher()),
        ]
    )
