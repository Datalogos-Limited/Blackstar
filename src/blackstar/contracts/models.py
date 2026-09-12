from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Sequence
from uuid import UUID, uuid4

class RequestedAction(str, Enum):
    MODIFY_TONE = "modify_tone"
    LOAD_PRESET = "load_preset"
    LOAD_SONG = "load_song"
    NEXT_SONG = "next_song"
    PREVIOUS_SONG = "previous_song"
    CHANGE_MONITOR = "change_monitor"
    UNDO = "undo"
    RESTORE = "restore"
    NO_OP = "no_op"

class DeltaOperation(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    SET = "set"

class ApplyStatus(str, Enum):
    ACK = "ack"
    NACK = "nack"

class PerformanceMode(str, Enum):
    EDIT = "edit"
    REHEARSAL = "rehearsal"
    PERFORMANCE_LOCK = "performance_lock"
    DEGRADED = "degraded"

@dataclass(frozen=True)
class SemanticDelta:
    dimension: str
    operation: DeltaOperation
    amount: float
    unit: str | None = None
    target: str | None = None

@dataclass(frozen=True)
class BlackstarIntent:
    intent_id: UUID
    timestamp: datetime
    semantic_deltas: Sequence[SemanticDelta]
    locks: Sequence[str]
    context: Mapping[str, Any]
    confidence: float
    requested_action: RequestedAction
    source: str
    model_id: str
    schema_version: str = "1.0"

    @staticmethod
    def create(*, semantic_deltas, locks, context, confidence,
               requested_action, source, model_id) -> "BlackstarIntent":
        return BlackstarIntent(
            intent_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            semantic_deltas=tuple(semantic_deltas),
            locks=tuple(locks),
            context=dict(context),
            confidence=float(confidence),
            requested_action=requested_action,
            source=source,
            model_id=model_id,
        )

@dataclass(frozen=True)
class ProposedDSPTransaction:
    transaction_id: UUID
    base_preset_version: str
    parameter_changes: Mapping[str, float]
    routing_changes: Mapping[str, Any] = field(default_factory=dict)
    monitor_changes: Mapping[str, Any] = field(default_factory=dict)
    safety_metadata: Mapping[str, Any] = field(default_factory=dict)
    compiler_version: str = "v1"
    schema_version: str = "1.0"

@dataclass(frozen=True)
class ValidationViolation:
    code: str
    message: str
    field: str | None = None

@dataclass(frozen=True)
class ValidationResult:
    accepted: bool
    violations: Sequence[ValidationViolation]
    confirmation_required: bool
    safe_transaction_hash: str | None
    policy_version: str

@dataclass(frozen=True)
class DSPApplyResult:
    transaction_id: UUID
    applied_version: str | None
    status: ApplyStatus
    latency_us: int
    rollback_token: str | None
    error_code: str | None = None
    schema_version: str = "1.0"

@dataclass(frozen=True)
class PerformanceEvent:
    event_id: UUID
    source: str
    topic: str
    sequence: int
    event_time: datetime
    schema_version: str
    payload: Mapping[str, Any]
    idempotency_key: str
    correlation_id: UUID
    causation_id: UUID | None = None
