from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Optional

from lumen_brain.config import (
    BRAIN_ID_HEADER,
    BRAINPAT_HEADER,
    REQUEST_ID_HEADER,
    AuthScheme,
)
from lumen_brain.errors import AuthenticationError, error_from_response


def drop_none(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def auth_headers(pat: str, scheme: AuthScheme) -> dict[str, str]:
    if not pat:
        raise AuthenticationError("A BrainAPI personal access token is required")
    if scheme == "brainpat":
        return {BRAINPAT_HEADER: pat}
    if scheme == "bearer":
        return {"Authorization": f"Bearer {pat}"}
    raise AuthenticationError(f"Unknown auth_scheme {scheme!r}")


def merge_headers(
    *,
    pat: str,
    auth_scheme: AuthScheme,
    brain_id: Optional[str] = None,
    extra: Optional[Mapping[str, str]] = None,
) -> dict[str, str]:
    headers = auth_headers(pat, auth_scheme)
    if brain_id:
        headers[BRAIN_ID_HEADER] = brain_id
    if extra:
        headers.update({key: value for key, value in extra.items() if value is not None})
    return headers


def decode_body(content: bytes, content_type: str) -> Any:
    if not content:
        return None
    media_type = content_type.split(";", 1)[0].strip().lower()
    if "json" in media_type or not media_type:
        try:
            return json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return content.decode("utf-8", errors="replace")
    return content.decode("utf-8", errors="replace")


def raise_for_status(
    status_code: int,
    content: bytes,
    content_type: str,
    headers: Mapping[str, str],
    expected: tuple[int, ...],
) -> Any:
    body = decode_body(content, content_type)
    if status_code in expected:
        return body
    raise error_from_response(status_code, body, headers)


def request_id_from_headers(headers: Mapping[str, str]) -> Optional[str]:
    return headers.get(REQUEST_ID_HEADER) or headers.get("x-request-id")


__all__ = [
    "auth_headers",
    "decode_body",
    "drop_none",
    "merge_headers",
    "raise_for_status",
    "request_id_from_headers",
]
