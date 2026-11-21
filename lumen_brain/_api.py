from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Optional, Type, Union
from urllib.parse import quote

from pydantic import BaseModel

from lumen_brain._http import drop_none
from lumen_brain.models import (
    Brain,
    BrainLifecycleResponse,
    CancelIngestionResponse,
    ChangelogItemResponse,
    ChangelogListResponse,
    ConflictItemResponse,
    ConflictListResponse,
    ConflictReportResponse,
    ConflictScanAcceptedResponse,
    EntityListResponse,
    FactVerificationListResponse,
    FactVerificationRecord,
    GetContextResponse,
    GetEntityContextResponse,
    GetEntityInfoResponse,
    GetEntityStatusResponse,
    GraphNode,
    HealthResponse,
    IngestGroupMeterResponse,
    IngestionAcceptedResponse,
    IngestionCapabilitiesResponse,
    IngestionTripleSet,
    LoginInfoResponse,
    NeighborResponse,
    ObservationItemResponse,
    ObservationListResponse,
    PartialNode,
    PurgeIngestionResponse,
    RecommendResponse,
    RelationshipListResponse,
    RetrieveResponse,
    SearchResponse,
    StructuredDataItemResponse,
    StructuredDataListResponse,
    TaskListResponse,
    TaskStateResponse,
    TextChunkListResponse,
    TypeListResponse,
)

JsonMapping = Mapping[str, Any]
TripleInput = Union[IngestionTripleSet, Mapping[str, Any]]
NodeInput = Union[PartialNode, Mapping[str, Any]]


@dataclass
class RequestSpec:
    method: str
    path: str
    json: Any = None
    params: Optional[dict[str, Any]] = None
    files: Any = None
    data: Optional[dict[str, Any]] = None
    expected_status: tuple[int, ...] = (200,)
    model: Optional[Type[BaseModel]] = None
    raw: bool = False
    requires_brain: bool = True
    extra_headers: dict[str, str] = field(default_factory=dict)


def _model_dump(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, Mapping):
        return dict(value)
    return value


def _optional_dict(value: Optional[JsonMapping]) -> Optional[dict[str, Any]]:
    if value is None:
        return None
    return dict(value)


def ingest_text(
    text: str,
    *,
    meta_keys: Optional[JsonMapping] = None,
    identification_params: Optional[JsonMapping] = None,
    observate_for: Optional[Sequence[str]] = None,
    preferred_extraction_entities: Optional[Sequence[str]] = None,
    source_timestamp: Optional[str] = None,
    skip_enrichment: bool = False,
    group_tracking: Optional[str] = None,
    task_identifier: Optional[str] = None,
) -> RequestSpec:
    payload = drop_none(
        {
            "data": {"data_type": "text", "text_data": text},
            "meta_keys": _optional_dict(meta_keys),
            "identification_params": _optional_dict(identification_params),
            "observate_for": list(observate_for) if observate_for else None,
            "preferred_extraction_entities": (
                list(preferred_extraction_entities) if preferred_extraction_entities else None
            ),
            "source_timestamp": source_timestamp,
            "skip_enrichment": skip_enrichment,
            "group_tracking": group_tracking,
        }
    )
    headers = {}
    if task_identifier:
        headers["Task-Identifier"] = task_identifier
    return RequestSpec(
        "POST",
        "/ingest/",
        json=payload,
        expected_status=(202,),
        model=IngestionAcceptedResponse,
        extra_headers=headers,
    )


def ingest_json(
    json_data: JsonMapping,
    *,
    meta_keys: Optional[JsonMapping] = None,
    identification_params: Optional[JsonMapping] = None,
    observate_for: Optional[Sequence[str]] = None,
    preferred_extraction_entities: Optional[Sequence[str]] = None,
    source_timestamp: Optional[str] = None,
    skip_enrichment: bool = False,
    group_tracking: Optional[str] = None,
    task_identifier: Optional[str] = None,
) -> RequestSpec:
    payload = drop_none(
        {
            "data": {"data_type": "json", "json_data": dict(json_data)},
            "meta_keys": _optional_dict(meta_keys),
            "identification_params": _optional_dict(identification_params),
            "observate_for": list(observate_for) if observate_for else None,
            "preferred_extraction_entities": (
                list(preferred_extraction_entities) if preferred_extraction_entities else None
            ),
            "source_timestamp": source_timestamp,
            "skip_enrichment": skip_enrichment,
            "group_tracking": group_tracking,
        }
    )
    headers = {}
    if task_identifier:
        headers["Task-Identifier"] = task_identifier
    return RequestSpec(
        "POST",
        "/ingest/",
        json=payload,
        expected_status=(202,),
        model=IngestionAcceptedResponse,
        extra_headers=headers,
    )


