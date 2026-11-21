from __future__ import annotations

from typing import FrozenSet, Literal, Optional
from urllib.parse import urlparse

AuthScheme = Literal["bearer", "brainpat"]

KNOWN_REGIONS: FrozenSet[str] = frozenset({"europe-central2", "us-east1"})
DEFAULT_REGION = "europe-central2"
REGIONAL_HOST_TEMPLATE = "https://system.{region}.brainapi.lumen-labs.ai"

BRAIN_ID_HEADER = "X-Brain-ID"
BRAINPAT_HEADER = "BrainPAT"
REQUEST_ID_HEADER = "X-Request-ID"

TERMINAL_TASK_STATUSES = frozenset(
    {
        "completed",
        "complete",
        "failed",
        "error",
        "cancelled",
        "canceled",
        "rollback_failed",
        "success",
        "partial_failed",
    }
)


class ConfigurationError(ValueError):
    pass


def normalize_region(region: str) -> str:
    value = region.strip().lower().replace("_", "-")
    if not value:
        raise ConfigurationError("region must be a non-empty string")
    if (
        "/" in value
        or "://" in value
        or "." in value
        and not value.replace("-", "").replace(".", "").isalnum()
    ):
        raise ConfigurationError(
            "region should be a short location id such as 'us-east1' or 'europe-central2'"
        )
    if not all(part.isalnum() for part in value.split("-")):
        raise ConfigurationError(
            "region should be a short location id such as 'us-east1' or 'europe-central2'"
        )
    return value


def regional_base_url(region: str) -> str:
    """Return the managed BrainAPI host for a GCP-style region id."""
    return REGIONAL_HOST_TEMPLATE.format(region=normalize_region(region))


def normalize_base_url(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    if not value:
        raise ConfigurationError("base_url must be a non-empty URL")
    try:
        parsed = urlparse(value)
    except ValueError as exc:
        raise ConfigurationError("base_url must be an absolute http(s) URL") from exc
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigurationError("base_url must be an absolute http(s) URL")
    return value


def resolve_base_url(
    *,
    base_url: Optional[str] = None,
    region: Optional[str] = None,
) -> str:
    if base_url and region:
        raise ConfigurationError("pass either base_url or region, not both")
    if base_url:
        return normalize_base_url(base_url)
    return regional_base_url(region or DEFAULT_REGION)
