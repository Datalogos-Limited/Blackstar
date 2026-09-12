from __future__ import annotations
import hashlib, json
from typing import Any, Mapping
from blackstar.contracts.models import (
    PerformanceMode, ProposedDSPTransaction, ValidationResult, ValidationViolation
)

class DefaultDenyValidator:
    VERSION = "policy-v1"

    def __init__(self, ontology: Mapping[str, Any]):
        self.ontology = ontology

    def validate(
        self,
        tx: ProposedDSPTransaction,
        policy: Mapping[str, Any],
    ) -> ValidationResult:
        violations: list[ValidationViolation] = []
        current_version = str(policy["current_preset_version"])

        if tx.base_preset_version != current_version:
            violations.append(ValidationViolation(
                "BASE_VERSION_MISMATCH",
                "Transaction was compiled against a stale preset version."
            ))

        mode = PerformanceMode(policy.get("performance_mode", "edit"))
        forbidden_routes = set(policy.get("forbidden_routes", []))
        locked = set(policy.get("locked_parameters", []))

        for name, value in tx.parameter_changes.items():
            rule = self.ontology["parameters"].get(name)
            if rule is None:
                violations.append(ValidationViolation(
                    "UNKNOWN_PARAMETER", f"Parameter {name} is not allow-listed.", name
                ))
                continue

            if name in locked:
                violations.append(ValidationViolation(
                    "LOCKED_PARAMETER", f"Parameter {name} is locked.", name
                ))

            if not (float(rule["min"]) <= float(value) <= float(rule["max"])):
                violations.append(ValidationViolation(
                    "OUT_OF_RANGE", f"{name} outside allowed range.", name
                ))

            if mode == PerformanceMode.PERFORMANCE_LOCK and not rule.get("performance_mutable", False):
                violations.append(ValidationViolation(
                    "PERFORMANCE_LOCK_DENY",
                    f"{name} may not be changed during Performance Lock.",
                    name
                ))

        for route in tx.routing_changes:
            if route in forbidden_routes:
                violations.append(ValidationViolation(
                    "PROHIBITED_ROUTING", f"Routing change {route} is prohibited.", route
                ))

        accepted = not violations
        digest = None
        if accepted:
            canonical = json.dumps({
                "transaction_id": str(tx.transaction_id),
                "base_preset_version": tx.base_preset_version,
                "parameter_changes": dict(sorted(tx.parameter_changes.items())),
                "routing_changes": tx.routing_changes,
                "monitor_changes": tx.monitor_changes,
                "compiler_version": tx.compiler_version,
            }, separators=(",", ":"), sort_keys=True).encode()
            digest = hashlib.sha256(canonical).hexdigest()

        return ValidationResult(
            accepted=accepted,
            violations=tuple(violations),
            confirmation_required=bool(policy.get("confirmation_required", False)),
            safe_transaction_hash=digest,
            policy_version=self.VERSION,
        )
