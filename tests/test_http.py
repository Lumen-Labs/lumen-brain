from __future__ import annotations

import pytest

from lumen_brain import AuthenticationError, BrainAPIError
from lumen_brain._http import auth_headers, decode_body, merge_headers, raise_for_status
from lumen_brain.errors import error_from_response


def test_bearer_auth_headers() -> None:
    headers = auth_headers("secret-pat", "bearer")
    assert headers == {"Authorization": "Bearer secret-pat"}


def test_brainpat_auth_headers() -> None:
    headers = auth_headers("secret-pat", "brainpat")
    assert headers == {"BrainPAT": "secret-pat"}


def test_unknown_auth_scheme() -> None:
    with pytest.raises(AuthenticationError, match="Unknown auth_scheme"):
        auth_headers("secret-pat", "basic")  # type: ignore[arg-type]


def test_merge_headers_adds_brain_id() -> None:
    headers = merge_headers(
        pat="secret-pat",
        auth_scheme="bearer",
        brain_id="brain-9",
        extra={"Task-Identifier": "job-1"},
    )
    assert headers["Authorization"] == "Bearer secret-pat"
    assert headers["X-Brain-ID"] == "brain-9"
    assert headers["Task-Identifier"] == "job-1"


def test_error_envelope() -> None:
    err = error_from_response(
        401,
        {
            "detail": "Invalid token",
            "error": {
                "code": "unauthorized",
                "message": "Invalid token",
                "resolution": "Provide a valid PAT",
                "request_id": "req-1",
            },
        },
        {"X-Request-ID": "ignored"},
    )
    assert isinstance(err, BrainAPIError)
    assert err.status_code == 401
    assert err.code == "unauthorized"
    assert err.resolution == "Provide a valid PAT"
    assert err.request_id == "req-1"
    assert "Invalid token" in str(err)


def test_decode_body_ignores_content_type_case() -> None:
    body = decode_body(
        b'{"message":"accepted","task_id":"t1"}',
        "Application/JSON; charset=utf-8",
    )
    assert body == {"message": "accepted", "task_id": "t1"}


def test_decode_body_without_content_type() -> None:
    body = decode_body(b'{"ok": true}', "")
    assert body == {"ok": True}


def test_raise_for_status_accepts_expected() -> None:
    body = raise_for_status(
        202,
        b'{"message":"accepted","task_id":"t1"}',
        "application/json",
        {},
        (202,),
    )
    assert body["task_id"] == "t1"


def test_raise_for_status_unexpected() -> None:
    with pytest.raises(BrainAPIError) as exc:
        raise_for_status(
            500,
            b'{"detail":"boom"}',
            "application/json",
            {"X-Request-ID": "abc"},
            (200,),
        )
    assert exc.value.status_code == 500
    assert exc.value.request_id == "abc"
