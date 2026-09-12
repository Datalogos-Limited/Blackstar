# Blackstar AI Performance Platform — Implementation Schema

## 1. Command authority chain
Speech audio is interpreted into a typed `BlackstarIntent`. That object contains semantic tone deltas, locks, context, confidence, requested action, source and model identity. The intent model has no DSP write authority.

`DeterministicToneCompiler` consumes the intent, current tone and ontology version and emits only a `ProposedDSPTransaction`. Compilation must be pure, reproducible and side-effect free.

`DefaultDenyValidator` is the policy authority. It verifies base-version concurrency, parameter allow-lists, value bounds, locks, routing restrictions and Performance Lock policy. Only an accepted transaction with a deterministic safe hash may reach the DSP bridge.

`DSPBridge` stages and applies a transaction atomically. It returns an immutable applied version, ACK/NACK, measured latency and rollback token.

## 2. Primary bounded contexts
### Speech
Wake phrase, VAD, local STT, transcript confidence and replay providers. No control authority.

### Intent
Model-specific inference hidden behind a stable adapter. Output must validate against `BlackstarIntent v1`.

### Tone Ontology
Semantic musician language mapped to explicit engineering dimensions, parameters, units, ranges, ownership and lock policy.

### Tone Compiler
Deterministic semantic-to-DSP mapping. No network, model or database calls.

### Validator
Default-deny safety policy and show-state authority.

### DSP Bridge
Hardware abstraction for atomic DSP state transitions, telemetry and rollback.

### Performance Domain
Artist/project -> gig -> setlist -> song -> section -> tone preset. Song and section are contextual control objects rather than isolated preset files.

### Event Store
Append-only evidence for all decisions and actuations. Supports replay, snapshots, undo and forensic reconstruction.

## 3. Required contract versions
- `BlackstarIntent v1`
- `ProposedDSPTransaction v1`
- `ValidationResult v1`
- `DSPApplyResult v1`
- `PerformanceEvent v1`

Within v1, compatibility changes should be additive and optional. Unknown required semantics are rejected.

## 4. Performance Lock
Performance Lock is a central policy state. Entering lock must perform manifest preflight for required presets, models, IRs and other show assets. Checksums must match. While locked:
- no model swaps;
- no required asset downloads;
- no structural preset edits;
- no ontology mutation;
- only explicitly performance-mutable parameters may change;
- unknown DSP parameters/routes are denied;
- cloud is never required for a live command.

## 5. Event topics
Suggested v1 topics:
- `blackstar.speech.accepted`
- `blackstar.intent.created`
- `blackstar.transaction.proposed`
- `blackstar.validation`
- `blackstar.dsp.apply`
- `blackstar.dsp.rollback`
- `blackstar.performance.lock.entered`
- `blackstar.performance.lock.failed`
- `blackstar.fastpath.command`
- `blackstar.system.degraded`
- `blackstar.system.recovered`

Every event carries sequence, timestamp, schema version, idempotency key and correlation ID. Consumers must detect gaps and out-of-order delivery.

## 6. Test strategy
Unit tests:
- ontology mapping;
- compiler determinism;
- range/lock/routing policy;
- safe hash reproducibility.

Golden tests:
- fixed musician utterance + fixed context -> exact structured intent;
- fixed intent + preset + ontology -> exact DSP transaction.

Contract tests:
- JSON schema compatibility;
- unknown required field rejection;
- additive optional field compatibility.

Integration tests:
- text -> intent -> compile -> validate -> simulated DSP;
- stale base preset rejection;
- rollback;
- Performance Lock asset preflight.

Failure injection:
- intent timeout;
- model unavailable;
- DSP NACK;
- watchdog/degraded mode;
- corrupted checksum;
- duplicate event/idempotency key;
- out-of-order event sequence.

Soak/performance tests:
- repeated commands over two-hour show;
- p95 intent/compile/validation latency;
- DSP apply latency;
- CPU/GPU/thermal contention;
- no impact from AI workload on the real-time audio callback.

## 7. Production split
The repository intentionally treats Python as the reference schema/orchestration language, not as the real-time DSP implementation. A production system should preserve the contracts while moving:
- DSP callback and transaction engine -> C/C++/existing Blackstar DSP environment;
- MCU safety/fast path -> embedded C/C++;
- host application/orchestration -> suitable native/system language;
- ML/STT adapters -> hardware-appropriate local inference runtime.

The contract boundary, deterministic authority model and event evidence should remain unchanged across implementations.
