from __future__ import annotations

import os
from typing import Any, Optional

from lumen_brain._api import RequestSpec
from lumen_brain._http import merge_headers, raise_for_status
from lumen_brain.config import (
    AuthScheme,
    resolve_base_url,
)
from lumen_brain.errors import AuthenticationError


def _first_env(*names: str) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


class ClientSettings:
    def __init__(
        self,
        pat: Optional[str] = None,
        *,
        api_key: Optional[str] = None,
        brain_id: Optional[str] = None,
        region: Optional[str] = None,
        base_url: Optional[str] = None,
        auth_scheme: AuthScheme = "bearer",
        timeout: float = 30.0,
    ) -> None:
        token = (
            pat
            or api_key
            or _first_env(
                "BRAINPAT_TOKEN",
                "LUMEN_BRAIN_PAT",
                "LUMEN_BRAIN_API_KEY",
            )
        )
        if not token:
            raise AuthenticationError(
                "A BrainAPI PAT is required. Pass pat=... or set BRAINPAT_TOKEN."
            )
        self.pat = token
        self.brain_id = brain_id or _first_env(
            "LUMEN_BRAIN_ID",
            "BRAIN_ID",
            "X_BRAIN_ID",
        )
        env_base = _first_env("LUMEN_BRAIN_BASE_URL", "BRAINAPI_BASE_URL")
        env_region = _first_env("LUMEN_BRAIN_REGION", "BRAINAPI_REGION")
        self.base_url = resolve_base_url(
            base_url=base_url or env_base,
            region=None if (base_url or env_base) else (region or env_region),
        )
        self.auth_scheme = auth_scheme
        self.timeout = timeout

    def headers(
        self,
        *,
        brain_id: Optional[str] = None,
        extra: Optional[dict[str, str]] = None,
        requires_brain: bool = True,
    ) -> dict[str, str]:
        resolved = brain_id if brain_id is not None else self.brain_id
        return merge_headers(
            pat=self.pat,
            auth_scheme=self.auth_scheme,
            brain_id=resolved if requires_brain or resolved else None,
            extra=extra,
        )


def parse_spec_response(spec: RequestSpec, body: Any) -> Any:
    if spec.raw or spec.model is None or body is None:
        return body
    if isinstance(body, spec.model):
        return body
    return spec.model.model_validate(body)


def send_httpx(
    client: Any,
    settings: ClientSettings,
    spec: RequestSpec,
    *,
    brain_id: Optional[str] = None,
) -> Any:
    headers = settings.headers(
        brain_id=brain_id,
        extra=spec.extra_headers or None,
        requires_brain=spec.requires_brain,
    )
    response = client.request(
        spec.method,
        spec.path,
        json=spec.json if spec.files is None else None,
        params=spec.params,
        files=spec.files,
        data=spec.data,
        headers=headers,
    )
    body = raise_for_status(
        response.status_code,
        response.content,
        response.headers.get("content-type", ""),
        response.headers,
        spec.expected_status,
    )
    return parse_spec_response(spec, body)


async def asend_httpx(
    client: Any,
    settings: ClientSettings,
    spec: RequestSpec,
    *,
    brain_id: Optional[str] = None,
) -> Any:
    headers = settings.headers(
        brain_id=brain_id,
        extra=spec.extra_headers or None,
        requires_brain=spec.requires_brain,
    )
    response = await client.request(
        spec.method,
        spec.path,
        json=spec.json if spec.files is None else None,
        params=spec.params,
        files=spec.files,
        data=spec.data,
        headers=headers,
    )
    body = raise_for_status(
        response.status_code,
        response.content,
        response.headers.get("content-type", ""),
        response.headers,
        spec.expected_status,
    )
    return parse_spec_response(spec, body)
