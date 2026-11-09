from typing import Literal

from pydantic import BaseModel

ProviderName = Literal["crossref", "openalex"]
ProviderStatus = Literal["ok", "not_configured", "rate_limited", "unavailable"]


class ResourceHit(BaseModel):
    id: str
    title: str
    authors: list[str]
    year: int | None
    doi: str | None
    source_url: str
    open_access_url: str | None = None
    providers: list[ProviderName]


class ResourceSearch(BaseModel):
    results: list[ResourceHit]
    providers: dict[ProviderName, ProviderStatus]