def ingest_structured(
    data: Sequence[TripleInput],
    *,
    anchor: Optional[NodeInput] = None,
    text: Optional[str] = None,
    mode: Optional[str] = None,
    group_tracking: Optional[str] = None,
) -> RequestSpec:
    payload = drop_none(
        {
            "data": [_model_dump(item) for item in data],
            "anchor": _model_dump(anchor) if anchor is not None else None,
            "text": text,
            "mode": mode,
            "group_tracking": group_tracking,
        }
    )
    return RequestSpec(
        "POST",
        "/ingest/structured",
        json=payload,
        expected_status=(202,),
        model=IngestionAcceptedResponse,
    )


def ingest_url(
    url: str,
    *,
    progressive: bool = False,
    max_pages: int = 10,
    allowed_domains: Optional[Sequence[str]] = None,
    allowed_path_prefixes: Optional[Sequence[str]] = None,
    group_tracking: Optional[str] = None,
    skip_enrichment: bool = False,
) -> RequestSpec:
    payload = drop_none(
        {
            "url": url,
            "progressive": progressive,
            "max_pages": max_pages,
            "allowed_domains": list(allowed_domains) if allowed_domains else None,
            "allowed_path_prefixes": (
                list(allowed_path_prefixes) if allowed_path_prefixes else None
            ),
            "group_tracking": group_tracking,
            "skip_enrichment": skip_enrichment,
        }
    )
    return RequestSpec(
        "POST",
        "/ingest/url",
        json=payload,
        expected_status=(202,),
        model=IngestionAcceptedResponse,
    )


def ingest_file(
    content: bytes,
    filename: str = "upload.bin",
    content_type: str = "application/octet-stream",
    *,
    group_tracking: Optional[str] = None,
) -> RequestSpec:
    data = drop_none({"group_tracking": group_tracking})
    return RequestSpec(
        "POST",
        "/ingest/file",
        files={"file": (filename, content, content_type)},
        data=data or None,
        expected_status=(202,),
        model=IngestionAcceptedResponse,
    )


def get_context(
    text: str,
    *,
    as_of: Optional[str] = None,
    include_validity_unknown: bool = False,
    annotate_conflicts: bool = False,
    include_history: Optional[bool] = None,
    historical_limit: int = 10,
    max_facts: int = 40,
    max_passages: int = 8,
    apply_fact_filter: bool = True,
    use_ppr: bool = True,
    sufficiency_retry: bool = False,
    profile_stages: bool = False,
    cross_event_bridges: int = 3,
    include_rejected: bool = False,
) -> RequestSpec:
    payload = drop_none(
        {
            "text": text,
            "as_of": as_of,
            "include_validity_unknown": include_validity_unknown,
            "annotate_conflicts": annotate_conflicts,
            "include_history": include_history,
            "historical_limit": historical_limit,
            "max_facts": max_facts,
            "max_passages": max_passages,
            "apply_fact_filter": apply_fact_filter,
            "use_ppr": use_ppr,
            "sufficiency_retry": sufficiency_retry,
            "profile_stages": profile_stages,
            "cross_event_bridges": cross_event_bridges,
            "include_rejected": include_rejected,
        }
    )
    return RequestSpec("POST", "/retrieve/context", json=payload, model=GetContextResponse)


def search(
    query: str,
    *,
    as_of: Optional[str] = None,
    include_validity_unknown: bool = False,
    k: int = 10,
    channels: Optional[Sequence[str]] = None,
    node_labels: Optional[Sequence[str]] = None,
    community_labels: Optional[Sequence[str]] = None,
    expand: str = "none",
    fusion: Optional[str] = None,
    fusion_alpha: Optional[float] = None,
    rerank: Optional[str] = None,
    mode: str = "default",
    profile_stages: bool = False,
    extras: Optional[Mapping[str, str]] = None,
    target: Optional[str] = None,
    include_rejected: bool = False,
) -> RequestSpec:
    payload = drop_none(
        {
            "query": query,
            "as_of": as_of,
            "include_validity_unknown": include_validity_unknown,
            "k": k,
            "channels": list(channels) if channels is not None else ["passages"],
            "node_labels": list(node_labels) if node_labels else None,
            "community_labels": list(community_labels) if community_labels else None,
            "expand": expand,
            "fusion": fusion,
            "fusion_alpha": fusion_alpha,
            "rerank": rerank,
            "mode": mode,
            "profile_stages": profile_stages,
            "extras": dict(extras) if extras else None,
            "target": target,
            "include_rejected": include_rejected,
        }
    )
    return RequestSpec("POST", "/retrieve/search", json=payload, model=SearchResponse)


