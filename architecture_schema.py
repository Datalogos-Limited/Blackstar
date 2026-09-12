from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, Sequence, Mapping, Any
from uuid import UUID
from datetime import datetime

class TrackingState(str, Enum):
    TRACKING = "tracking"
    UNCERTAIN = "uncertain"
    LOST = "lost"
    MANUAL = "manual"

@dataclass(frozen=True)
class SemanticDelta:
    dimension: str       # gain, spectrum, dynamics, space, monitor, etc.
    operation: str       # increase/decrease/set
    amount: float
    unit: str | None = None

@dataclass(frozen=True)
class BlackstarIntent:
    intent_id: UUID
    timestamp: datetime
    semantic_deltas: Sequence[SemanticDelta]
    locks: Sequence[str]
    context: Mapping[str, Any]
    confidence: float
    requested_action: str
    source: str
    model_id: str

@dataclass(frozen=True)
class ProposedDSPTransaction:
    transaction_id: UUID
    base_preset_version: str
    parameter_changes: Mapping[str, float]
    routing_changes: Mapping[str, Any] = field(default_factory=dict)
    monitor_changes: Mapping[str, Any] = field(default_factory=dict)
    safety_metadata: Mapping[str, Any] = field(default_factory=dict)
    compiler_version: str = "v1"

@dataclass(frozen=True)
class ValidationResult:
    accepted: bool
    violations: Sequence[str]
    confirmation_required: bool
    safe_transaction_hash: str | None

class IntentAdapter(Protocol):
    def interpret(self, transcript: str, context: Mapping[str, Any]) -> BlackstarIntent: ...

class ToneCompiler(Protocol):
    def compile(self, intent: BlackstarIntent, current_tone: Mapping[str, float],
                ontology_version: str) -> ProposedDSPTransaction: ...

class Validator(Protocol):
    def validate(self, tx: ProposedDSPTransaction, policy: Mapping[str, Any]) -> ValidationResult: ...

class DSPBridge(Protocol):
    def apply_atomic(self, tx: ProposedDSPTransaction) -> Mapping[str, Any]: ...

@dataclass(frozen=True)
class FeatureFrame:
    timestamp_ms: int
    partial_tokens: Sequence[str]
    token_confidence: Sequence[float]
    phonetic_vector: Sequence[float]
    acoustic_vector: Sequence[float]

@dataclass(frozen=True)
class PositionHypothesis:
    song_id: UUID
    line_id: UUID
    section_id: UUID
    confidence: float
    runner_up_margin: float
    evidence_scores: Mapping[str, float]
    state: TrackingState
    timestamp_ms: int

@dataclass(frozen=True)
class PositionDecision:
    action: str           # advance/hold/recover/manual
    committed_line_id: UUID
    reason_code: str
    confidence: float
    timestamp_ms: int

class CandidateScorer(Protocol):
    def score(self, frame: FeatureFrame, candidate: Mapping[str, Any], context: Mapping[str, Any]) -> Mapping[str, float]: ...

class PositionCore(Protocol):
    def update(self, frame: FeatureFrame) -> PositionDecision: ...

class PerformanceEventBus(Protocol):
    def publish(self, topic: str, payload: Mapping[str, Any], idempotency_key: str) -> None: ...
