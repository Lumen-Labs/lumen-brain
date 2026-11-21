from __future__ import annotations

from lumen_brain import AsyncLumenBrainDriver, LumenBrainDriver
from tests.helpers import MockAPI, async_client, sync_client


def test_driver_aliases() -> None:
    from lumen_brain import AsyncLumenBrain, LumenBrain

    assert LumenBrainDriver is LumenBrain
    assert AsyncLumenBrainDriver is AsyncLumenBrain


def test_save_message_polls_task() -> None:
    mock = MockAPI()
    mock.route(
        "POST",
        "/ingest/",
        status=202,
        json_body={"message": "accepted", "task_id": "task-msg"},
    )
    mock.route(
        "GET",
        "/tasks/task-msg",
        json_body={"status": "completed", "task_id": "task-msg"},
    )
    with sync_client(mock) as brain:
        result = brain.save_message(
            memory_uuid="mem-1",
            type="message",
            content="Hello from Ada",
            role="user",
            conversation_id="conv-1",
            metadata={"source": "chat"},
        )
    assert result.status == "completed"
    body = mock.json_body(mock.calls[0])
    assert body["data"]["text_data"] == "Hello from Ada"
    assert body["identification_params"]["memory_id"] == "mem-1"
    assert body["identification_params"]["conversation_id"] == "conv-1"
    assert body["identification_params"]["role"] == "user"
    assert body["meta_keys"] == {"source": "chat"}
    assert mock.calls[0].headers["X-Brain-ID"] == "mem-1"


def test_save_message_wait_false() -> None:
    mock = MockAPI()
    mock.route(
        "POST",
        "/ingest/",
        status=202,
        json_body={"message": "accepted", "task_id": "task-nowait"},
    )
    with sync_client(mock) as brain:
        accepted = brain.inject_knowledge(
            content="notes about Ada",
            wait=False,
        )
    assert accepted.task_id == "task-nowait"
    assert len(mock.calls) == 1


def test_query_memory_and_fetch_info() -> None:
    mock = MockAPI()
    mock.route(
        "POST",
        "/retrieve/context",
        json_body={"text_context": "Ada designs products.", "triples": []},
    )
    mock.route(
        "GET",
        "/retrieve/entity/info",
        json_body={"target_node": {"name": "Ada", "labels": ["Person"]}},
    )
    with sync_client(mock) as brain:
        ctx = brain.query_memory("Who is Ada?", memory_uuid="mem-1")
        info = brain.fetch_info(
            memory_uuid="mem-1",
            entities=["Ada"],
            info="role",
            depth=3,
        )
    assert ctx.text_context.startswith("Ada")
    assert info.target_node.name == "Ada"
    assert mock.calls[0].headers["X-Brain-ID"] == "mem-1"
    assert mock.calls[1].url.params["target"] == "Ada"
    assert mock.calls[1].url.params["query"] == "role"
    assert mock.calls[1].url.params["max_depth"] == "3"


async def test_async_save_message() -> None:
    mock = MockAPI()
    mock.route(
        "POST",
        "/ingest/",
        status=202,
        json_body={"message": "accepted", "task_id": "a1"},
    )
    mock.route(
        "GET",
        "/tasks/a1",
        json_body={"status": "completed", "task_id": "a1"},
    )
    async with async_client(mock) as brain:
        result = await brain.save_message(content="async hello", wait=True)
    assert result.status == "completed"
