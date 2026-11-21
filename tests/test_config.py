from __future__ import annotations

import pytest

from lumen_brain import (
    KNOWN_REGIONS,
    ConfigurationError,
    LumenBrain,
    regional_base_url,
)
from lumen_brain.config import DEFAULT_REGION, normalize_base_url, resolve_base_url
from lumen_brain.models import Brain


def test_known_regions() -> None:
    assert "europe-central2" in KNOWN_REGIONS
    assert "us-east1" in KNOWN_REGIONS
    assert DEFAULT_REGION == "europe-central2"


@pytest.mark.parametrize(
    ("region", "expected"),
    [
        ("europe-central2", "https://system.europe-central2.brainapi.lumen-labs.ai"),
        ("us-east1", "https://system.us-east1.brainapi.lumen-labs.ai"),
        ("US_EAST1", "https://system.us-east1.brainapi.lumen-labs.ai"),
    ],
)
def test_regional_base_url(region: str, expected: str) -> None:
    assert regional_base_url(region) == expected


def test_default_region_url() -> None:
    assert resolve_base_url() == regional_base_url("europe-central2")


def test_explicit_base_url() -> None:
    assert resolve_base_url(base_url="https://brain.example.test/") == "https://brain.example.test"


def test_base_url_and_region_are_exclusive() -> None:
    with pytest.raises(ConfigurationError, match="either base_url or region"):
        resolve_base_url(base_url="https://brain.example.test", region="europe-central2")


def test_invalid_region() -> None:
    with pytest.raises(ConfigurationError):
        regional_base_url("https://evil.example")
    with pytest.raises(ConfigurationError):
        regional_base_url("")


def test_invalid_base_url() -> None:
    with pytest.raises(ConfigurationError):
        resolve_base_url(base_url="not-a-url")


def test_malformed_ipv6_base_url_is_configuration_error() -> None:
    with pytest.raises(ConfigurationError):
        normalize_base_url("http://[::1")
    assert normalize_base_url("http://[::1]") == "http://[::1]"


def test_constructor_rejects_explicit_base_url_and_region() -> None:
    with pytest.raises(ConfigurationError, match="either base_url or region"):
        LumenBrain(
            pat="test-pat",
            base_url="https://brain.example.test",
            region="us-east1",
        )


def test_constructor_rejects_region_when_env_base_url_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LUMEN_BRAIN_BASE_URL", "https://env.example.test")
    with pytest.raises(ConfigurationError, match="either base_url or region"):
        LumenBrain(pat="test-pat", region="us-east1")


def test_brain_pat_omitted_from_repr() -> None:
    brain = Brain(name_key="b1", pat="super-secret")
    assert brain.pat == "super-secret"
    assert "super-secret" not in repr(brain)
