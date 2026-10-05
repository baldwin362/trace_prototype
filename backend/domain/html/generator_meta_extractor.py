"""Reads the <meta name="generator"> tag, where site builders and CMSs write their own name and often their version."""

from bs4 import BeautifulSoup

from backend.domain.models.extracted_key import ExtractedKey

GENERATOR_SOURCE = "html:generator"


def extract_generator_meta(document: BeautifulSoup) -> list[ExtractedKey]:
    return [
        ExtractedKey(key=meta_element["content"].strip().lower(), raw_value=meta_element["content"], source=GENERATOR_SOURCE)
        for meta_element in document.find_all("meta", attrs={"name": "generator", "content": True})
    ]
