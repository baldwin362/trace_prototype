"""Performs one GET on a domain's homepage, following redirects and keeping every hop of the redirect chain.

Connection errors are retried once. Timeouts, too many redirects and any other HTTP failure are raised straight away.
"""

import time

import httpx
from loguru import logger

from backend.domain.errors.http_errors import HttpConnectionFailed, HttpTimeout, HttpTooManyRedirects

BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"


class HttpRequestClient:
    def __init__(self, timeout_seconds: float = 10.0, connection_attempts: int = 2):
        self.timeout_seconds = timeout_seconds
        self.connection_attempts = connection_attempts

    async def fetch_homepage(self, domain: str) -> httpx.Response:
        homepage_url = f"https://{domain}/"
        last_connection_error = None
        for attempt_number in range(1, self.connection_attempts + 1):
            logger.debug("{}  http    GET {} sent (attempt {})", domain, homepage_url, attempt_number)
            started_at = time.perf_counter()
            try:
                async with httpx.AsyncClient(
                    follow_redirects=True,
                    timeout=self.timeout_seconds,
                    headers={"User-Agent": BROWSER_USER_AGENT},
                ) as http_client:
                    response = await http_client.get(homepage_url)
            except httpx.ConnectError as connection_error:
                last_connection_error = connection_error
                logger.debug("{}  http    GET {} could not connect: {}", domain, homepage_url, connection_error)
                continue
            except httpx.TimeoutException:
                raise HttpTimeout(f"{homepage_url} did not answer within {self.timeout_seconds} seconds")
            except httpx.TooManyRedirects:
                raise HttpTooManyRedirects(f"{homepage_url} redirected too many times")
            except httpx.HTTPError as http_error:
                raise HttpConnectionFailed(f"{homepage_url} failed: {type(http_error).__name__} {http_error}")

            elapsed_milliseconds = (time.perf_counter() - started_at) * 1000
            logger.debug("{}  http    GET {} returned {} in {:.0f} ms", domain, homepage_url, response.status_code, elapsed_milliseconds)
            return response

        raise HttpConnectionFailed(f"could not connect to {homepage_url} after {self.connection_attempts} attempts: {last_connection_error}")
