import json, sqlite3
from blackstar.contracts.models import PerformanceEvent

class SQLiteEventStore:
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)

    def next_sequence(self) -> int:
        row = self.db.execute("SELECT COALESCE(MAX(sequence),0)+1 FROM performance_event").fetchone()
        return int(row[0])

    def append(self, event: PerformanceEvent) -> None:
        self.db.execute(
            """INSERT INTO performance_event
            (event_id, source, topic, sequence, event_time, schema_version,
             payload_json, idempotency_key, correlation_id, causation_id)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(event.event_id), event.source, event.topic, event.sequence,
                event.event_time.isoformat(), event.schema_version,
                json.dumps(event.payload, separators=(",", ":"), sort_keys=True),
                event.idempotency_key, str(event.correlation_id),
                str(event.causation_id) if event.causation_id else None,
            )
        )
        self.db.commit()
