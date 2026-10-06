"""Requests a list of well-known paths (robots.txt, ads.txt, security.txt...) on a domain, all at the same time.

A 404 is a normal answer and is returned like any other. A path that cannot be reached is logged and left out.
Only when no path at all can be reached is the site considered unreachable.
"""

import asyncio
import time

import httpx
from loguru import logger

from backend.domain.errors.robots_errors import WellKnownPathUnreachable

BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"


class WellKnownPathFetcher:
    def __init__(self, timeout_seconds: float = 8.0):
        self.timeout_seconds = timeout_seconds

    async def fetch_paths(self, domain: str, paths: list[str]) -> dict[str, httpx.Response]:
        """Downloads several files of a domain at the same time, for example its robots.txt and ads.txt.

        Args:
            domain: the domain to request, for example "gymshark.com".
            paths: the files to download, for example ["/robots.txt", "/ads.txt"].

        Returns:
            The response of each file that answered, a 404 included. Files that could not be reached are left out.

        Raises:
            WellKnownPathUnreachable: not a single file could be reached.

        Example:
            wellknown_path_fetcher = WellKnownPathFetcher()

            response_by_path = await wellknown_path_fetcher.fetch_paths("gymshark.com", ["/robots.txt", "/ads.txt"])
            response_by_path["/robots.txt"].status_code   # 200
            response_by_path["/ads.txt"].status_code      # 404
        """
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=self.timeout_seconds,
            headers={"User-Agent": BROWSER_USER_AGENT},
        ) as http_client:
            responses = await asyncio.gather(*(self.fetch_path(http_client, domain, path) for path in paths))

        response_by_path = {path: response for path, response in zip(paths, responses) if response is not None}
        if not response_by_path:
            raise WellKnownPathUnreachable(f"none of the {len(paths)} well-known paths of {domain} could be reached")
        return response_by_path

    async def fetch_path(self, http_client: httpx.AsyncClient, domain: str, path: str) -> httpx.Response | None:
        """Downloads one file of a domain, and returns None instead of failing.

        Args:
            http_client: the HTTP client shared by all the downloads of fetch_paths.
            domain: the domain to request, for example "gymshark.com".
            path: the file to download, for example "/robots.txt".

        Returns:
            The response, whatever its status code. None if the file could not be reached at all.

        Example:
            await wellknown_path_fetcher.fetch_path(http_client, "gymshark.com", "/robots.txt")   # <Response [200 OK]>
        """
        path_url = f"https://{domain}{path}"
        logger.debug("{}  robots  GET {} sent", domain, path_url)
        started_at = time.perf_counter()
        try:
            response = await http_client.get(path_url)
        except httpx.HTTPError as http_error:
            logger.warning("{}  robots  GET {} failed: {} {}", domain, path_url, type(http_error).__name__, http_error)
            return None
        elapsed_milliseconds = (time.perf_counter() - started_at) * 1000
        logger.debug("{}  robots  GET {} returned {} in {:.0f} ms", domain, path_url, response.status_code, elapsed_milliseconds)
        return response
