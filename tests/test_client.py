from __future__ import annotations

import pytest

from lumen_brain import (
    AuthenticationError,
    BrainAPIError,
    LumenBrain,
    TaskTimeoutError,
    regional_base_url,
)
from tests.helpers import MockAPI, sync_client


def test_missing_pat() -> None:
    with pytest.raises(AuthenticationError, match="PAT"):
        LumenBrain()


def test_default_region_and_bearer_headers() -> None:
    mock = MockAPI()
    mock.route("GET", "/health", json_body={"status": "healthy", "service": "brainapi"})
    with sync_client(mock) as brain:
        assert brain.base_url == regional_base_url("europe-central2")
        health = brain.health()
    assert health.status == "healthy"
    assert mock.last.headers["Authorization"] == "Bearer test-pat"
    assert mock.last.headers["X-Brain-ID"] == "brain-1"
    assert "BrainPAT" not in mock.last.headers


def test_brainpat_scheme_and_per_call_brain_id() -> None:
    mock = MockAPI()
    mock.route(
        "POST",
        "/retrieve/context",
        json_body={"text_context": "Ada is a designer.", "triples": []},
    )
    with sync_client(mock, auth_scheme="brainpat") as brain:
        ctx = brain.context("Who is Ada?", brain_id="other-brain", as_of="2025-01-01T00:00:00Z")
    assert ctx.text_context == "Ada is a designer."
    assert mock.last.headers["BrainPAT"] == "test-pat"
    assert "Authorization" not in mock.last.headers
    assert mock.last.headers["X-Brain-ID"] == "other-brain"
    body = mock.json_body()
    assert body["text"] == "Who is Ada?"
    assert body["as_of"] == "2025-01-01T00:00:00Z"


def test_ingest_save_search_retrieve() -> None:
    mock = MockAPI()
    mock.route(
        "POST",
        "/ingest/",
        status=202,
        json_body={"message": "accepted", "task_id": "task-1"},
    )
    mock.route(
        "POST",
        "/retrieve/search",
        json_body={
            "hits": [
                {
                    "id": "h1",
                    "channel": "passages",
                    "score": 0.9,
                    "scores": {"bm25": 0.8},
                    "snippet": "Ada joined design",
                    "labels": [],
                }
            ]
        },
    )
    mock.route(
        "GET",
        "/retrieve/",
        json_body={"data": [{"name": "Ada"}], "observations": [], "relationships": []},
    )
    with sync_client(mock) as brain:
        accepted = brain.save("Ada joined the design team.")
        assert accepted.task_id == "task-1"
        ingest_body = mock.json_body(mock.calls[0])
        assert ingest_body["data"] == {
            "data_type": "text",
            "text_data": "Ada joined the design team.",
        }
        hits = brain.search("Ada", as_of="2024-12-01T00:00:00Z")
        assert hits.hits[0].snippet.startswith("Ada")
        assert mock.json_body(mock.calls[1])["as_of"] == "2024-12-01T00:00:00Z"
        retrieved = brain.retrieve("Ada", include_validity_unknown=True)
        assert retrieved.data[0]["name"] == "Ada"
        assert mock.calls[2].url.params["include_validity_unknown"] == "true"


def test_ingest_json_and_structured() -> None:
    mock = MockAPI()
    mock.route(
        "POST",
        "/ingest/",
        status=202,
        json_body={"message": "accepted", "task_id": "t-json"},
    )
    mock.route(
        "POST",
        "/ingest/structured",
        status=202,
        json_body={"message": "accepted", "task_id": "t-struct"},
    )
    with sync_client(mock) as brain:
        brain.ingest(json_data={"title": "Ada"})
        brain.ingest_structured(
            [{"object": {"name": "Ada", "labels": ["Person"]}}],
            text="Ada is a person",
        )
    assert mock.json_body(mock.calls[0])["data"]["data_type"] == "json"
    struct = mock.json_body(mock.calls[1])
    assert struct["text"] == "Ada is a person"
    assert struct["data"][0]["object"]["name"] == "Ada"


