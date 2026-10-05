"""Loads the list of subdomains (www, help, status...) whose CNAME records are worth checking."""

from pathlib import Path

from backend.domain.rules.mapping_loader import load_string_list

SUBDOMAINS_FILE = Path(__file__).parent / "mappings" / "subdomains.json"


def load_subdomain_candidates() -> list[str]:
    return load_string_list(SUBDOMAINS_FILE)
