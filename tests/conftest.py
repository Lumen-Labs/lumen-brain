from __future__ import annotations

import pytest

ENV_KEYS = (
    "BRAINPAT_TOKEN",
    "LUMEN_BRAIN_PAT",
    "LUMEN_BRAIN_API_KEY",
    "LUMEN_BRAIN_ID",
    "BRAIN_ID",
    "X_BRAIN_ID",
    "LUMEN_BRAIN_BASE_URL",
    "BRAINAPI_BASE_URL",
    "LUMEN_BRAIN_REGION",
    "BRAINAPI_REGION",
)


@pytest.fixture(autouse=True)
def clear_sdk_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
