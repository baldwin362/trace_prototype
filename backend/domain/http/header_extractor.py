"""Turns the headers of every response in the redirect chain into lookup keys.

Each header gives two keys: its lowercased name ("cf-ray"), and its name with its lowercased value ("server|cloudflare").
The evidence is the header exactly as received, e.g. "powered-by: Shopify". Set-Cookie is left to the cookie extractor.
"""

import httpx

from backend.domain.models.extracted_key import ExtractedKey

HEADER_NAME_SOURCE = "http:header_name"
HEADER_VALUE_SOURCE = "http:header_value"


def extract_headers(response: httpx.Response) -> list[ExtractedKey]:
    extracted_keys = []
    seen_raw_headers = set()
    for hop_response in [*response.history, response]:
        for header_name, header_value in hop_response.headers.multi_items():
            raw_header = f"{header_name}: {header_value}"
            lowercased_header_name = header_name.lower()
            if lowercased_header_name == "set-cookie" or raw_header in seen_raw_headers:
                continue
            seen_raw_headers.add(raw_header)
            extracted_keys.append(ExtractedKey(key=lowercased_header_name, raw_value=raw_header, source=HEADER_NAME_SOURCE))
            extracted_keys.append(
                ExtractedKey(key=f"{lowercased_header_name}|{header_value.lower()}", raw_value=raw_header, source=HEADER_VALUE_SOURCE)
            )
    return extracted_keys
