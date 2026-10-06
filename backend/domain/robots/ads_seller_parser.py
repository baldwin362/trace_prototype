"""Pulls the ad seller domain out of each line of an ads.txt file.

"google.com, pub-123, DIRECT, f08c47fec0942fa0" gives "google.com". Each seller is kept once, at its first line.
Lines with fewer than three comma-separated fields are not ads.txt records and are skipped.
"""

from backend.domain.models.extracted_key import ExtractedKey

ADS_SELLER_SOURCE = "robots:ads_seller"
MINIMUM_FIELD_COUNT = 3


def parse_ads_sellers(ads_text: str) -> list[ExtractedKey]:
    """Returns the ad seller of each line of an ads.txt, written the same way as in ads_seller.json.

    Args:
        ads_text: the content of the ads.txt file.

    Returns:
        One ExtractedKey per seller. The key is the seller's domain (the first word of the line),
        the raw_value is the line unchanged. A seller already seen is not repeated.

    Example:
        parse_ads_sellers("google.com, pub-123, DIRECT, f08c47fec0942fa0")
        # [ExtractedKey(key="google.com", raw_value="google.com, pub-123, DIRECT, f08c47fec0942fa0", source="robots:ads_seller")]
    """
    extracted_keys = []
    seen_seller_domains = set()
    for ads_line in ads_text.splitlines():
        record_fields = [record_field.strip() for record_field in ads_line.split("#")[0].split(",")]
        if len(record_fields) < MINIMUM_FIELD_COUNT:
            continue
        seller_domain = record_fields[0].lower()
        if seller_domain in seen_seller_domains:
            continue
        seen_seller_domains.add(seller_domain)
        extracted_keys.append(ExtractedKey(key=seller_domain, raw_value=ads_line.strip(), source=ADS_SELLER_SOURCE))
    return extracted_keys
