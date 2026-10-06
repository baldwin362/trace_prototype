"""Turns raw CNAME targets into lookup keys: "shops.myshopify.com." becomes "shops.myshopify.com".

The evidence keeps the subdomain that was queried, e.g. "www.gymshark.com CNAME shops.myshopify.com.",
so a reader can see which part of the domain points at the vendor.
"""

from backend.domain.models.extracted_key import ExtractedKey

CNAME_SOURCE = "dns:CNAME"


def normalize_cname_records(queried_hostname: str, raw_cname_records: list[str]) -> list[ExtractedKey]:
    """Turns each CNAME record into the name it points to, written the same way as in cname.json.

    Args:
        queried_hostname: the subdomain that was looked up, for example "www.gymshark.com".
        raw_cname_records: the CNAME records as the resolver gave them, for example ["shops.myshopify.com."].

    Returns:
        One ExtractedKey per record. The key is the name it points to, the raw_value says which subdomain points where.

    Example:
        normalize_cname_records("www.gymshark.com", ["shops.myshopify.com."])
        # [ExtractedKey(key="shops.myshopify.com", raw_value="www.gymshark.com CNAME shops.myshopify.com.", source="dns:CNAME")]
    """
    return [
        ExtractedKey(
            key=raw_cname_record.rstrip(".").lower(),
            raw_value=f"{queried_hostname} CNAME {raw_cname_record}",
            source=CNAME_SOURCE,
        )
        for raw_cname_record in raw_cname_records
    ]