def retrieve(
    text: str,
    *,
    limit: int = 10,
    preferred_entities: Optional[Sequence[str]] = None,
    include_rejected: bool = False,
    as_of: Optional[str] = None,
    include_validity_unknown: bool = False,
) -> RequestSpec:
    params = drop_none(
        {
            "text": text,
            "limit": limit,
            "preferred_entities": (",".join(preferred_entities) if preferred_entities else None),
            "include_rejected": include_rejected,
            "as_of": as_of,
            "include_validity_unknown": include_validity_unknown,
        }
    )
    return RequestSpec("GET", "/retrieve/", params=params, model=RetrieveResponse)


def entity_info(
    target: str,
    query: str,
    *,
    max_depth: int = 2,
) -> RequestSpec:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query is required")
    return RequestSpec(
        "GET",
        "/retrieve/entity/info",
        params=drop_none({"target": target, "query": query, "max_depth": max_depth}),
        model=GetEntityInfoResponse,
    )


def entity_context(target: str, *, context_depth: int = 1) -> RequestSpec:
    return RequestSpec(
        "GET",
        "/retrieve/entity/context",
        params={"target": target, "context_depth": context_depth},
        model=GetEntityContextResponse,
    )


def entity_status(target: str) -> RequestSpec:
    return RequestSpec(
        "GET",
        "/retrieve/entity/status",
        params={"target": target},
        model=GetEntityStatusResponse,
    )


def entity_synergies(
    target: str,
    *,
    polarity: str = "same",
    do: Optional[float] = None,
    pa: Optional[float] = None,
    ppa: Optional[float] = None,
    top_k: int = 20,
) -> RequestSpec:
    return RequestSpec(
        "GET",
        "/retrieve/entity/synergies",
        params=drop_none(
            {
                "target": target,
                "polarity": polarity,
                "do": do,
                "pa": pa,
                "ppa": ppa,
                "top_k": top_k,
            }
        ),
        raw=True,
    )


def list_entities(
    *,
    limit: int = 10,
    skip: int = 0,
    node_labels: Optional[Sequence[str]] = None,
    query_text: Optional[str] = None,
) -> RequestSpec:
    return RequestSpec(
        "GET",
        "/retrieve/entities",
        params=drop_none(
            {
                "limit": limit,
                "skip": skip,
                "node_labels": ",".join(node_labels) if node_labels else None,
                "query_text": query_text,
            }
        ),
        model=EntityListResponse,
    )


def list_relationships(
    *,
    limit: int = 10,
    skip: int = 0,
    relationship_types: Optional[Sequence[str]] = None,
    from_node_labels: Optional[Sequence[str]] = None,
    to_node_labels: Optional[Sequence[str]] = None,
    query_text: Optional[str] = None,
    query_search_target: Optional[str] = None,
) -> RequestSpec:
    return RequestSpec(
        "GET",
        "/retrieve/relationships",
        params=drop_none(
            {
                "limit": limit,
                "skip": skip,
                "relationship_types": (
                    ",".join(relationship_types) if relationship_types else None
                ),
                "from_node_labels": (",".join(from_node_labels) if from_node_labels else None),
                "to_node_labels": ",".join(to_node_labels) if to_node_labels else None,
                "query_text": query_text,
                "query_search_target": query_search_target,
            }
        ),
        model=RelationshipListResponse,
    )


def neighbors(
    uuid: str,
    *,
    limit: int = 10,
    look_for: Optional[str] = None,
    include_rejected: bool = False,
) -> RequestSpec:
    return RequestSpec(
        "GET",
        "/retrieve/entities/neighbors",
        params=drop_none(
            {
                "uuid": uuid,
                "limit": limit,
                "look_for": look_for,
                "include_rejected": include_rejected,
            }
        ),
        model=NeighborResponse,
    )


