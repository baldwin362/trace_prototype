"""Pulls the hostname of every URL the homepage request went through, from the first hop to the final page."""

import httpx

from backend.domain.models.extracted_key import ExtractedKey

REDIRECT_SOURCE = "http:redirect"


def extract_redirect_hostnames(response: httpx.Response) -> list[ExtractedKey]:
    """Returns the hostname of every page the homepage request went through, written the same way as in redirect_hostname.json.

    Args:
        response: the homepage response, including the redirects it went through.

    Returns:
        One ExtractedKey per page, in order. The key is the hostname, the raw_value is "redirect: <full url>".

    Example:
        gymshark.com redirects to us.checkout.gymshark.com, which gives:
        # [ExtractedKey(key="gymshark.com", raw_value="redirect: https://gymshark.com/", source="http:redirect"),
        #  ExtractedKey(key="us.checkout.gymshark.com", raw_value="redirect: https://us.checkout.gymshark.com/", source="http:redirect")]
    """
    extracted_keys = []
    seen_urls = set()
    for hop_response in [*response.history, response]:
        hop_url = str(hop_response.url)
        if hop_url in seen_urls:
            continue
        seen_urls.add(hop_url)
        extracted_keys.append(ExtractedKey(key=hop_response.url.host.lower(), raw_value=f"redirect: {hop_url}", source=REDIRECT_SOURCE))
    return extracted_keys
