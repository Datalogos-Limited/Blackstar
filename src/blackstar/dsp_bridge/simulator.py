from __future__ import annotations
from time import perf_counter_ns
from uuid import uuid4
from blackstar.contracts.models import ApplyStatus, DSPApplyResult, ProposedDSPTransaction

class SimulatedDSPBridge:
    """POC bridge. Replace internals with hardware IPC/SPI/shared-memory adapter."""

    def __init__(self, initial_tone: dict[str, float], version: str = "preset-1"):
        self._tone = dict(initial_tone)
        self._version = version
        self._history: dict[str, tuple[str, dict[str, float]]] = {}

    def current_preset_version(self) -> str:
        return self._version

    def current_tone(self) -> dict[str, float]:
        return dict(self._tone)

    def apply_atomic(self, tx: ProposedDSPTransaction) -> DSPApplyResult:
        start = perf_counter_ns()
        if tx.base_preset_version != self._version:
            return DSPApplyResult(
                transaction_id=tx.transaction_id,
                applied_version=None,
                status=ApplyStatus.NACK,
                latency_us=(perf_counter_ns() - start)//1000,
                rollback_token=None,
                error_code="BASE_VERSION_MISMATCH",
            )

        rollback_token = str(uuid4())
        self._history[rollback_token] = (self._version, dict(self._tone))

        # Hardware implementation must stage then commit atomically.
        staged = dict(self._tone)
        staged.update(tx.parameter_changes)
        self._tone = staged
        self._version = f"{self._version}+1"

        return DSPApplyResult(
            transaction_id=tx.transaction_id,
            applied_version=self._version,
            status=ApplyStatus.ACK,
            latency_us=(perf_counter_ns() - start)//1000,
            rollback_token=rollback_token,
        )

    def rollback(self, rollback_token: str) -> DSPApplyResult:
        start = perf_counter_ns()
        old_version, old_tone = self._history.pop(rollback_token)
        self._version, self._tone = old_version, old_tone
        return DSPApplyResult(
            transaction_id=uuid4(),
            applied_version=self._version,
            status=ApplyStatus.ACK,
            latency_us=(perf_counter_ns() - start)//1000,
            rollback_token=None,
        )
