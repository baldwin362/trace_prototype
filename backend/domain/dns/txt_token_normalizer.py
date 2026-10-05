"""Turns verification TXT records into lookup keys: "docusign=a1b2c3" becomes "docusign".

SPF records are skipped here, they have their own normalizer.
"""

from backend.domain.models.extracted_key import ExtractedKey

TXT_TOKEN_SOURCE = "dns:TXT"
SPF_PREFIX = "v=spf1"


def normalize_txt_tokens(raw_txt_records: list[str]) -> list[ExtractedKey]:
    return [
        ExtractedKey(key=raw_txt_record.split("=", 1)[0].strip().lower(), raw_value=raw_txt_record, source=TXT_TOKEN_SOURCE)
        for raw_txt_record in raw_txt_records
        if not raw_txt_record.lower().startswith(SPF_PREFIX)
    ]
