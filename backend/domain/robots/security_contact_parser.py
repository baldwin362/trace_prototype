"""Pulls the hostname out of each Contact line of a security.txt file.

"Contact: https://hackerone.com/acme" gives "hackerone.com", and "Contact: mailto:security@acme.com" gives "acme.com".
A bug bounty platform shows up here.
"""

from urllib.parse import urlsplit

from backend.domain.models.extracted_key import ExtractedKey

SECURITY_CONTACT_SOURCE = "robots:security_contact"
MAILTO_PREFIX = "mailto:"


def parse_security_contacts(security_text: str) -> list[ExtractedKey]:
    extracted_keys = []
    for security_line in security_text.splitlines():
        field_name, separator, contact_value = security_line.partition(":")
        if not separator or field_name.strip().lower() != "contact":
            continue
        contact_value = contact_value.strip()
        if contact_value.lower().startswith(MAILTO_PREFIX):
            contact_hostname = contact_value.rsplit("@", 1)[-1]
        else:
            contact_hostname = urlsplit(contact_value).hostname or ""
        if contact_hostname:
            extracted_keys.append(ExtractedKey(key=contact_hostname.lower(), raw_value=security_line.strip(), source=SECURITY_CONTACT_SOURCE))
    return extracted_keys
