"""Command line entry point. Scans one or more domains and prints the technologies each one uses, with evidence.

Domains are scanned at the same time and each one is printed as soon as it finishes.
Results go to stdout, logs go to stderr, so `python main.py x.com --json > out.json` gives a clean JSON file.

    python main.py gymshark.com qonto.com
    python main.py --file domains.txt --save-artifacts
    python main.py gymshark.com --json --log-level DEBUG
    python main.py                                        opens a prompt to type domains one after another
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
    """Reads the options typed on the command line.

    Returns:
        The options: domains, file, json, resolver, save_artifacts, artifacts_dir, log_level and concurrency.

    Example:
        python main.py gymshark.com --json
        # Namespace(domains=["gymshark.com"], json=True, resolver="1.1.1.1", ...)
    """
    argument_parser = argparse.ArgumentParser(description="Detect the technologies a company uses from its domain.")
    argument_parser.add_argument("domains", nargs="*", help="domains to scan, e.g. gymshark.com")
    argument_parser.add_argument("--file", type=Path, help="text file with one domain per line")
    argument_parser.add_argument("--json", action="store_true", help="print one JSON result per line instead of a table")
    argument_parser.add_argument("--resolver", default="1.1.1.1", help="DNS resolver to query (default 1.1.1.1)")
    argument_parser.add_argument("--save-artifacts", action="store_true", help="write raw fetched data and results to disk")
    argument_parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"), help="where --save-artifacts writes (default ./artifacts)")
    argument_parser.add_argument("--log-level", default="INFO", help="DEBUG, INFO, WARNING or ERROR (default INFO)")
    argument_parser.add_argument("--concurrency", type=int, default=5, help="how many domains to scan at once (default 5)")
    return argument_parser.parse_args()


def read_domains(arguments: argparse.Namespace) -> list[str]:
    """Collects the domains to scan, from the command line and from the --file, if given.

    Args:
        arguments: the options read by parse_arguments.

    Returns:
        The domains in lowercase, without empty lines.

    Example:
        python main.py Gymshark.com --file domains.txt
        # ["gymshark.com", "zapier.com", "qonto.com", ...]
    """
    domains = list(arguments.domains)
    if arguments.file:
        domains.extend(arguments.file.read_text(encoding="utf-8").splitlines())
    return [domain.strip().lower() for domain in domains if domain.strip()]


def render_scan_result(scan_result: ScanResult) -> str:
    """Turns a scan result into the table printed in the terminal.

    Args:
        scan_result: the result of the scan.

    Returns:
        The domain on the first line, then one line per detection: technology, source, evidence.
        Errors and the client-side rendering note come last.

    Example:
        print(render_scan_result(scan_result))
        # gymshark.com
        #   Shopify                      http:header_value        powered-by: Shopify
        #   Shopify                      http:cookie              cookie: cart_currency
    """
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
    """Scans all the domains, a few at a time, and prints each result as soon as it is ready.

    Args:
        domains: the domains to scan, for example ["gymshark.com", "qonto.com"].
        arguments: the options read by parse_arguments (json, save_artifacts, concurrency...).

    Returns:
        True if every engine failed on every domain, False otherwise.

    Example:
        await scan_domains(["gymshark.com", "qonto.com"], arguments)
        # prints each domain's table as soon as its scan finishes, then returns False
    """
    scanner = build_scanner(resolver_address=arguments.resolver)
    artifact_paths = ArtifactPaths(arguments.artifacts_dir)
    artifact_writer = ArtifactWriter(artifact_paths)
    result_writer = ResultWriter(artifact_paths)
    concurrency_limit = asyncio.Semaphore(arguments.concurrency)

    async def scan_with_concurrency_limit(domain: str) -> ScanResult:
        """Scans one domain, waiting first if --concurrency domains are already being scanned.

        Args:
            domain: the domain to scan, for example "gymshark.com".

        Returns:
            The ScanResult of the domain.

        Example:
            With --concurrency 5 and 19 domains, the 6th domain waits until one of the first 5 is done.
        """
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


def run_interactive_prompt(arguments: argparse.Namespace) -> None:
    """Asks for domains again and again, and scans each line typed, until the user types exit.

    Args:
        arguments: the options read by parse_arguments (json, save_artifacts, concurrency...).

    Example:
        python main.py
        # trace> gymshark.com
        # ...gymshark.com's table...
        # trace> qonto.com figma.com
        # ...both tables...
        # trace> exit
    """
    print("Type one or more domains separated by spaces, or exit to quit.", flush=True)
    try:
        while True:
            typed_text = input("trace> ").strip().lower()
            if typed_text in ("exit", "quit"):
                return
            if typed_text:
                asyncio.run(scan_domains(typed_text.split(), arguments))
    except (EOFError, KeyboardInterrupt):
        print()


def main() -> int:
    """Runs the command line tool: reads the options, sets up the logs, scans the domains.

    With no domain and no --file, it opens the interactive prompt instead.

    Returns:
        The exit code: 1 if every engine failed on every domain, 0 otherwise.

    Example:
        python main.py gymshark.com   # prints the table, exits with 0
        python main.py                # opens the trace> prompt
    """
    arguments = parse_arguments()
    sys.stdout.reconfigure(encoding="utf-8")
    logger.remove()
    logger.add(sys.stderr, level=arguments.log_level.upper(), format="<green>{time:HH:mm:ss.SSS}</green> <level>{level: <7}</level> {message}")
    domains = read_domains(arguments)
    if not domains:
        run_interactive_prompt(arguments)
        return 0
    every_engine_failed_everywhere = asyncio.run(scan_domains(domains, arguments))
    return 1 if every_engine_failed_everywhere else 0


if __name__ == "__main__":
    sys.exit(main())
