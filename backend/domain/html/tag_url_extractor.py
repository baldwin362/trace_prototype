"""Collects the absolute URLs a page loads through script, link, img and iframe tags.

Relative URLs point at the site itself, so they are skipped. A protocol-relative URL ("//cdn.x.com/a.js") gets "https:" in its key,
while the evidence keeps the URL exactly as written in the page.
"""

from bs4 import BeautifulSoup

from backend.domain.models.extracted_key import ExtractedKey

TAG_URL_SOURCE = "html:tag_url"
URL_ATTRIBUTE_BY_TAG_NAME = {"script": "src", "link": "href", "img": "src", "iframe": "src"}


def extract_tag_urls(document: BeautifulSoup) -> list[ExtractedKey]:
    extracted_keys = []
    seen_urls = set()
    for tag_name, attribute_name in URL_ATTRIBUTE_BY_TAG_NAME.items():
        for element in document.find_all(tag_name, attrs={attribute_name: True}):
            raw_url = element[attribute_name].strip()
            absolute_url = f"https:{raw_url}" if raw_url.startswith("//") else raw_url
            if not absolute_url.startswith(("http://", "https://")) or absolute_url in seen_urls:
                continue
            seen_urls.add(absolute_url)
            extracted_keys.append(ExtractedKey(key=absolute_url, raw_value=raw_url, source=TAG_URL_SOURCE))
    return extracted_keys
