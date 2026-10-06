"""Turns raw NS records into lookup keys: "adi.ns.cloudflare.com." becomes "adi.ns.cloudflare.com"."""

from backend.domain.models.extracted_key import ExtractedKey

NS_SOURCE = "dns:NS"


def normalize_ns_records(raw_ns_records: list[str]) -> list[ExtractedKey]:
    """Turns each NS record into the nameserver name, written the same way as in ns.json.

    Args:
        raw_ns_records: the NS records as the resolver gave them, for example ["adi.ns.cloudflare.com."].

    Returns:
        One ExtractedKey per record. The key is the nameserver name, the raw_value is the record unchanged.

    Example:
        normalize_ns_records(["adi.ns.cloudflare.com."])
        # [ExtractedKey(key="adi.ns.cloudflare.com", raw_value="adi.ns.cloudflare.com.", source="dns:NS")]
    """
    return [
        ExtractedKey(key=raw_ns_record.rstrip(".").lower(), raw_value=raw_ns_record, source=NS_SOURCE)
        for raw_ns_record in raw_ns_records
    ]
