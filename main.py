"""Command line entry point. Scans one or more domains and prints the technologies each one uses, with evidence.

Domains are scanned at the same time and each one is printed as soon as it finishes.
Results go to stdout, logs go to stderr, so `python main.py x.com --json > out.json` gives a clean JSON file.

    python main.py gymshark.com qonto.com
    python main.py --file domains.txt --save-artifacts
    python main.py gymshark.com --json --log-level DEBUG
"""

import argparse
import asyncio
import sys
from pathlib import Path

from loguru import logger

from backend.domain.models.scan_result import ScanResult
from backend.domain.persistence.artifact_paths import ArtifactPaths
from backend.domain.persistence.artifact_writer import ArtifactWriter
from backend.domain.persistence.result_writer import ResultWriter
from backend.domain.scanner import build_scanner

MAXIMUM_EVIDENCE_WIDTH = 140


def parse_arguments() -> argparse.Namespace:
    argument_parser = argparse.ArgumentParser(description="Detect the technologies a company uses from its domain.")
    argument_parser.add_argument("domains", nargs="*", help="domains to scan, e.g. gymshark.com")
    argument_parser.add_argument("--file", type=Path, help="text file with one domain per line")
    argument_parser.add_argument("--json", action="store_true", help="print one JSON result per line instead of a table")
    argument_parser.add_argument("--resolver", default="1.1.1.1", help="DNS resolver to query (default 1.1.1.1)")
    argument_parser.add_argument("--save-artifacts", action="store_true", help="write raw fetched data and results to disk")
    argument_parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"), help="where --save-artifacts writes (default ./artifacts)")
    argument_parser.add_argument("--log-level", default="INFO", help="DEBUG, INFO, WARNING or ERROR (default INFO)")
    argument_parser.add_argument("--concurrency", type=int, default=5, help="how many domains to scan at once (default 5)")
    arguments = argument_parser.parse_args()
    if not arguments.domains and not arguments.file:
        argument_parser.error("give at least one domain, or --file")
    return arguments


def read_domains(arguments: argparse.Namespace) -> list[str]:
    domains = list(arguments.domains)
    if arguments.file:
        domains.extend(arguments.file.read_text(encoding="utf-8").splitlines())
    return [domain.strip().lower() for domain in domains if domain.strip()]


def render_scan_result(scan_result: ScanResult) -> str:
    output_lines = [scan_result.domain]
    for detection in scan_result.detections:
        single_line_evidence = " ".join(detection.evidence.split())[:MAXIMUM_EVIDENCE_WIDTH]
        output_lines.append(f"  {detection.technology:<28} {detection.source:<24} {single_line_evidence}")
    if not scan_result.detections:
        output_lines.append("  no technology detected")
    if scan_result.client_side_rendered:
        output_lines.append("  note: the page looks client-side rendered, so HTML analysis is limited")
    for engine_error in scan_result.errors:
        output_lines.append(f"  error: {engine_error.engine} engine failed: {engine_error.message}")
    return "\n".join(output_lines) + "\n"


async def scan_domains(domains: list[str], arguments: argparse.Namespace) -> bool:
    scanner = build_scanner(resolver_address=arguments.resolver)
    artifact_paths = ArtifactPaths(arguments.artifacts_dir)
    artifact_writer = ArtifactWriter(artifact_paths)
    result_writer = ResultWriter(artifact_paths)
    concurrency_limit = asyncio.Semaphore(arguments.concurrency)

    async def scan_with_concurrency_limit(domain: str) -> ScanResult:
        async with concurrency_limit:
            return await scanner.scan(domain)

    every_engine_failed_everywhere = True
    for finished_scan in asyncio.as_completed([scan_with_concurrency_limit(domain) for domain in domains]):
        scan_result = await finished_scan
        if arguments.save_artifacts:
            artifact_writer.write(scan_result)
            result_writer.write(scan_result)
        print(scan_result.model_dump_json() if arguments.json else render_scan_result(scan_result), flush=True)
        if len(scan_result.errors) < len(scanner.engines):
            every_engine_failed_everywhere = False
    return every_engine_failed_everywhere


def main() -> int:
    arguments = parse_arguments()
    sys.stdout.reconfigure(encoding="utf-8")
    logger.remove()
    logger.add(sys.stderr, level=arguments.log_level.upper(), format="<green>{time:HH:mm:ss.SSS}</green> <level>{level: <7}</level> {message}")
    every_engine_failed_everywhere = asyncio.run(scan_domains(read_domains(arguments), arguments))
    return 1 if every_engine_failed_everywhere else 0


if __name__ == "__main__":
    sys.exit(main())
