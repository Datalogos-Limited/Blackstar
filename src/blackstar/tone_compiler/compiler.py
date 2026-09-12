from __future__ import annotations
from uuid import uuid4
from typing import Any, Mapping
from blackstar.contracts.models import BlackstarIntent, DeltaOperation, ProposedDSPTransaction

class DeterministicToneCompiler:
    """Pure intent -> proposed transaction compiler. No I/O and no model calls."""

    VERSION = "v1"

    def __init__(self, ontology: Mapping[str, Any]):
        self.ontology = ontology

    def compile(
        self,
        intent: BlackstarIntent,
        current_tone: Mapping[str, float],
        ontology_version: str,
    ) -> ProposedDSPTransaction:
        changes: dict[str, float] = {}

        for delta in intent.semantic_deltas:
            dim = self.ontology["dimensions"].get(delta.dimension)
            if not dim:
                # Unknown semantics are intentionally not guessed.
                continue

            parameters = dim["parameters"]
            # v1 uses a deterministic distribution rule. Production rules can
            # become richer while remaining table-driven and golden-testable.
            per_parameter = delta.amount / max(len(parameters), 1)

            for parameter in parameters:
                if parameter in intent.locks:
                    continue
                current = float(current_tone.get(parameter, 0.0))
                if delta.operation == DeltaOperation.INCREASE:
                    proposed = current + per_parameter
                elif delta.operation == DeltaOperation.DECREASE:
                    proposed = current - per_parameter
                else:
                    proposed = delta.amount
                changes[parameter] = proposed

        return ProposedDSPTransaction(
            transaction_id=uuid4(),
            base_preset_version=str(intent.context["base_preset_version"]),
            parameter_changes=changes,
            safety_metadata={
                "intent_id": str(intent.intent_id),
                "intent_confidence": intent.confidence,
                "ontology_version": ontology_version,
                "locked_attributes": list(intent.locks),
            },
            compiler_version=self.VERSION,
        )
