from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4
from blackstar.contracts.models import PerformanceEvent, ApplyStatus
from blackstar.contracts.protocols import IntentAdapter, ToneCompiler, Validator, DSPBridge, EventStore

class CommandService:
    def __init__(self, intent: IntentAdapter, compiler: ToneCompiler, validator: Validator,
                 dsp: DSPBridge, events: EventStore, ontology_version: str):
        self.intent = intent
        self.compiler = compiler
        self.validator = validator
        self.dsp = dsp
        self.events = events
        self.ontology_version = ontology_version

    def execute(self, transcript: str, context: Mapping[str, Any], policy: Mapping[str, Any]):
        correlation_id = uuid4()
        blackstar_intent = self.intent.interpret(transcript, context)

        tx = self.compiler.compile(
            blackstar_intent,
            self.dsp.current_tone(),
            self.ontology_version,
        )

        effective_policy = dict(policy)
        effective_policy["current_preset_version"] = self.dsp.current_preset_version()
        validation = self.validator.validate(tx, effective_policy)

        self._record("blackstar.validation", {
            "intent_id": str(blackstar_intent.intent_id),
            "transaction_id": str(tx.transaction_id),
            "accepted": validation.accepted,
            "violations": [v.code for v in validation.violations],
            "safe_transaction_hash": validation.safe_transaction_hash,
        }, correlation_id)

        if not validation.accepted:
            return validation, None

        result = self.dsp.apply_atomic(tx)

        self._record("blackstar.dsp.apply", {
            "transaction_id": str(tx.transaction_id),
            "status": result.status.value,
            "applied_version": result.applied_version,
            "latency_us": result.latency_us,
            "rollback_token": result.rollback_token,
        }, correlation_id)

        return validation, result

    def _record(self, topic: str, payload: Mapping[str, Any], correlation_id):
        event = PerformanceEvent(
            event_id=uuid4(),
            source="blackstar-command-service",
            topic=topic,
            sequence=self.events.next_sequence(),
            event_time=datetime.now(timezone.utc),
            schema_version="1.0",
            payload=dict(payload),
            idempotency_key=str(uuid4()),
            correlation_id=correlation_id,
        )
        self.events.append(event)
