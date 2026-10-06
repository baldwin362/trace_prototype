"""Turns each URL into two lookup keys: its hostname, and its hostname joined to its path.

"https://www.facebook.com/tr?id=1" gives "www.facebook.com" and "www.facebook.com|/tr".
The path key exists because some vendors share a hostname with plain links: only the path tells a tracking pixel from a profile link.
Each hostname is kept once, with the first URL that used it as evidence, so a page with a hundred CMS images gives one key, not a hundred.
"""

from urllib.parse import urlsplit

from backend.domain.models.extracted_key import ExtractedKey

URL_HOSTNAME_SOURCE = "html:url_hostname"
URL_HOSTNAME_PATH_SOURCE = "html:url_hostname_path"


def normalize_url_hostnames(url_keys: list[ExtractedKey]) -> list[ExtractedKey]:
    """Turns each URL into two values: one for hostname.json, one for hostname_path.json.

    Args:
        url_keys: the URLs found by extract_tag_urls.

    Returns:
        Two ExtractedKey per URL. The first key is the hostname, the second is the hostname and path joined by "|".
        Both have the URL as raw_value. A hostname already seen is not repeated.

    Example:
        normalize_url_hostnames(extract_tag_urls(parse_html_document('<img src="https://www.facebook.com/tr?id=1">')))
        # [ExtractedKey(key="www.facebook.com", raw_value="https://www.facebook.com/tr?id=1", source="html:url_hostname"),
        #  ExtractedKey(key="www.facebook.com|/tr", raw_value="https://www.facebook.com/tr?id=1", source="html:url_hostname_path")]
    """
    extracted_keys = []
    seen_keys = set()
    for url_key in url_keys:
        try:
            split_url = urlsplit(url_key.key)
            hostname = split_url.hostname
        except ValueError:
            continue
        if not hostname:
            continue
        for lookup_key, source in [(hostname, URL_HOSTNAME_SOURCE), (f"{hostname}|{split_url.path}", URL_HOSTNAME_PATH_SOURCE)]:
            if lookup_key in seen_keys:
                continue
            seen_keys.add(lookup_key)
            extracted_keys.append(ExtractedKey(key=lookup_key, raw_value=url_key.raw_value, source=source))
    return extracted_keys
