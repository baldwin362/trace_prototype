"""Reads the <meta name="generator"> tag, where site builders and CMSs write their own name and often their version."""

from bs4 import BeautifulSoup

from backend.domain.models.extracted_key import ExtractedKey

GENERATOR_SOURCE = "html:generator"


def extract_generator_meta(document: BeautifulSoup) -> list[ExtractedKey]:
    """Returns the content of the <meta name="generator"> tag, written the same way as in generator.json.

    Args:
        document: the parsed page.

    Returns:
        One ExtractedKey per generator tag. The key is the content in lowercase, the raw_value is the content unchanged.
        An empty list if the page has no generator tag.

    Example:
        extract_generator_meta(parse_html_document('<meta name="generator" content="WordPress 6.4.2">'))
        # [ExtractedKey(key="wordpress 6.4.2", raw_value="WordPress 6.4.2", source="html:generator")]
    """
    return [
        ExtractedKey(key=meta_element["content"].strip().lower(), raw_value=meta_element["content"], source=GENERATOR_SOURCE)
        for meta_element in document.find_all("meta", attrs={"name": "generator", "content": True})
    ]
