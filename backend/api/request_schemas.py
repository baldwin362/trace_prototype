"""The shape of the JSON bodies the API accepts."""

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    domain: str = Field(min_length=3, max_length=253, pattern=r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", examples=["gymshark.com"])
