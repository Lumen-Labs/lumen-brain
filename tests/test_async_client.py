from __future__ import annotations

import pytest

from lumen_brain import AsyncLumenBrain, AuthenticationError
from tests.helpers import MockAPI, async_client


def test_async_missing_pat() -> None:
    with pytest.raises(AuthenticationError):
        AsyncLumenBrain()


@pytest.mark.asyncio
async def test_async_ingest_context_search_facts() -> None:
    mock = MockAPI()
    mock.route(
        "POST",
        "/ingest/",
        status=202,
        json_body={"message": "accepted", "task_id": "t-async"},
    )
    mock.route(
        "GET",
        "/tasks/t-async",
        json_body={"status": "completed", "task_id": "t-async"},
    )
    mock.route(
        "POST",
        "/retrieve/context",
        json_body={
            "text_context": "Ada is on the design team.",
            "triples": [],
            "validity_unknown_count": 0,
        },
    )
    mock.route(
        "POST",
        "/retrieve/search",
        json_body={"hits": []},
    )
    mock.route(
        "GET",
        "/model/facts/f1",
        json_body={
            "kind": "relationship",
            "fact_id": "f1",
            "name": "joined",
            "verification": {"state": "verified"},
        },
    )
    async with async_client(mock) as brain:
        accepted = await brain.ingest(text="Ada joined design.")
        done = await brain.wait_for_task(accepted.task_id, poll_interval=0)
        ctx = await brain.query("Who is Ada?", as_of="2025-01-01T00:00:00Z")
        hits = await brain.search("Ada", include_validity_unknown=True)
        fact = await brain.get_fact("f1")
    assert accepted.task_id == "t-async"
    assert done.is_terminal
    assert ctx.text_context.startswith("Ada")
    assert hits.hits == []
    assert fact.verification.state == "verified"
    assert mock.calls[0].headers["Authorization"] == "Bearer test-pat"
    assert mock.json_body(mock.calls[2])["as_of"] == "2025-01-01T00:00:00Z"
    assert mock.json_body(mock.calls[3])["include_validity_unknown"] is True


@pytest.mark.asyncio
async def test_async_per_call_override_and_brainpat() -> None:
    mock = MockAPI()
    mock.route(
        "GET",
        "/retrieve/conflicts",
        json_body={"conflicts": [], "count": 0, "total": 0},
    )
    async with async_client(mock, auth_scheme="brainpat") as brain:
        result = await brain.list_conflicts(brain_id="override")
    assert result.total == 0
    assert mock.last.headers["BrainPAT"] == "test-pat"
    assert mock.last.headers["X-Brain-ID"] == "override"
