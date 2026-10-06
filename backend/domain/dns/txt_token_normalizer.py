"""Turns verification TXT records into lookup keys: "docusign=a1b2c3" becomes "docusign".

SPF records are skipped here, they have their own normalizer.
"""

from backend.domain.models.extracted_key import ExtractedKey

TXT_TOKEN_SOURCE = "dns:TXT"
SPF_PREFIX = "v=spf1"


def normalize_txt_tokens(raw_txt_records: list[str]) -> list[ExtractedKey]:
    """Turns each verification TXT record into its name (the part before "="), written the same way as in txt_token.json.

    Args:
        raw_txt_records: all the TXT records of the domain. The SPF record is skipped.

    Returns:
        One ExtractedKey per record. The key is the lowercased name, the raw_value is the record unchanged.

    Example:
        normalize_txt_tokens(["MS=ms54108504", "v=spf1 include:_spf.google.com ~all"])
        # [ExtractedKey(key="ms", raw_value="MS=ms54108504", source="dns:TXT")]
    """
    return [
        ExtractedKey(key=raw_txt_record.split("=", 1)[0].strip().lower(), raw_value=raw_txt_record, source=TXT_TOKEN_SOURCE)
        for raw_txt_record in raw_txt_records
        if not raw_txt_record.lower().startswith(SPF_PREFIX)
    ]
