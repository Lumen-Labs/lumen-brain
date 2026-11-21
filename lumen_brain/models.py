from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

JsonDict = Dict[str, Any]
VerificationState = Literal["unverified", "verified", "rejected"]
AuthSchemeName = Literal["bearer", "brainpat"]


class APIModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ErrorInfo(APIModel):
    code: str
    message: str
    resolution: str
    request_id: str


class ErrorResponse(APIModel):
    detail: Any = None
    error: ErrorInfo


class HealthResponse(APIModel):
    status: str
    service: Optional[str] = None
    version: Optional[str] = None


class LoginInfoResponse(APIModel):
    is_system_pat: bool
    brain_id: str


class Brain(APIModel):
    id: Optional[str] = None
    name_key: str
    pat: Optional[str] = Field(default=None, repr=False)


class BrainLifecycleResponse(APIModel):
    success: bool
    brain_id: str
    operation: Literal["clear", "delete"]
    existed: bool
    cleared_backends: List[str] = Field(default_factory=list)


class IngestionAcceptedResponse(APIModel):
    message: str
    task_id: str


class TaskStateResponse(APIModel):
    status: str
    task_id: Optional[str] = None
    id: Optional[str] = None
    stage: Optional[str] = None
    error: Optional[str] = None
    result: Any = None

    @property
    def identifier(self) -> Optional[str]:
        return self.task_id or self.id

    @property
    def is_terminal(self) -> bool:
        from lumen_brain.config import TERMINAL_TASK_STATUSES

        return self.status.lower() in TERMINAL_TASK_STATUSES


class TaskListResponse(APIModel):
    tasks: List[TaskStateResponse] = Field(default_factory=list)


class CancelIngestionResponse(APIModel):
    task_id: str
    mode: Literal["keep_saved", "rollback"]
    status: Literal["cancelling", "cancelled", "rollback_failed"]


class GraphNode(APIModel):
    uuid: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    properties: JsonDict = Field(default_factory=dict)


class GraphPredicate(APIModel):
    uuid: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    properties: JsonDict = Field(default_factory=dict)


class PartialNode(APIModel):
    uuid: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    labels: Optional[List[str]] = None
    description: Optional[str] = None
    properties: Optional[JsonDict] = None


class PartialPredicate(APIModel):
    name: Optional[str] = None
    description: Optional[str] = None
    properties: Optional[JsonDict] = None


class IngestionTripleSet(APIModel):
    subject: Optional[PartialNode] = None
    subj_event: Optional[PartialPredicate] = None
    event: Optional[PartialNode] = None
    event_obj: Optional[PartialPredicate] = None
    object: PartialNode


class FactVerificationInfo(APIModel):
    state: VerificationState = "unverified"
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None
    verification_source: Optional[str] = None
    note: Optional[str] = None
    fact_id: Optional[str] = None
    kind: Optional[Literal["relationship", "node"]] = None


class FactVerificationHistoryEntry(APIModel):
    id: str
    from_state: VerificationState
    to_state: VerificationState
    verified_by: Optional[str] = None
    verified_at: str
    verification_source: Optional[str] = None
    note: Optional[str] = None


class FactVerificationRecord(APIModel):
    kind: Literal["relationship", "node"]
    fact_id: str
    name: str = ""
    description: str = ""
    verification: FactVerificationInfo
    history: List[FactVerificationHistoryEntry] = Field(default_factory=list)
    subject_uuid: Optional[str] = None
    subject_name: Optional[str] = None
    subject_labels: List[str] = Field(default_factory=list)
    object_uuid: Optional[str] = None
    object_name: Optional[str] = None
    object_labels: List[str] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)


class FactVerificationListResponse(APIModel):
    facts: List[FactVerificationRecord] = Field(default_factory=list)
    total: int = 0


class GetContextTriple(APIModel):
    identified_entity: Optional[str] = None
    triple: Any = None
    source_chunk_ids: Optional[List[str]] = None
    source_session_ids: Optional[List[str]] = None
    open_conflicts: Optional[List[JsonDict]] = None
    verification: Optional[FactVerificationInfo] = None


class GetContextResponse(APIModel):
    text_context: str = ""
    triples: List[GetContextTriple] = Field(default_factory=list)
    historical_context: List[str] = Field(default_factory=list)
    source_passages: List[str] = Field(default_factory=list)
    graph_session_ids: Optional[List[str]] = None
    temporal_conflicts: Optional[List[JsonDict]] = None
    paths: Optional[List[JsonDict]] = None
    topics: Optional[List[JsonDict]] = None
    stage_timings: Optional[JsonDict] = None
    validity_unknown_count: Optional[int] = None
    validity_unknown: Optional[List[JsonDict]] = None


class SearchHitScores(APIModel):
    bm25: Optional[float] = None
    dense: Optional[float] = None
    rrf: Optional[float] = None
    cc: Optional[float] = None
    rerank: Optional[float] = None
    plugin: Optional[Dict[str, float]] = None
    graph: Optional[float] = None
    personalize: Optional[float] = None


class SearchHit(APIModel):
    id: str
    channel: str
    score: float
    scores: SearchHitScores
    snippet: str
    labels: List[str] = Field(default_factory=list)
    extras: Optional[JsonDict] = None
    node_id: Optional[str] = None


