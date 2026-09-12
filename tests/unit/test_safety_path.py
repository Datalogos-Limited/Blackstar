import json
from pathlib import Path
from blackstar.contracts.models import (
    BlackstarIntent, SemanticDelta, DeltaOperation, RequestedAction, PerformanceMode
)
from blackstar.tone_compiler.compiler import DeterministicToneCompiler
from blackstar.validator.default_deny import DefaultDenyValidator

def ontology():
    path = Path(__file__).parents[2] / "config" / "tone_ontology_v0.1.json"
    return json.loads(path.read_text())

def test_compiler_is_deterministic():
    o = ontology()
    c = DeterministicToneCompiler(o)
    intent = BlackstarIntent.create(
        semantic_deltas=[SemanticDelta("spectrum.warmth", DeltaOperation.INCREASE, 0.2)],
        locks=[],
        context={"base_preset_version":"preset-1"},
        confidence=0.95,
        requested_action=RequestedAction.MODIFY_TONE,
        source="test",
        model_id="stub-v1"
    )
    tone = {"bass":0.5,"mid":0.5,"treble":0.5,"presence":0.5}
    a = c.compile(intent, tone, "0.1")
    b = c.compile(intent, tone, "0.1")
    assert a.parameter_changes == b.parameter_changes

def test_validator_default_denies_unknown_parameter():
    from uuid import uuid4
    from blackstar.contracts.models import ProposedDSPTransaction
    v = DefaultDenyValidator(ontology())
    tx = ProposedDSPTransaction(uuid4(), "preset-1", {"evil_parameter": 1.0})
    result = v.validate(tx, {
        "current_preset_version":"preset-1",
        "performance_mode":PerformanceMode.PERFORMANCE_LOCK.value
    })
    assert result.accepted is False
    assert any(x.code == "UNKNOWN_PARAMETER" for x in result.violations)