def recommend(
    target: str,
    *,
    polarity: str = "same",
    top_k: int = 20,
    labels: Optional[Sequence[str]] = None,
    include_asymmetric: bool = True,
    include_multi_interest: bool = True,
    include_attribute_pref: bool = False,
    diversify: bool = True,
    asymmetric_direction: str = "outbound",
    exclude_seen: bool = False,
    recency_half_life_days: Optional[float] = None,
    dampen_degree: bool = False,
    behavior_weights: Optional[Mapping[str, float]] = None,
) -> RequestSpec:
    payload = drop_none(
        {
            "target": target,
            "polarity": polarity,
            "top_k": top_k,
            "labels": list(labels) if labels else None,
            "include_asymmetric": include_asymmetric,
            "include_multi_interest": include_multi_interest,
            "include_attribute_pref": include_attribute_pref,
            "diversify": diversify,
            "asymmetric_direction": asymmetric_direction,
            "exclude_seen": exclude_seen,
            "recency_half_life_days": recency_half_life_days,
            "dampen_degree": dampen_degree,
            "behavior_weights": dict(behavior_weights) if behavior_weights else None,
        }
    )
    return RequestSpec("POST", "/retrieve/recommend", json=payload, model=RecommendResponse)


def add_entity(
    name: str,
    *,
    labels: Optional[Sequence[str]] = None,
    description: Optional[str] = None,
    properties: Optional[JsonMapping] = None,
    identification_params: Optional[JsonMapping] = None,
    metadata: Optional[JsonMapping] = None,
) -> RequestSpec:
    payload = drop_none(
        {
            "name": name,
            "labels": list(labels) if labels else [],
            "description": description,
            "properties": dict(properties) if properties else None,
            "identification_params": (
                dict(identification_params) if identification_params else None
            ),
            "metadata": dict(metadata) if metadata else None,
        }
    )
    return RequestSpec("POST", "/model/entity", json=payload, raw=True)


def update_entity(
    uuid: str,
    *,
    new_name: Optional[str] = None,
    new_description: Optional[str] = None,
    new_labels: Optional[Sequence[str]] = None,
    new_properties: Optional[JsonMapping] = None,
    properties_to_remove: Optional[Sequence[str]] = None,
) -> RequestSpec:
    payload = drop_none(
        {
            "uuid": uuid,
            "new_name": new_name,
            "new_description": new_description,
            "new_labels": list(new_labels) if new_labels else None,
            "new_properties": dict(new_properties) if new_properties else None,
            "properties_to_remove": (list(properties_to_remove) if properties_to_remove else None),
        }
    )
    return RequestSpec("PUT", "/model/entity", json=payload, model=GraphNode)


def add_relationship(
    subject_uuid: str,
    predicate_name: str,
    object_uuid: str,
    *,
    predicate_description: str = "",
) -> RequestSpec:
    return RequestSpec(
        "POST",
        "/model/relationship",
        json={
            "subject_uuid": subject_uuid,
            "predicate_name": predicate_name,
            "predicate_description": predicate_description,
            "object_uuid": object_uuid,
        },
        raw=True,
    )


def update_relationship(
    uuid: str,
    *,
    new_properties: Optional[JsonMapping] = None,
    properties_to_remove: Optional[Sequence[str]] = None,
) -> RequestSpec:
    payload = drop_none(
        {
            "uuid": uuid,
            "new_properties": dict(new_properties) if new_properties else None,
            "properties_to_remove": (list(properties_to_remove) if properties_to_remove else None),
        }
    )
    return RequestSpec("PUT", "/model/relationship", json=payload, raw=True)


def list_facts(
    *,
    state: Optional[str] = None,
    include_rejected: bool = False,
    limit: int = 50,
    skip: int = 0,
) -> RequestSpec:
    return RequestSpec(
        "GET",
        "/model/facts",
        params=drop_none(
            {
                "state": state,
                "include_rejected": include_rejected,
                "limit": limit,
                "skip": skip,
            }
        ),
        model=FactVerificationListResponse,
    )


def get_fact(fact_id: str) -> RequestSpec:
    return RequestSpec("GET", f"/model/facts/{fact_id}", model=FactVerificationRecord)


def _fact_action(fact_id: str, action: str, **body: Any) -> RequestSpec:
    return RequestSpec(
        "POST",
        f"/model/facts/{fact_id}/{action}",
        json=drop_none(body),
        model=FactVerificationRecord,
    )


