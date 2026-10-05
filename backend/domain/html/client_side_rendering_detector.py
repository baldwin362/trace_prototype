"""Flags pages that show almost no text without JavaScript, meaning most of the page is built in the browser.

Such pages are under-analyzed by a plain GET, and the report says so. A page is flagged when its visible text,
outside scripts and styles, is shorter than 500 characters.
"""

from bs4 import BeautifulSoup, Comment

MINIMUM_VISIBLE_CHARACTERS = 500
INVISIBLE_PARENT_TAG_NAMES = {"script", "style", "noscript", "template"}


def is_client_side_rendered(document: BeautifulSoup) -> bool:
    visible_text_fragments = [
        text_fragment
        for text_fragment in document.find_all(string=True)
        if not isinstance(text_fragment, Comment) and text_fragment.parent.name not in INVISIBLE_PARENT_TAG_NAMES
    ]
    visible_text = " ".join(" ".join(visible_text_fragments).split())
    return len(visible_text) < MINIMUM_VISIBLE_CHARACTERS
