"""Pulls the name of every cookie the server sets, across the whole redirect chain, e.g. "_shopify_y"."""

import httpx

from backend.domain.models.extracted_key import ExtractedKey

COOKIE_SOURCE = "http:cookie"


def extract_cookie_names(response: httpx.Response) -> list[ExtractedKey]:
    """Returns the name of every cookie the site sets, written the same way as in cookie_name.json.

    Args:
        response: the homepage response, including the redirects it went through.

    Returns:
        One ExtractedKey per cookie name. The key is the cookie name, the raw_value is "cookie: <name>".

    Example:
        A response with the header "set-cookie: cart_currency=USD; path=/" gives:
        # [ExtractedKey(key="cart_currency", raw_value="cookie: cart_currency", source="http:cookie")]
    """
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
