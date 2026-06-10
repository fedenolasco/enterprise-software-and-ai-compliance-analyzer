from agent_brain.governance.audit import persist_governance_audit_events_with_connection
from agent_brain.governance.observability import build_governance_audit_event
from agent_brain.orchestration.state import create_initial_state


class FakeCursor:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple[object, ...]]] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def execute(self, sql: str, params: tuple[object, ...]) -> None:
        self.executed.append((sql, params))


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_instance = FakeCursor()
        self.committed = False

    def cursor(self) -> FakeCursor:
        return self.cursor_instance

    def commit(self) -> None:
        self.committed = True


def test_persist_governance_audit_events_with_connection_inserts_rows() -> None:
    connection = FakeConnection()
    event = build_governance_audit_event(
        create_initial_state("Summarize posture", trace_id="trace-audit"),
        message="Audit persistence test.",
    )

    inserted = persist_governance_audit_events_with_connection(connection, [event])  # type: ignore[arg-type]

    assert inserted == 1
    assert connection.committed
    sql, params = connection.cursor_instance.executed[0]
    assert 'INSERT INTO "AuditEvent"' in sql
    assert params[0] == "AGENT_RECOMMENDATION"
    assert params[3] == "trace-audit"
