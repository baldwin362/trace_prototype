"""Loads the list of subdomains (www, help, status...) whose CNAME records are worth checking."""

from pathlib import Path

from backend.domain.rules.mapping_loader import load_string_list

SUBDOMAINS_FILE = Path(__file__).parent / "mappings" / "subdomains.json"


def load_subdomain_candidates() -> list[str]:
    """Returns the subdomains whose CNAME records the DNS engine checks, read from subdomains.json.

    Returns:
        The list of subdomains, for example ["www", "help", "support", ...].

    Example:
        load_subdomain_candidates()   # ["www", "help", "support", "careers", ...]
    """
    return load_string_list(SUBDOMAINS_FILE)
