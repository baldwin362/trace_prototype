"""Parses raw HTML into a BeautifulSoup tree that the extractors can search."""

from bs4 import BeautifulSoup
from bs4.exceptions import ParserRejectedMarkup

from backend.domain.errors.html_errors import HtmlParseFailed


def parse_html_document(raw_html: str) -> BeautifulSoup:
    """Turns the HTML text into a BeautifulSoup document, so the extractors can search its tags.

    Args:
        raw_html: the HTML of the page, for example '<script src="https://cdn.shopify.com/app.js"></script>'.

    Returns:
        The BeautifulSoup document.

    Raises:
        HtmlParseFailed: the HTML could not be read.

    Example:
        document = parse_html_document('<script src="https://cdn.shopify.com/app.js"></script>')
        document.find("script")["src"]   # "https://cdn.shopify.com/app.js"
    """
    try:
        return BeautifulSoup(raw_html, "lxml")
    except ParserRejectedMarkup as parser_error:
        raise HtmlParseFailed(f"the page could not be parsed: {parser_error}")
