PRAGMA foreign_keys = ON;

CREATE TABLE artist_project (
  artist_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE gig (
  gig_id TEXT PRIMARY KEY,
  artist_id TEXT NOT NULL REFERENCES artist_project(artist_id),
  starts_at TEXT,
  venue TEXT,
  lock_state TEXT NOT NULL DEFAULT 'draft'
    CHECK(lock_state IN ('draft','rehearsal','performance_lock','completed')),
  manifest_hash TEXT
);

CREATE TABLE song (
  song_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  artist_name TEXT,
  tempo_bpm REAL,
  musical_key TEXT
);

CREATE TABLE setlist (
  setlist_id TEXT PRIMARY KEY,
  gig_id TEXT NOT NULL REFERENCES gig(gig_id),
  version INTEGER NOT NULL
);

CREATE TABLE setlist_item (
  item_id TEXT PRIMARY KEY,
  setlist_id TEXT NOT NULL REFERENCES setlist(setlist_id),
  song_id TEXT NOT NULL REFERENCES song(song_id),
  position INTEGER NOT NULL,
  UNIQUE(setlist_id, position)
);

CREATE TABLE section (
  section_id TEXT PRIMARY KEY,
  song_id TEXT NOT NULL REFERENCES song(song_id),
  name TEXT NOT NULL,
  ordinal INTEGER NOT NULL
);

CREATE TABLE tone_preset (
  preset_id TEXT NOT NULL,
  section_id TEXT REFERENCES section(section_id),
  version INTEGER NOT NULL,
  parameter_json TEXT NOT NULL,
  checksum TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(preset_id, version)
);

CREATE TABLE dsp_transaction (
  transaction_id TEXT PRIMARY KEY,
  base_preset_version TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  safe_transaction_hash TEXT,
  compiler_version TEXT NOT NULL,
  validation_policy_version TEXT,
  apply_status TEXT,
  applied_version TEXT,
  rollback_token TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE asset_manifest (
  asset_id TEXT PRIMARY KEY,
  gig_id TEXT NOT NULL REFERENCES gig(gig_id),
  asset_type TEXT NOT NULL,
  local_uri TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  required INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE model_bundle (
  model_id TEXT PRIMARY KEY,
  model_kind TEXT NOT NULL,
  version TEXT NOT NULL,
  checksum TEXT NOT NULL,
  training_data_version TEXT,
  feature_schema_version TEXT,
  metrics_json TEXT NOT NULL,
  device_profile TEXT,
  approval_status TEXT NOT NULL DEFAULT 'draft',
  approved_at TEXT
);

CREATE TABLE performance_event (
  event_id TEXT PRIMARY KEY,
  gig_id TEXT,
  source TEXT NOT NULL,
  topic TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  event_time TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  correlation_id TEXT NOT NULL,
  causation_id TEXT
);

CREATE INDEX idx_event_seq ON performance_event(sequence);
CREATE INDEX idx_event_corr ON performance_event(correlation_id);

CREATE TABLE state_snapshot (
  snapshot_id TEXT PRIMARY KEY,
  gig_id TEXT NOT NULL REFERENCES gig(gig_id),
  event_sequence INTEGER NOT NULL,
  state_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE evaluation_run (
  run_id TEXT PRIMARY KEY,
  model_id TEXT REFERENCES model_bundle(model_id),
  corpus_version TEXT NOT NULL,
  config_hash TEXT NOT NULL,
  started_at TEXT NOT NULL,
  metrics_json TEXT NOT NULL,
  passed INTEGER NOT NULL
);
