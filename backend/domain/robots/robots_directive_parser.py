"""Pulls the paths out of the Disallow and Allow lines of a robots.txt file, e.g. "Disallow: /checkouts/" gives "/checkouts/".

Platforms ship their own default robots.txt, so these paths often reveal the platform behind a site.
"""

from backend.domain.models.extracted_key import ExtractedKey

DISALLOW_SOURCE = "robots:disallow"
ALLOW_SOURCE = "robots:allow"
SOURCE_BY_DIRECTIVE_NAME = {"disallow": DISALLOW_SOURCE, "allow": ALLOW_SOURCE}


def parse_robots_directives(robots_text: str) -> list[ExtractedKey]:
    extracted_keys = []
    seen_paths = set()
    for robots_line in robots_text.splitlines():
        directive_name, separator, directive_value = robots_line.partition(":")
        source = SOURCE_BY_DIRECTIVE_NAME.get(directive_name.strip().lower())
        path = directive_value.split("#")[0].strip()
        if not separator or source is None or not path or path in seen_paths:
            continue
        seen_paths.add(path)
        extracted_keys.append(ExtractedKey(key=path, raw_value=robots_line.strip(), source=source))
    return extracted_keys
