"""Tests that pages with little visible text are flagged, and that script text is not counted as visible."""

from bs4 import BeautifulSoup

from backend.domain.html.client_side_rendering_detector import is_client_side_rendered


def test_empty_shell_page_is_flagged():
    document = BeautifulSoup('<div id="root"></div><script>' + "x" * 5000 + "</script>", "lxml")

    assert is_client_side_rendered(document)


def test_page_with_real_text_is_not_flagged():
    document = BeautifulSoup("<p>" + "Real visible content. " * 50 + "</p>", "lxml")

    assert not is_client_side_rendered(document)
