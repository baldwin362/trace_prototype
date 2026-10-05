"""A lookup key pulled out of fetched data, together with the raw text it came from and where it was found."""

from pydantic import BaseModel


class ExtractedKey(BaseModel):
    key: str
    raw_value: str
    source: str
