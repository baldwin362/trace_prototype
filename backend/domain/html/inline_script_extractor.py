"""Joins the text of every <script> written directly in the page (no src), where tracking snippets like fbq('init') live."""

from bs4 import BeautifulSoup

from backend.domain.models.extracted_key import ExtractedKey

INLINE_SCRIPT_SOURCE = "html:inline"


def extract_inline_scripts(document: BeautifulSoup) -> list[ExtractedKey]:
    """Joins the code of every <script> written inside the page into one text, to be searched with inline_fingerprints.json.

    Args:
        document: the parsed page.

    Returns:
        One ExtractedKey holding all the inline script code. Scripts loaded from a URL (with src) are left out.
        An empty list if the page has no inline script.

    Example:
        extract_inline_scripts(parse_html_document("<script>fbq('init', '1');</script><script src='https://a.com/x.js'></script>"))
        # [ExtractedKey(key="fbq('init', '1');", raw_value="fbq('init', '1');", source="html:inline")]
    """
    inline_script_texts = [script_element.get_text() for script_element in document.find_all("script") if not script_element.has_attr("src")]
    all_inline_script_text = "\n".join(inline_script_texts)
    if not all_inline_script_text.strip():
        return []
    return [ExtractedKey(key=all_inline_script_text, raw_value=all_inline_script_text, source=INLINE_SCRIPT_SOURCE)]