def test_ingest_url_and_file() -> None:
    mock = MockAPI()
    mock.route(
        "POST",
        "/ingest/url",
        status=202,
        json_body={"message": "accepted", "task_id": "t-url"},
    )
    mock.route(
        "POST",
        "/ingest/file",
        status=202,
        json_body={"message": "accepted", "task_id": "t-file"},
    )
    with sync_client(mock) as brain:
        brain.ingest_url("https://example.test/notes")
        brain.ingest_file(b"hello", filename="notes.txt", content_type="text/plain")
    assert mock.json_body(mock.calls[0])["url"] == "https://example.test/notes"
    assert mock.calls[1].headers["content-type"].startswith("multipart/form-data")


def test_facts_conflicts_and_graph() -> None:
    mock = MockAPI()
    mock.route(
        "GET",
        "/model/facts",
        json_body={
            "facts": [
                {
                    "kind": "relationship",
                    "fact_id": "f1",
                    "name": "joined",
                    "verification": {"state": "unverified"},
                }
            ],
            "total": 1,
        },
    )
    mock.route(
        "POST",
        "/model/facts/f1/verify",
        json_body={
            "kind": "relationship",
            "fact_id": "f1",
            "name": "joined",
            "verification": {"state": "verified", "note": "ok"},
        },
    )
    mock.route(
        "GET",
        "/retrieve/conflicts",
        json_body={"conflicts": [{"id": "c1", "status": "open"}], "count": 1, "total": 1},
    )
    mock.route(
        "POST",
        "/retrieve/conflicts/c1/resolve",
        json_body={"conflict": {"id": "c1", "status": "resolved"}},
    )
    mock.route(
        "GET",
        "/retrieve/entity/info",
        json_body={"target_node": {"name": "Ada", "labels": ["Person"]}},
    )
    mock.route(
        "GET",
        "/retrieve/entities",
        json_body={"entities": [{"name": "Ada"}], "total": 1},
    )
    mock.route(
        "POST",
        "/model/entity",
        json_body={"uuid": "n1", "name": "Ada"},
    )
    with sync_client(mock) as brain:
        facts = brain.list_facts(state="unverified")
        assert facts.facts[0].fact_id == "f1"
        verified = brain.verify_fact("f1", note="ok")
        assert verified.verification.state == "verified"
        conflicts = brain.list_conflicts(status="open")
        assert conflicts.count == 1
        resolved = brain.resolve_conflict("c1", winning_fact_id="f1")
        assert resolved.conflict["status"] == "resolved"
        info = brain.entity_info("Ada")
        assert info.target_node.name == "Ada"
        listed = brain.list_entities(query_text="Ada")
        assert listed.total == 1
        created = brain.add_entity("Ada", labels=["Person"])
        assert created["name"] == "Ada"
    assert mock.calls[0].url.params["state"] == "unverified"
    assert mock.json_body(mock.calls[1])["note"] == "ok"
    assert mock.json_body(mock.calls[3])["winning_fact_id"] == "f1"


def test_tasks_wait_and_timeout() -> None:
    mock = MockAPI()
    mock.route(
        "GET",
        "/tasks/task-1",
        sequence=[
            {"json": {"status": "running", "task_id": "task-1"}},
            {"json": {"status": "completed", "task_id": "task-1"}},
        ],
    )
    with sync_client(mock) as brain:
        done = brain.wait_for_task("task-1", poll_interval=0)
        assert done.is_terminal
        assert done.status == "completed"

    timeout_mock = MockAPI()
    timeout_mock.route(
        "GET",
        "/tasks/slow",
        json_body={"status": "running", "task_id": "slow"},
    )
    with sync_client(timeout_mock) as brain:
        with pytest.raises(TaskTimeoutError) as exc:
            brain.wait_for_task("slow", poll_interval=0, timeout=0)
        assert exc.value.task_id == "slow"
        assert exc.value.last_status == "running"


