"""PostgreSQL persistence helpers for governance audit events."""

from __future__ import annotations

from collections.abc import Sequence
from json import dumps

from psycopg import Connection
from psycopg.types.json import Jsonb

from agent_brain.governance.observability import GovernanceAuditEvent


def persist_governance_audit_events(
    database_url: str,
    events: Sequence[GovernanceAuditEvent],
) -> int:
    """Persist AuditEvent-compatible governance events to local PostgreSQL."""

    if not events:
        return 0
    with Connection.connect(database_url) as connection:
        return persist_governance_audit_events_with_connection(connection, events)


def persist_governance_audit_events_with_connection(
    connection: Connection[object],
    events: Sequence[GovernanceAuditEvent],
) -> int:
    """Persist events using an existing psycopg connection for testability."""

    with connection.cursor() as cursor:
        for event in events:
            payload = event.to_prisma_insert()
            cursor.execute(
                """
                INSERT INTO "AuditEvent"
                    ("eventType", "status", "actor", "traceId", "message", "detail")
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    payload["eventType"],
                    payload["status"],
                    payload["actor"],
                    payload["traceId"],
                    payload["message"],
                    Jsonb(payload["detail"], dumps=dumps),
                ),
            )
    connection.commit()
    return len(events)
