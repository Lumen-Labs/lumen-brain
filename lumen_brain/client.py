from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from typing import Any, Optional, Union

import httpx

from lumen_brain import _api
from lumen_brain._base import ClientSettings, send_httpx
from lumen_brain.config import AuthScheme
from lumen_brain.errors import TaskTimeoutError
from lumen_brain.models import (
    IngestionAcceptedResponse,
    IngestionTripleSet,
    TaskStateResponse,
)

JsonMapping = Mapping[str, Any]
TripleInput = Union[IngestionTripleSet, Mapping[str, Any]]


class LumenBrain:
    """Synchronous BrainAPI v2 client."""

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
        client: Optional[httpx.Client] = None,
    ) -> None:
        self._settings = ClientSettings(
            pat,
            api_key=api_key,
            brain_id=brain_id,
            region=region,
            base_url=base_url,
            auth_scheme=auth_scheme,
            timeout=timeout,
        )
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=self._settings.base_url,
            timeout=timeout,
        )

    @property
    def base_url(self) -> str:
        return self._settings.base_url

    @property
    def brain_id(self) -> Optional[str]:
        return self._settings.brain_id

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> LumenBrain:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _send(self, spec: _api.RequestSpec, *, brain_id: Optional[str] = None) -> Any:
        return send_httpx(self._client, self._settings, spec, brain_id=brain_id)

    def ingest(
        self,
        text: Optional[str] = None,
        *,
        json_data: Optional[JsonMapping] = None,
        brain_id: Optional[str] = None,
        **kwargs: Any,
    ) -> IngestionAcceptedResponse:
        if (text is None) == (json_data is None):
            raise ValueError("pass exactly one of text or json_data")
        if text is not None:
            return self._send(_api.ingest_text(text, **kwargs), brain_id=brain_id)
        return self._send(_api.ingest_json(json_data or {}, **kwargs), brain_id=brain_id)

    def ingest_structured(
        self,
        data: Sequence[TripleInput],
        *,
        brain_id: Optional[str] = None,
        **kwargs: Any,
    ) -> IngestionAcceptedResponse:
        return self._send(_api.ingest_structured(data, **kwargs), brain_id=brain_id)

    def ingest_url(
        self, url: str, *, brain_id: Optional[str] = None, **kwargs: Any
    ) -> IngestionAcceptedResponse:
        return self._send(_api.ingest_url(url, **kwargs), brain_id=brain_id)

    def ingest_file(
        self,
        content: bytes,
        filename: str = "upload.bin",
        content_type: str = "application/octet-stream",
        *,
        brain_id: Optional[str] = None,
        **kwargs: Any,
    ) -> IngestionAcceptedResponse:
        return self._send(
            _api.ingest_file(content, filename, content_type, **kwargs),
            brain_id=brain_id,
        )

    def save(self, text: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self.ingest(text=text, brain_id=brain_id, **kwargs)

    def context(self, text: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.get_context(text, **kwargs), brain_id=brain_id)

    def query(self, text: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self.context(text, brain_id=brain_id, **kwargs)

    def search(self, query: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.search(query, **kwargs), brain_id=brain_id)

    def retrieve(self, text: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.retrieve(text, **kwargs), brain_id=brain_id)

    def entity_info(self, target: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.entity_info(target, **kwargs), brain_id=brain_id)

    def entity_context(self, target: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.entity_context(target, **kwargs), brain_id=brain_id)

    def entity_status(self, target: str, *, brain_id: Optional[str] = None):
        return self._send(_api.entity_status(target), brain_id=brain_id)

    def entity_synergies(self, target: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.entity_synergies(target, **kwargs), brain_id=brain_id)

    def list_entities(self, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.list_entities(**kwargs), brain_id=brain_id)

    def list_relationships(self, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.list_relationships(**kwargs), brain_id=brain_id)

    def neighbors(self, uuid: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.neighbors(uuid, **kwargs), brain_id=brain_id)

    def recommend(self, target: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.recommend(target, **kwargs), brain_id=brain_id)

    def add_entity(self, name: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.add_entity(name, **kwargs), brain_id=brain_id)

    def update_entity(self, uuid: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.update_entity(uuid, **kwargs), brain_id=brain_id)

    def add_relationship(
        self,
        subject_uuid: str,
        predicate_name: str,
        object_uuid: str,
        *,
        brain_id: Optional[str] = None,
        **kwargs: Any,
    ):
        return self._send(
            _api.add_relationship(subject_uuid, predicate_name, object_uuid, **kwargs),
            brain_id=brain_id,
        )

    def update_relationship(self, uuid: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.update_relationship(uuid, **kwargs), brain_id=brain_id)

    def list_facts(self, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.list_facts(**kwargs), brain_id=brain_id)

    def get_fact(self, fact_id: str, *, brain_id: Optional[str] = None):
        return self._send(_api.get_fact(fact_id), brain_id=brain_id)

    def verify_fact(self, fact_id: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.verify_fact(fact_id, **kwargs), brain_id=brain_id)

    def reject_fact(self, fact_id: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.reject_fact(fact_id, **kwargs), brain_id=brain_id)

    def reset_fact(self, fact_id: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.reset_fact(fact_id, **kwargs), brain_id=brain_id)

    def list_conflicts(self, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.list_conflicts(**kwargs), brain_id=brain_id)

    def get_conflict(self, conflict_id: str, *, brain_id: Optional[str] = None):
        return self._send(_api.get_conflict(conflict_id), brain_id=brain_id)

    def resolve_conflict(self, conflict_id: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.resolve_conflict(conflict_id, **kwargs), brain_id=brain_id)

    def dismiss_conflict(self, conflict_id: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.dismiss_conflict(conflict_id, **kwargs), brain_id=brain_id)

    def conflict_report(self, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.conflict_report(**kwargs), brain_id=brain_id)

    def scan_conflicts(self, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.scan_conflicts(**kwargs), brain_id=brain_id)

    def list_changelogs(self, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.list_changelogs(**kwargs), brain_id=brain_id)

    def get_changelog(self, changelog_id: str, *, brain_id: Optional[str] = None):
        return self._send(_api.get_changelog(changelog_id), brain_id=brain_id)

    def changelog_types(self, *, brain_id: Optional[str] = None):
        return self._send(_api.changelog_types(), brain_id=brain_id)

    def list_observations(self, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.list_observations(**kwargs), brain_id=brain_id)

    def get_observation(self, observation_id: str, *, brain_id: Optional[str] = None):
        return self._send(_api.get_observation(observation_id), brain_id=brain_id)

    def list_structured_data(self, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.list_structured_data(**kwargs), brain_id=brain_id)

    def get_structured_data(self, item_id: str, *, brain_id: Optional[str] = None):
        return self._send(_api.get_structured_data(item_id), brain_id=brain_id)

    def list_text_chunks(self, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.list_text_chunks(**kwargs), brain_id=brain_id)

    def get_task(self, task_id: str, *, brain_id: Optional[str] = None):
        return self._send(_api.get_task(task_id), brain_id=brain_id)

    def list_tasks(self, *, brain_id: Optional[str] = None):
        return self._send(_api.list_tasks(), brain_id=brain_id)

    def cancel_task(
        self, task_id: str, mode: str = "keep_saved", *, brain_id: Optional[str] = None
    ):
        return self._send(_api.cancel_task(task_id, mode), brain_id=brain_id)

    def purge_task(self, task_id: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.purge_task(task_id, **kwargs), brain_id=brain_id)

    def task_activity(self, task_id: str, *, brain_id: Optional[str] = None, **kwargs: Any):
        return self._send(_api.task_activity(task_id, **kwargs), brain_id=brain_id)

    def wait_for_task(
        self,
        task_id: str,
        *,
        brain_id: Optional[str] = None,
        poll_interval: float = 1.0,
        timeout: float = 120.0,
    ) -> TaskStateResponse:
        deadline = time.monotonic() + timeout
        last = self.get_task(task_id, brain_id=brain_id)
        while True:
            if last.is_terminal:
                return last
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TaskTimeoutError(task_id, last.status)
            if remaining <= poll_interval:
                time.sleep(remaining)
                raise TaskTimeoutError(task_id, last.status)
            time.sleep(poll_interval)
            last = self.get_task(task_id, brain_id=brain_id)

    def health(self):
        return self._send(_api.health())

    def login_info(self):
        return self._send(_api.login_info())

    def entity_labels(self, *, brain_id: Optional[str] = None):
        return self._send(_api.entity_labels(), brain_id=brain_id)

    def entity_properties(self, *, brain_id: Optional[str] = None):
        return self._send(_api.entity_properties(), brain_id=brain_id)

    def relationship_properties(self, *, brain_id: Optional[str] = None):
        return self._send(_api.relationship_properties(), brain_id=brain_id)

    def ingestion_capabilities(self, *, brain_id: Optional[str] = None):
        return self._send(_api.ingestion_capabilities(), brain_id=brain_id)

    def ingest_group(self, group_tracking: str, *, brain_id: Optional[str] = None):
        return self._send(_api.ingest_group(group_tracking), brain_id=brain_id)

    def list_brains(self):
        return self._send(_api.list_brains())

    def create_brain(self, brain_id: str):
        return self._send(_api.create_brain(brain_id))

    def clear_brain(self, brain_id: str):
        return self._send(_api.clear_brain(brain_id))

    def delete_brain(self, brain_id: str):
        return self._send(_api.delete_brain(brain_id))

    def save_message(
        self,
        memory_uuid: Optional[str] = None,
        type: Optional[str] = None,
        content: Optional[str] = None,
        *,
        text: Optional[str] = None,
        role: Optional[str] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[JsonMapping] = None,
        wait: bool = True,
        brain_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        body = text if text is not None else content
        if not body:
            raise ValueError("content or text is required")
        identification = dict(kwargs.pop("identification_params", {}) or {})
        if memory_uuid:
            identification.setdefault("memory_id", memory_uuid)
        if conversation_id:
            identification.setdefault("conversation_id", conversation_id)
        if role:
            identification.setdefault("role", role)
        accepted = self.ingest(
            text=body,
            identification_params=identification or None,
            meta_keys=metadata,
            brain_id=brain_id or memory_uuid,
            **kwargs,
        )
        if not wait:
            return accepted
        return self.wait_for_task(accepted.task_id, brain_id=brain_id or memory_uuid)

    def inject_knowledge(
        self,
        memory_uuid: Optional[str] = None,
        type: Optional[str] = None,
        content: Optional[str] = None,
        *,
        text: Optional[str] = None,
        resource_type: Optional[str] = None,
        metadata: Optional[JsonMapping] = None,
        wait: bool = True,
        brain_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        return self.save_message(
            memory_uuid=memory_uuid,
            type=type or resource_type,
            content=content,
            text=text,
            metadata=metadata,
            wait=wait,
            brain_id=brain_id,
            **kwargs,
        )

    def query_memory(
        self,
        text: str,
        memory_uuid: Optional[str] = None,
        conversation_id: Optional[str] = None,
        *,
        brain_id: Optional[str] = None,
        **kwargs: Any,
    ):
        del conversation_id
        return self.context(text, brain_id=brain_id or memory_uuid, **kwargs)

    def fetch_info(
        self,
        memory_uuid: Optional[str] = None,
        entities: Optional[Sequence[str]] = None,
        info: Optional[str] = None,
        depth: int = 2,
        *,
        brain_id: Optional[str] = None,
        target: Optional[str] = None,
        **kwargs: Any,
    ):
        resolved_target = target or (",".join(entities) if entities else None)
        if not resolved_target:
            raise ValueError("entities or target is required")
        return self.entity_info(
            resolved_target,
            query=info,
            max_depth=depth,
            brain_id=brain_id or memory_uuid,
            **kwargs,
        )


LumenBrainDriver = LumenBrain
