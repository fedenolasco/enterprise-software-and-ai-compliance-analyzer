"""Reset Neo4j demo graph state for repeatable local demonstrations.

This script deletes only the graph labels and relationships created by the
agent-brain projection workflow. It leaves the Neo4j service, database, users,
and constraints available so `python -m agent_brain.cli.project_graph` can
rebuild graph state from the current PostgreSQL fixture load.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from os import getenv
from pathlib import Path
import sys
from typing import Final

from neo4j import Driver, GraphDatabase, Session

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent_brain.config import AgentBrainSettings, get_settings


DEMO_LABELS: tuple[str, ...] = (
    "DocumentChunk",
    "ComplianceDocument",
    "Subscription",
    "Software",
    "Vendor",
)

DEMO_RELATIONSHIP_TYPES: tuple[str, ...] = (
    "EVIDENCES_RISK",
    "HAS_CHUNK",
    "HAS_POLICY",
    "HAS_SUBSCRIPTION",
    "SELLS",
)

COUNT_DEMO_NODES_QUERY: Final = """
MATCH (node)
WHERE any(label IN labels(node) WHERE label IN $labels)
RETURN count(node) AS count
""".strip()

COUNT_DEMO_RELATIONSHIPS_QUERY: Final = """
MATCH ()-[relationship]->()
WHERE type(relationship) IN $relationship_types
RETURN count(relationship) AS count
""".strip()


@dataclass(frozen=True)
class GraphResetSummary:
    """Counts returned after Neo4j demo graph reset."""

    nodes_deleted: int
    relationships_deleted: int


def reset_graph(settings: AgentBrainSettings | None = None) -> GraphResetSummary:
    """Delete demo-owned Neo4j nodes and relationships."""

    active_settings = settings or get_settings()
    driver = GraphDatabase.driver(
        active_settings.neo4j_uri,
        auth=(active_settings.neo4j_username, active_settings.neo4j_password),
    )
    try:
        return reset_graph_with_driver(driver)
    finally:
        driver.close()


def reset_graph_with_driver(driver: Driver) -> GraphResetSummary:
    """Delete demo graph state using an existing Neo4j driver."""

    with driver.session() as session:
        before_nodes = _count_demo_nodes(session)
        before_relationships = _count_demo_relationships(session)

        session.run(
            """
            MATCH (node)
            WHERE any(label IN labels(node) WHERE label IN $labels)
            DETACH DELETE node
            """.strip(),
            labels=list(DEMO_LABELS),
        )

        after_nodes = _count_demo_nodes(session)
        after_relationships = _count_demo_relationships(session)

    return GraphResetSummary(
        nodes_deleted=before_nodes - after_nodes,
        relationships_deleted=before_relationships - after_relationships,
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Delete Neo4j demo graph nodes and relationships created by the "
            "agent-brain projection workflow."
        )
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm deletion without an interactive prompt.",
    )
    return parser


def main() -> None:
    """Run the Neo4j demo graph reset command."""

    args = build_parser().parse_args()
    if not _is_confirmed(args.yes):
        raise SystemExit(
            "Refusing to reset Neo4j demo graph without confirmation. "
            "Re-run with --yes or set RESET_GRAPH=true."
        )

    summary = reset_graph()
    print(
        "Reset Neo4j demo graph: "
        f"deleted {summary.nodes_deleted} nodes and "
        f"{summary.relationships_deleted} relationships."
    )


def _count_demo_nodes(session: Session) -> int:
    record = session.run(COUNT_DEMO_NODES_QUERY, labels=list(DEMO_LABELS)).single(strict=True)
    return int(record.data()["count"])


def _count_demo_relationships(session: Session) -> int:
    record = session.run(
        COUNT_DEMO_RELATIONSHIPS_QUERY,
        relationship_types=list(DEMO_RELATIONSHIP_TYPES),
    ).single(strict=True)
    return int(record.data()["count"])


def _is_confirmed(argument_confirmed: bool) -> bool:
    if argument_confirmed:
        return True
    return getenv("RESET_GRAPH", "").strip().lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    main()
