"""Joins the text of every <script> written directly in the page (no src), where tracking snippets like fbq('init') live."""

from bs4 import BeautifulSoup

from backend.domain.models.extracted_key import ExtractedKey

INLINE_SCRIPT_SOURCE = "html:inline"


def extract_inline_scripts(document: BeautifulSoup) -> list[ExtractedKey]:
    inline_script_texts = [script_element.get_text() for script_element in document.find_all("script") if not script_element.has_attr("src")]
    all_inline_script_text = "\n".join(inline_script_texts)
    if not all_inline_script_text.strip():
        return []
    return [ExtractedKey(key=all_inline_script_text, raw_value=all_inline_script_text, source=INLINE_SCRIPT_SOURCE)]
