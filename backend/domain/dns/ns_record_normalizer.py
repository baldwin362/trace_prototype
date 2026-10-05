"""Turns raw NS records into lookup keys: "adi.ns.cloudflare.com." becomes "adi.ns.cloudflare.com"."""

from backend.domain.models.extracted_key import ExtractedKey

NS_SOURCE = "dns:NS"


def normalize_ns_records(raw_ns_records: list[str]) -> list[ExtractedKey]:
    return [
        ExtractedKey(key=raw_ns_record.rstrip(".").lower(), raw_value=raw_ns_record, source=NS_SOURCE)
        for raw_ns_record in raw_ns_records
    ]
