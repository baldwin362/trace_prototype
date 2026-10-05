"""Parses raw HTML into a BeautifulSoup tree that the extractors can search."""

from bs4 import BeautifulSoup
from bs4.exceptions import ParserRejectedMarkup

from backend.domain.errors.html_errors import HtmlParseFailed


def parse_html_document(raw_html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(raw_html, "lxml")
    except ParserRejectedMarkup as parser_error:
        raise HtmlParseFailed(f"the page could not be parsed: {parser_error}")
