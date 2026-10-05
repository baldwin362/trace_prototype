"""Turns raw CNAME targets into lookup keys: "shops.myshopify.com." becomes "shops.myshopify.com".

The evidence keeps the subdomain that was queried, e.g. "www.gymshark.com CNAME shops.myshopify.com.",
so a reader can see which part of the domain points at the vendor.
"""

from backend.domain.models.extracted_key import ExtractedKey

CNAME_SOURCE = "dns:CNAME"


def normalize_cname_records(queried_hostname: str, raw_cname_records: list[str]) -> list[ExtractedKey]:
    return [
        ExtractedKey(
            key=raw_cname_record.rstrip(".").lower(),
            raw_value=f"{queried_hostname} CNAME {raw_cname_record}",
            source=CNAME_SOURCE,
        )
        for raw_cname_record in raw_cname_records
    ]