class SearchResponse(APIModel):
    hits: List[SearchHit] = Field(default_factory=list)
    stage_timings: Optional[JsonDict] = None
    channel_lists: Optional[Dict[str, List[str]]] = None
    facets: Optional[Dict[str, Dict[str, int]]] = None
    node_ids: List[str] = Field(default_factory=list)
    validity_unknown_count: Optional[int] = None
    validity_unknown: Optional[List[JsonDict]] = None


class RetrieveResponse(APIModel):
    data: List[JsonDict] = Field(default_factory=list)
    observations: List[JsonDict] = Field(default_factory=list)
    relationships: List[JsonDict] = Field(default_factory=list)
    validity_unknown_count: Optional[int] = None
    validity_unknown: Optional[List[JsonDict]] = None


class EntityListResponse(APIModel):
    message: Optional[str] = None
    entities: List[GraphNode] = Field(default_factory=list)
    total: int = 0


class RelationshipListResponse(APIModel):
    message: Optional[str] = None
    relationships: List[JsonDict] = Field(default_factory=list)
    total: int = 0


class GetEntityInfoResponse(APIModel):
    target_node: Optional[GraphNode] = None
    path: Any = None


class GetEntityContextResponse(APIModel):
    neighborhood: List[JsonDict] = Field(default_factory=list)
    target_node: Optional[GraphNode] = None
    text_contexts: List[str] = Field(default_factory=list)
    natural_language_web: List[JsonDict] = Field(default_factory=list)


class GetEntityStatusResponse(APIModel):
    node: Optional[GraphNode] = None
    exists: bool = False
    has_relationships: bool = False
    relationships: List[Any] = Field(default_factory=list)
    observations: List[JsonDict] = Field(default_factory=list)


class RecommendItem(APIModel):
    node: GraphNode
    score: float
    connected_by: List[GraphNode] = Field(default_factory=list)
    channel: str


class RecommendResponse(APIModel):
    target_node: GraphNode
    recommendations: List[RecommendItem] = Field(default_factory=list)


class ConflictRecord(APIModel):
    id: Optional[str] = None
    status: Optional[str] = None
    subject: Optional[str] = None
    predicate: Optional[str] = None
    source: Optional[str] = None
    detected_at: Optional[str] = None


class ConflictItemResponse(APIModel):
    message: Optional[str] = None
    conflict: JsonDict = Field(default_factory=dict)


class ConflictListResponse(APIModel):
    message: Optional[str] = None
    conflicts: List[JsonDict] = Field(default_factory=list)
    count: int = 0
    total: int = 0


class ConflictReportResponse(APIModel):
    message: Optional[str] = None
    summary: JsonDict = Field(default_factory=dict)
    conflicts: List[JsonDict] = Field(default_factory=list)
    markdown: Optional[str] = None


class ConflictScanAcceptedResponse(APIModel):
    message: str
    task_id: str


class ChangelogItemResponse(APIModel):
    message: Optional[str] = None
    changelog: JsonDict = Field(default_factory=dict)


class ChangelogListResponse(APIModel):
    message: Optional[str] = None
    changelogs: List[JsonDict] = Field(default_factory=list)
    count: int = 0
    changes: Optional[List[JsonDict]] = None
    total: Optional[int] = None
    since: Optional[str] = None
    until: Optional[str] = None


class TypeListResponse(APIModel):
    message: Optional[str] = None
    types: List[str] = Field(default_factory=list)
    count: int = 0


class ObservationListResponse(APIModel):
    message: Optional[str] = None
    observations: List[JsonDict] = Field(default_factory=list)
    count: int = 0


class ObservationItemResponse(APIModel):
    message: Optional[str] = None
    observation: JsonDict = Field(default_factory=dict)


class StructuredDataListResponse(APIModel):
    message: Optional[str] = None
    data: List[JsonDict] = Field(default_factory=list)
    count: int = 0
    total: int = 0


class StructuredDataItemResponse(APIModel):
    message: Optional[str] = None
    data: JsonDict = Field(default_factory=dict)


class TextChunkListResponse(APIModel):
    message: Optional[str] = None
    data: List[JsonDict] = Field(default_factory=list)
    total: int = 0


class IngestGroupMeterResponse(APIModel):
    group_tracking: str
    task_count: int = 0
    completed: int = 0
    failed: int = 0
    partial_failed: int = 0
    total_llm_tokens: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cached_tokens: int = 0
    source_chars: int = 0
    source_tokens: int = 0
    stages: JsonDict = Field(default_factory=dict)
    updated_at: Optional[str] = None
    task_ids: List[str] = Field(default_factory=list)


class IngestionCapabilitiesResponse(APIModel):
    progressive: bool = False
    version: str = ""
    concurrency: int = 0


class PurgeIngestionResponse(APIModel):
    digest: Optional[str] = None
    executed: Optional[bool] = None
    passages: Optional[JsonDict] = None
    records: Optional[int] = None
    entities: Optional[JsonDict] = None
    connections: Optional[JsonDict] = None
    unresolved: Optional[int] = None
    ledger_incomplete: bool = False
    ledger_error: Optional[str] = None
    partial: bool = False
    completed: Optional[List[JsonDict]] = None
    error: Optional[str] = None


class NeighborResponse(APIModel):
    count: int = 0
    main_node: Optional[GraphNode] = None
    neighbors: List[JsonDict] = Field(default_factory=list)


MemoryQueryResponse = GetContextResponse
MemoryUpdateResponse = IngestionAcceptedResponse
