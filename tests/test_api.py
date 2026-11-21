from __future__ import annotations

from collections import UserDict
from datetime import date

import pytest
from pydantic import ValidationError

from lumen_brain import _api
from lumen_brain._base import parse_spec_response
from lumen_brain.models import PartialNode


def test_ingest_text_payload() -> None:
    spec = _api.ingest_text(
        "hello world",
        meta_keys={"source": "notes"},
        identification_params={"conversation_id": "c1"},
        task_identifier="job-1",
        source_timestamp="2025-01-01T00:00:00Z",
    )
    assert spec.method == "POST"
    assert spec.path == "/ingest/"
    assert spec.expected_status == (202,)
    assert spec.json["data"] == {"data_type": "text", "text_data": "hello world"}
    assert spec.json["meta_keys"] == {"source": "notes"}
    assert spec.json["identification_params"] == {"conversation_id": "c1"}
    assert spec.json["source_timestamp"] == "2025-01-01T00:00:00Z"
    assert spec.extra_headers["Task-Identifier"] == "job-1"


def test_ingest_json_payload() -> None:
    spec = _api.ingest_json({"title": "Ada"})
    assert spec.json["data"] == {"data_type": "json", "json_data": {"title": "Ada"}}


def test_ingest_converts_mapping_metadata() -> None:
    spec = _api.ingest_text(
        "hello",
        meta_keys=UserDict({"source": "notes"}),
        identification_params=UserDict({"conversation_id": "c1"}),
    )
    assert type(spec.json["meta_keys"]) is dict
    assert spec.json["meta_keys"] == {"source": "notes"}
    assert type(spec.json["identification_params"]) is dict
    spec_empty = _api.ingest_json({"title": "Ada"}, meta_keys={})
    assert spec_empty.json["meta_keys"] == {}


def test_structured_ingest_serializes_dates() -> None:
    dumped = _api._model_dump(PartialNode(name="Ada", properties={"joined": date(2024, 1, 1)}))
    assert dumped["properties"]["joined"] == "2024-01-01"


def test_context_includes_as_of() -> None:
    spec = _api.get_context(
        "who is Ada?",
        as_of="2025-06-01T00:00:00Z",
        include_validity_unknown=True,
    )
    assert spec.path == "/retrieve/context"
    assert spec.json["text"] == "who is Ada?"
    assert spec.json["as_of"] == "2025-06-01T00:00:00Z"
    assert spec.json["include_validity_unknown"] is True


def test_search_and_retrieve_as_of() -> None:
    search = _api.search("Ada", as_of="2024-01-01T00:00:00Z", k=5)
    assert search.path == "/retrieve/search"
    assert search.json["query"] == "Ada"
    assert search.json["as_of"] == "2024-01-01T00:00:00Z"
    retrieve = _api.retrieve("Ada", as_of="2024-01-01T00:00:00Z", preferred_entities=["Person"])
    assert retrieve.method == "GET"
    assert retrieve.path == "/retrieve/"
    assert retrieve.params["as_of"] == "2024-01-01T00:00:00Z"
    assert retrieve.params["preferred_entities"] == "Person"
    assert "preferred_entities" in retrieve.params


def test_fact_and_conflict_paths() -> None:
    assert _api.list_facts(state="unverified").path == "/model/facts"
    assert _api.get_fact("f1").path == "/model/facts/f1"
    assert _api.verify_fact("f1", note="ok").path == "/model/facts/f1/verify"
    assert _api.list_conflicts(status="open").path == "/retrieve/conflicts"
    assert _api.resolve_conflict("c1", winning_fact_id="f1").path == (
        "/retrieve/conflicts/c1/resolve"
    )
    scan = _api.scan_conflicts(use_llm=True)
    assert scan.expected_status == (202,)
    assert scan.json == {"use_llm": True}


def test_graph_and_system_paths() -> None:
    assert _api.entity_info("Ada", query="role", max_depth=3).params["max_depth"] == 3
    assert _api.neighbors("uuid-1").path == "/retrieve/entities/neighbors"
    assert _api.add_entity("Ada", labels=["Person"]).path == "/model/entity"
    assert _api.create_brain("new-brain").requires_brain is False
    assert _api.health().requires_brain is False
    assert _api.login_info().path == "/meta/login-info"
    purge = _api.purge_task("t1", digest="abc")
    assert purge.path == "/tasks/t1/purge"
    assert purge.json == {"digest": "abc"}
    assert _api.ingest_group("batch#1").path == "/meta/ingest-groups/batch%231"


def test_modeled_response_rejects_empty_body() -> None:
    spec = _api.ingest_text("hello")
    with pytest.raises(ValidationError):
        parse_spec_response(spec, None)
