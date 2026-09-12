# Blackstar AI Performance Platform — Code Schema v0.1

This scaffold converts the existing Blackstar architecture baseline into a build-ready code structure.

## Core engineering rule

Probabilistic components may interpret musician language or evidence, but they do not own live DSP state.
The live command path is:

`Speech -> IntentAdapter -> BlackstarIntent -> ToneCompiler -> ProposedDSPTransaction -> Validator -> DSPBridge`

Only an accepted ValidationResult may reach `DSPBridge.apply_atomic()`.

## Runtime domains

- **AI host (M5/M5 Pro reference)**: speech, intent adapter, ontology, compiler, validator, orchestration, event store.
- **DSP**: real-time audio processing and atomic preset/parameter application.
- **Control MCU**: fast footswitch/MIDI path, watchdog, mute/recovery, safe boot.
- **Cloud**: optional enrichment/sync only; never required for a live show action.

## Repository structure

- `contracts/` — stable, versioned DTOs and enums
- `speech/` — wake/VAD/STT adapters
- `intent/` — model-agnostic intent interpretation
- `tone_ontology/` — semantic dimensions, parameter mappings, units, constraints and locks
- `tone_compiler/` — pure deterministic intent-to-DSP compiler
- `validator/` — default-deny policy and Performance Lock authority
- `dsp_bridge/` — simulator and hardware adapter with atomic apply/rollback
- `performance_domain/` — artist/gig/setlist/song/section and performance state
- `event_store/` — append-only evidence and snapshots
- `orchestration/` — end-to-end command service
- `security/` — manifest/checksum/preflight controls
- `observability/` — trace records and latency evidence
- `api/` — local control API boundary
- `schemas/json/` — external JSON contract definitions
- `db/migrations/` — local SQLite baseline
- `tests/` — unit, contract, integration, replay and golden tests

## Non-negotiable invariants

1. No generative AI in the real-time audio callback.
2. Intent model output must validate against `BlackstarIntent`.
3. Compiler is pure and deterministic.
4. Validator is default-deny for unknown parameters and prohibited routing.
5. DSP updates are atomic, idempotent and based on an immutable base preset version.
6. Performance Lock freezes models, presets, IRs and other show-critical assets.
7. Every live action is traceable through correlation IDs and append-only events.
8. AI/network failure must not interrupt core performance.
9. Physical controls and fast-path MCU commands remain independently usable.
10. Rollback must be available for every successful DSP transaction.

## Suggested production languages

Python is suitable for contracts, orchestration, POC services, test harnesses and ML adapters.
Production DSP/MCU should remain in appropriate real-time embedded languages.
