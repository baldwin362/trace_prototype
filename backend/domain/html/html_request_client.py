"""Downloads a domain's homepage with a plain GET and returns the raw HTML. No browser, so no JavaScript is executed."""

import time

import httpx
from loguru import logger

from backend.domain.errors.html_errors import HtmlFetchFailed

BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"


class HtmlRequestClient:
    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout_seconds = timeout_seconds

    async def fetch_homepage_html(self, domain: str) -> str:
        homepage_url = f"https://{domain}/"
        logger.debug("{}  html    GET {} sent", domain, homepage_url)
        started_at = time.perf_counter()
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=self.timeout_seconds,
                headers={"User-Agent": BROWSER_USER_AGENT},
            ) as http_client:
                response = await http_client.get(homepage_url)
        except httpx.HTTPError as http_error:
            raise HtmlFetchFailed(f"could not download {homepage_url}: {type(http_error).__name__} {http_error}")

        elapsed_milliseconds = (time.perf_counter() - started_at) * 1000
        logger.debug("{}  html    GET {} returned {} ({} bytes) in {:.0f} ms", domain, homepage_url, response.status_code, len(response.content), elapsed_milliseconds)
        return response.text
