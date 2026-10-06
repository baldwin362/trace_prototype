"""Turns raw MX records into lookup keys: "10 aspmx.l.google.com." becomes "aspmx.l.google.com"."""

from backend.domain.models.extracted_key import ExtractedKey

MX_SOURCE = "dns:MX"


def normalize_mx_records(raw_mx_records: list[str]) -> list[ExtractedKey]:
    """Turns each MX record into the mail server name, written the same way as in mx.json.

    Args:
        raw_mx_records: the MX records as the resolver gave them, for example ["10 aspmx.l.google.com."].

    Returns:
        One ExtractedKey per record. The key is the mail server name, the raw_value is the record unchanged.

    Example:
        normalize_mx_records(["10 aspmx.l.google.com."])
        # [ExtractedKey(key="aspmx.l.google.com", raw_value="10 aspmx.l.google.com.", source="dns:MX")]
    """
    return [
        ExtractedKey(key=raw_mx_record.split()[-1].rstrip(".").lower(), raw_value=raw_mx_record, source=MX_SOURCE)
        for raw_mx_record in raw_mx_records
    ]
