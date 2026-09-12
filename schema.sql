-- POC baseline: SQLite; portable to PostgreSQL if cloud/library services are added.
PRAGMA foreign_keys = ON;

CREATE TABLE artist_project (
  artist_id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE gig (
  gig_id TEXT PRIMARY KEY, artist_id TEXT NOT NULL REFERENCES artist_project(artist_id),
  starts_at TEXT, venue TEXT, lock_state TEXT NOT NULL DEFAULT 'draft', manifest_hash TEXT
);
CREATE TABLE song (
  song_id TEXT PRIMARY KEY, title TEXT NOT NULL, artist_name TEXT, tempo_bpm REAL, musical_key TEXT
);
CREATE TABLE setlist (
  setlist_id TEXT PRIMARY KEY, gig_id TEXT NOT NULL REFERENCES gig(gig_id), version INTEGER NOT NULL
);
CREATE TABLE setlist_item (
  item_id TEXT PRIMARY KEY, setlist_id TEXT NOT NULL REFERENCES setlist(setlist_id),
  song_id TEXT NOT NULL REFERENCES song(song_id), position INTEGER NOT NULL,
  UNIQUE(setlist_id, position)
);
CREATE TABLE section (
  section_id TEXT PRIMARY KEY, song_id TEXT NOT NULL REFERENCES song(song_id),
  name TEXT NOT NULL, ordinal INTEGER NOT NULL
);
CREATE TABLE tone_preset (
  preset_id TEXT PRIMARY KEY, section_id TEXT REFERENCES section(section_id), version INTEGER NOT NULL,
  parameter_json TEXT NOT NULL, checksum TEXT NOT NULL
);
CREATE TABLE song_map (
  songmap_id TEXT PRIMARY KEY, song_id TEXT NOT NULL REFERENCES song(song_id), version INTEGER NOT NULL,
  lifecycle_state TEXT NOT NULL CHECK(lifecycle_state IN ('draft','approved','locked')),
  checksum TEXT NOT NULL, UNIQUE(song_id, version)
);
CREATE TABLE song_line (
  line_id TEXT PRIMARY KEY, songmap_id TEXT NOT NULL REFERENCES song_map(songmap_id),
  section_id TEXT NOT NULL REFERENCES section(section_id), ordinal INTEGER NOT NULL,
  lyric_ref TEXT NOT NULL, canonical_tokens_json TEXT, UNIQUE(songmap_id, ordinal)
);
CREATE TABLE line_variant (
  variant_id TEXT PRIMARY KEY, line_id TEXT NOT NULL REFERENCES song_line(line_id),
  variant_type TEXT NOT NULL, token_form_json TEXT NOT NULL
);
CREATE TABLE song_map_edge (
  from_line_id TEXT NOT NULL REFERENCES song_line(line_id),
  to_line_id TEXT NOT NULL REFERENCES song_line(line_id), edge_type TEXT NOT NULL,
  transition_weight REAL NOT NULL DEFAULT 1.0, PRIMARY KEY(from_line_id,to_line_id,edge_type)
);
CREATE TABLE asset_manifest (
  asset_id TEXT PRIMARY KEY, gig_id TEXT NOT NULL REFERENCES gig(gig_id), asset_type TEXT NOT NULL,
  local_uri TEXT NOT NULL, sha256 TEXT NOT NULL, required INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE performance_event (
  event_id TEXT PRIMARY KEY, gig_id TEXT REFERENCES gig(gig_id), source TEXT NOT NULL,
  topic TEXT NOT NULL, sequence INTEGER NOT NULL, event_time TEXT NOT NULL,
  schema_version TEXT NOT NULL, payload_json TEXT NOT NULL, idempotency_key TEXT NOT NULL UNIQUE
);
CREATE INDEX idx_event_gig_seq ON performance_event(gig_id, sequence);
CREATE TABLE state_snapshot (
  snapshot_id TEXT PRIMARY KEY, gig_id TEXT NOT NULL REFERENCES gig(gig_id),
  event_sequence INTEGER NOT NULL, state_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE model_bundle (
  model_id TEXT PRIMARY KEY, model_kind TEXT NOT NULL, version TEXT NOT NULL,
  checksum TEXT NOT NULL, metrics_json TEXT NOT NULL, approved_at TEXT
);
CREATE TABLE evaluation_run (
  run_id TEXT PRIMARY KEY, model_id TEXT REFERENCES model_bundle(model_id), corpus_version TEXT NOT NULL,
  config_hash TEXT NOT NULL, started_at TEXT NOT NULL, metrics_json TEXT NOT NULL, passed INTEGER NOT NULL
);
