from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional

from lumen_brain.config import REQUEST_ID_HEADER


class LumenBrainError(Exception):
    """Base error for the Lumen Brain SDK."""


class AuthenticationError(LumenBrainError):
    pass


class BrainAPIError(LumenBrainError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        code: Optional[str] = None,
        detail: Any = None,
        resolution: Optional[str] = None,
        request_id: Optional[str] = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.detail = detail
        self.resolution = resolution
        self.request_id = request_id
        self.body = body


class TaskTimeoutError(LumenBrainError):
    def __init__(self, task_id: str, last_status: Optional[str] = None) -> None:
        super().__init__(f"Timed out waiting for task {task_id!r}")
        self.task_id = task_id
        self.last_status = last_status


def error_from_response(
    status_code: int,
    body: Any,
    headers: Optional[Mapping[str, str]] = None,
) -> BrainAPIError:
    request_id = None
    if headers:
        request_id = headers.get(REQUEST_ID_HEADER) or headers.get("x-request-id")
    detail: Any = body
    code: Optional[str] = None
    message: Optional[str] = None
    resolution: Optional[str] = None
    if isinstance(body, dict):
        detail = body.get("detail", body)
        error = body.get("error")
        if isinstance(error, dict):
            code = error.get("code")
            message = error.get("message")
            resolution = error.get("resolution")
            request_id = error.get("request_id") or request_id
        elif isinstance(detail, str):
            message = detail
    if not message:
        if isinstance(detail, str):
            message = detail
        else:
            message = f"BrainAPI request failed with HTTP {status_code}"
    return BrainAPIError(
        message,
        status_code=status_code,
        code=code,
        detail=detail,
        resolution=resolution,
        request_id=request_id,
        body=body,
    )
