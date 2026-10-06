"""Pulls the include: values out of SPF records.

"v=spf1 include:_spf.google.com include:sendgrid.net ~all" gives two keys, "_spf.google.com" and "sendgrid.net".
TXT records that are not SPF are ignored here.
"""

from backend.domain.models.extracted_key import ExtractedKey

SPF_SOURCE = "dns:TXT:spf"
SPF_PREFIX = "v=spf1"
INCLUDE_PREFIX = "include:"


def normalize_spf_records(raw_txt_records: list[str]) -> list[ExtractedKey]:
    """Pulls out every "include:" of the SPF record, written the same way as in txt_spf.json.

    Args:
        raw_txt_records: all the TXT records of the domain. Only the one starting with "v=spf1" is read.

    Returns:
        One ExtractedKey per "include:". The key is the included name, the raw_value is the "include:..." part unchanged.

    Example:
        normalize_spf_records(["v=spf1 include:_spf.google.com include:sendgrid.net ~all", "MS=ms54108504"])
        # [ExtractedKey(key="_spf.google.com", raw_value="include:_spf.google.com", source="dns:TXT:spf"),
        #  ExtractedKey(key="sendgrid.net", raw_value="include:sendgrid.net", source="dns:TXT:spf")]
    """
    extracted_keys = []
    for raw_txt_record in raw_txt_records:
        if not raw_txt_record.lower().startswith(SPF_PREFIX):
            continue
        for spf_token in raw_txt_record.split():
            if spf_token.lower().startswith(INCLUDE_PREFIX):
                included_hostname = spf_token[len(INCLUDE_PREFIX):].rstrip(".").lower()
                extracted_keys.append(ExtractedKey(key=included_hostname, raw_value=spf_token, source=SPF_SOURCE))
    return extracted_keys
