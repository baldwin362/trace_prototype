"""Pulls the name of every cookie the server sets, across the whole redirect chain, e.g. "_shopify_y"."""

import httpx

from backend.domain.models.extracted_key import ExtractedKey

COOKIE_SOURCE = "http:cookie"


def extract_cookie_names(response: httpx.Response) -> list[ExtractedKey]:
    extracted_keys = []
    seen_cookie_names = set()
    for hop_response in [*response.history, response]:
        for set_cookie_value in hop_response.headers.get_list("set-cookie"):
            cookie_name = set_cookie_value.split("=", 1)[0].strip()
            if cookie_name in seen_cookie_names:
                continue
            seen_cookie_names.add(cookie_name)
            extracted_keys.append(ExtractedKey(key=cookie_name, raw_value=f"cookie: {cookie_name}", source=COOKIE_SOURCE))
    return extracted_keys