def verify_fact(
    fact_id: str,
    *,
    verification_source: Optional[str] = None,
    note: Optional[str] = None,
) -> RequestSpec:
    return _fact_action(fact_id, "verify", verification_source=verification_source, note=note)


def reject_fact(
    fact_id: str,
    *,
    verification_source: Optional[str] = None,
    note: Optional[str] = None,
) -> RequestSpec:
    return _fact_action(fact_id, "reject", verification_source=verification_source, note=note)


def reset_fact(
    fact_id: str,
    *,
    verification_source: Optional[str] = None,
    note: Optional[str] = None,
) -> RequestSpec:
    return _fact_action(fact_id, "reset", verification_source=verification_source, note=note)


def list_conflicts(
    *,
    limit: int = 10,
    skip: int = 0,
    status: Optional[str] = None,
    source: Optional[str] = None,
    subject: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
) -> RequestSpec:
    return RequestSpec(
        "GET",
        "/retrieve/conflicts",
        params=drop_none(
            {
                "limit": limit,
                "skip": skip,
                "status": status,
                "source": source,
                "subject": subject,
                "since": since,
                "until": until,
            }
        ),
        model=ConflictListResponse,
    )


def get_conflict(conflict_id: str) -> RequestSpec:
    return RequestSpec("GET", f"/retrieve/conflicts/{conflict_id}", model=ConflictItemResponse)


def resolve_conflict(
    conflict_id: str,
    *,
    winning_fact_id: Optional[str] = None,
    notes: Optional[str] = None,
    method: str = "manual",
) -> RequestSpec:
    return RequestSpec(
        "POST",
        f"/retrieve/conflicts/{conflict_id}/resolve",
        json=drop_none(
            {
                "winning_fact_id": winning_fact_id,
                "notes": notes,
                "method": method,
            }
        ),
        model=ConflictItemResponse,
    )


def dismiss_conflict(conflict_id: str, *, notes: Optional[str] = None) -> RequestSpec:
    return RequestSpec(
        "POST",
        f"/retrieve/conflicts/{conflict_id}/dismiss",
        json=drop_none({"notes": notes}),
        model=ConflictItemResponse,
    )


def conflict_report(
    *,
    status: Optional[str] = None,
    source: Optional[str] = None,
    subject: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    format: str = "json",
    limit: int = 200,
    skip: int = 0,
) -> RequestSpec:
    return RequestSpec(
        "GET",
        "/retrieve/conflicts/report",
        params=drop_none(
            {
                "status": status,
                "source": source,
                "subject": subject,
                "since": since,
                "until": until,
                "format": format,
                "limit": limit,
                "skip": skip,
            }
        ),
        model=ConflictReportResponse,
        raw=format == "markdown",
    )


def scan_conflicts(*, use_llm: bool = False) -> RequestSpec:
    return RequestSpec(
        "POST",
        "/retrieve/conflicts/scan",
        json={"use_llm": use_llm},
        expected_status=(202,),
        model=ConflictScanAcceptedResponse,
    )


def list_changelogs(
    *,
    limit: int = 10,
    skip: int = 0,
    types: Optional[str] = None,
    query_text: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
) -> RequestSpec:
    return RequestSpec(
        "GET",
        "/retrieve/changelogs",
        params=drop_none(
            {
                "limit": limit,
                "skip": skip,
                "types": types,
                "query_text": query_text,
                "since": since,
                "until": until,
            }
        ),
        model=ChangelogListResponse,
    )


def get_changelog(changelog_id: str) -> RequestSpec:
    return RequestSpec("GET", f"/retrieve/changelogs/{changelog_id}", model=ChangelogItemResponse)


def changelog_types() -> RequestSpec:
    return RequestSpec("GET", "/retrieve/changelogs/types", model=TypeListResponse)


def list_observations(
    *,
    limit: int = 10,
    skip: int = 0,
    resource_id: Optional[str] = None,
    labels: Optional[str] = None,
    query_text: Optional[str] = None,
) -> RequestSpec:
    return RequestSpec(
        "GET",
        "/retrieve/observations",
        params=drop_none(
            {
                "limit": limit,
                "skip": skip,
                "resource_id": resource_id,
                "labels": labels,
                "query_text": query_text,
            }
        ),
        model=ObservationListResponse,
    )


