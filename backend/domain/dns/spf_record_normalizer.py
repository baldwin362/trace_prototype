"""Pulls the include: values out of SPF records.

"v=spf1 include:_spf.google.com include:sendgrid.net ~all" gives two keys, "_spf.google.com" and "sendgrid.net".
TXT records that are not SPF are ignored here.
"""

from backend.domain.models.extracted_key import ExtractedKey

SPF_SOURCE = "dns:TXT:spf"
SPF_PREFIX = "v=spf1"
INCLUDE_PREFIX = "include:"


def normalize_spf_records(raw_txt_records: list[str]) -> list[ExtractedKey]:
    extracted_keys = []
    for raw_txt_record in raw_txt_records:
        if not raw_txt_record.lower().startswith(SPF_PREFIX):
            continue
        for spf_token in raw_txt_record.split():
            if spf_token.lower().startswith(INCLUDE_PREFIX):
                included_hostname = spf_token[len(INCLUDE_PREFIX):].rstrip(".").lower()
                extracted_keys.append(ExtractedKey(key=included_hostname, raw_value=spf_token, source=SPF_SOURCE))
    return extracted_keys