def test_wait_for_task_clamps_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("lumen_brain.client.time.sleep", lambda seconds: sleeps.append(seconds))
    mock = MockAPI()
    mock.route(
        "GET",
        "/tasks/slow",
        json_body={"status": "running", "task_id": "slow"},
    )
    with sync_client(mock) as brain:
        with pytest.raises(TaskTimeoutError) as exc:
            brain.wait_for_task("slow", poll_interval=60, timeout=0.05)
    assert exc.value.last_status == "running"
    assert len(sleeps) == 1
    assert 0 < sleeps[0] <= 0.05 + 0.02
    assert len(mock.calls) == 1


def test_error_envelope_from_client() -> None:
    mock = MockAPI()
    mock.route(
        "POST",
        "/retrieve/context",
        status=401,
        json_body={
            "detail": "Invalid token",
            "error": {
                "code": "unauthorized",
                "message": "Invalid token",
                "resolution": "Rotate the PAT",
                "request_id": "req-9",
            },
        },
    )
    with sync_client(mock) as brain:
        with pytest.raises(BrainAPIError) as exc:
            brain.query("hello")
    assert exc.value.code == "unauthorized"
    assert exc.value.request_id == "req-9"
    assert exc.value.resolution == "Rotate the PAT"


def test_query_alias_and_custom_base_url() -> None:
    mock = MockAPI()
    mock.route(
        "POST",
        "/retrieve/context",
        json_body={"text_context": "ok", "triples": []},
    )
    with sync_client(mock, base_url="https://brain.example.test") as brain:
        result = brain.query("hello")
    assert result.text_context == "ok"
    assert str(mock.last.url).startswith("https://brain.example.test/retrieve/context")


def test_scan_conflicts_and_system_brains() -> None:
    mock = MockAPI()
    mock.route(
        "POST",
        "/retrieve/conflicts/scan",
        status=202,
        json_body={"message": "accepted", "task_id": "scan-1"},
    )
    mock.route("GET", "/system/brains-list", json_body=[{"name_key": "brain-1"}])
    mock.route(
        "POST",
        "/system/brains",
        json_body={"name_key": "new-brain", "id": "new-brain"},
    )
    with sync_client(mock) as brain:
        scan = brain.scan_conflicts()
        assert scan.task_id == "scan-1"
        listed = brain.list_brains()
        assert listed[0]["name_key"] == "brain-1"
        created = brain.create_brain("new-brain")
        assert created.name_key == "new-brain"
    assert mock.json_body(mock.calls[2]) == {"brain_id": "new-brain"}


def test_reject_reset_dismiss_neighbors() -> None:
    mock = MockAPI()
    mock.route(
        "POST",
        "/model/facts/f1/reject",
        json_body={
            "kind": "node",
            "fact_id": "f1",
            "name": "Ada",
            "verification": {"state": "rejected"},
        },
    )
    mock.route(
        "POST",
        "/model/facts/f1/reset",
        json_body={
            "kind": "node",
            "fact_id": "f1",
            "name": "Ada",
            "verification": {"state": "unverified"},
        },
    )
    mock.route(
        "POST",
        "/retrieve/conflicts/c1/dismiss",
        json_body={"conflict": {"id": "c1", "status": "dismissed"}},
    )
    mock.route(
        "GET",
        "/retrieve/entities/neighbors",
        json_body={"count": 1, "neighbors": [{"name": "Berlin"}]},
    )
    with sync_client(mock) as brain:
        assert brain.reject_fact("f1").verification.state == "rejected"
        assert brain.reset_fact("f1").verification.state == "unverified"
        dismissed = brain.dismiss_conflict("c1", notes="duplicate")
        assert dismissed.conflict["status"] == "dismissed"
        neighbors = brain.neighbors("uuid-ada")
        assert neighbors.count == 1
    assert mock.json_body(mock.calls[2]) == {"notes": "duplicate"}
    assert mock.calls[3].url.params["uuid"] == "uuid-ada"
