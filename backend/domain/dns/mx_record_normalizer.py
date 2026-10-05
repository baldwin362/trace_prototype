"""Turns raw MX records into lookup keys: "10 aspmx.l.google.com." becomes "aspmx.l.google.com"."""

from backend.domain.models.extracted_key import ExtractedKey

MX_SOURCE = "dns:MX"


def normalize_mx_records(raw_mx_records: list[str]) -> list[ExtractedKey]:
    return [
        ExtractedKey(key=raw_mx_record.split()[-1].rstrip(".").lower(), raw_value=raw_mx_record, source=MX_SOURCE)
        for raw_mx_record in raw_mx_records
    ]