def get_observation(observation_id: str) -> RequestSpec:
    return RequestSpec(
        "GET",
        f"/retrieve/observations/{observation_id}",
        model=ObservationItemResponse,
    )


def list_structured_data(
    *,
    limit: int = 10,
    skip: int = 0,
    types: Optional[str] = None,
    query_text: Optional[str] = None,
) -> RequestSpec:
    return RequestSpec(
        "GET",
        "/retrieve/structured-data",
        params=drop_none(
            {
                "limit": limit,
                "skip": skip,
                "types": types,
                "query_text": query_text,
            }
        ),
        model=StructuredDataListResponse,
    )


def get_structured_data(item_id: str) -> RequestSpec:
    return RequestSpec(
        "GET",
        f"/retrieve/structured-data/{item_id}",
        model=StructuredDataItemResponse,
    )


def list_text_chunks(
    *,
    limit: int = 10,
    skip: int = 0,
    query_text: Optional[str] = None,
    metadata_eq: Optional[str] = None,
    order: Optional[str] = None,
) -> RequestSpec:
    return RequestSpec(
        "GET",
        "/retrieve/text-chunks",
        params=drop_none(
            {
                "limit": limit,
                "skip": skip,
                "query_text": query_text,
                "metadata_eq": metadata_eq,
                "order": order,
            }
        ),
        model=TextChunkListResponse,
    )


def get_task(task_id: str) -> RequestSpec:
    return RequestSpec("GET", f"/tasks/{task_id}", model=TaskStateResponse)


def list_tasks() -> RequestSpec:
    return RequestSpec("GET", "/tasks/", model=TaskListResponse)


def cancel_task(task_id: str, mode: str = "keep_saved") -> RequestSpec:
    return RequestSpec(
        "POST",
        f"/tasks/{task_id}/cancel",
        json={"mode": mode},
        expected_status=(202, 200),
        model=CancelIngestionResponse,
    )


def purge_task(
    task_id: str,
    *,
    digest: Optional[str] = None,
    source_key: Optional[str] = None,
) -> RequestSpec:
    return RequestSpec(
        "POST",
        f"/tasks/{task_id}/purge",
        json=drop_none({"digest": digest, "source_key": source_key}),
        model=PurgeIngestionResponse,
    )


def task_activity(task_id: str, *, offset: int = 0, limit: int = 50) -> RequestSpec:
    return RequestSpec(
        "GET",
        f"/tasks/{task_id}/activity",
        params={"offset": offset, "limit": limit},
        raw=True,
    )


def health() -> RequestSpec:
    return RequestSpec(
        "GET", "/health", model=HealthResponse, requires_brain=False, expected_status=(200,)
    )


def login_info() -> RequestSpec:
    return RequestSpec("GET", "/meta/login-info", model=LoginInfoResponse, requires_brain=False)


def entity_labels() -> RequestSpec:
    return RequestSpec("GET", "/meta/entity-labels", raw=True)


def entity_properties() -> RequestSpec:
    return RequestSpec("GET", "/meta/entity-properties", raw=True)


def relationship_properties() -> RequestSpec:
    return RequestSpec("GET", "/meta/relationships-properties", raw=True)


def ingestion_capabilities() -> RequestSpec:
    return RequestSpec("GET", "/meta/ingestion-capabilities", model=IngestionCapabilitiesResponse)


def ingest_group(group_tracking: str) -> RequestSpec:
    return RequestSpec(
        "GET",
        f"/meta/ingest-groups/{quote(group_tracking, safe='')}",
        model=IngestGroupMeterResponse,
    )


def list_brains() -> RequestSpec:
    return RequestSpec("GET", "/system/brains-list", requires_brain=False, raw=True)


def create_brain(brain_id: str) -> RequestSpec:
    return RequestSpec(
        "POST",
        "/system/brains",
        json={"brain_id": brain_id},
        requires_brain=False,
        model=Brain,
    )


def clear_brain(brain_id: str) -> RequestSpec:
    return RequestSpec(
        "POST",
        f"/system/brains/{brain_id}/clear",
        requires_brain=False,
        model=BrainLifecycleResponse,
    )


def delete_brain(brain_id: str) -> RequestSpec:
    return RequestSpec(
        "DELETE",
        f"/system/brains/{brain_id}",
        requires_brain=False,
        model=BrainLifecycleResponse,
    )
