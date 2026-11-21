from __future__ import annotations

import json
from typing import Any, Optional

import httpx

from lumen_brain import AsyncLumenBrain, LumenBrain


class MockAPI:
    def __init__(self) -> None:
        self.calls: list[httpx.Request] = []
        self._routes: dict[tuple[str, str], dict[str, Any]] = {}

    def route(
        self,
        method: str,
        path: str,
        *,
        status: int = 200,
        json_body: Any = None,
        sequence: Optional[list[dict[str, Any]]] = None,
        text: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        self._routes[(method.upper(), path)] = {
            "status": status,
            "json": json_body,
            "text": text,
            "headers": headers or {},
            "sequence": sequence,
            "index": 0,
        }

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        spec = self._routes.get((request.method, request.url.path))
        if spec is None:
            return httpx.Response(
                404,
                json={
                    "detail": f"unmocked {request.method} {request.url.path}",
                    "error": {
                        "code": "not_found",
                        "message": f"unmocked {request.method} {request.url.path}",
                        "resolution": "Add a mock route",
                        "request_id": "test",
                    },
                },
            )
        if spec["sequence"]:
            item = spec["sequence"][min(spec["index"], len(spec["sequence"]) - 1)]
            spec["index"] += 1
            return httpx.Response(
                item.get("status", 200),
                json=item.get("json"),
                text=item.get("text"),
                headers=item.get("headers", {}),
            )
        if spec["text"] is not None:
            return httpx.Response(spec["status"], text=spec["text"], headers=spec["headers"])
        return httpx.Response(spec["status"], json=spec["json"], headers=spec["headers"])

    @property
    def last(self) -> httpx.Request:
        return self.calls[-1]

    def json_body(self, request: Optional[httpx.Request] = None) -> Any:
        req = request or self.last
        if not req.content:
            return None
        return json.loads(req.content.decode("utf-8"))


def sync_client(mock: MockAPI, **kwargs: Any) -> LumenBrain:
    transport = httpx.MockTransport(mock)
    client = httpx.Client(
        transport=transport,
        base_url=kwargs.pop("base_url", "https://system.europe-central2.brainapi.lumen-labs.ai"),
    )
    return LumenBrain(
        pat=kwargs.pop("pat", "test-pat"),
        brain_id=kwargs.pop("brain_id", "brain-1"),
        client=client,
        **kwargs,
    )


def async_client(mock: MockAPI, **kwargs: Any) -> AsyncLumenBrain:
    transport = httpx.MockTransport(mock)
    client = httpx.AsyncClient(
        transport=transport,
        base_url=kwargs.pop("base_url", "https://system.europe-central2.brainapi.lumen-labs.ai"),
    )
    return AsyncLumenBrain(
        pat=kwargs.pop("pat", "test-pat"),
        brain_id=kwargs.pop("brain_id", "brain-1"),
        client=client,
        **kwargs,
    )
