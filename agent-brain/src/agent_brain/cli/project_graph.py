"""Command-line entry point for Neo4j graph projection."""

from rich.console import Console

from agent_brain.graph.projection import project_graph


def main() -> None:
    """Project validated PostgreSQL data into the local Neo4j graph."""

    summary = project_graph()
    Console().print(
        "[green]Projected graph context:[/green] "
        f"{summary.vendors} vendors, "
        f"{summary.software} software products, "
        f"{summary.subscriptions} subscriptions, "
        f"{summary.documents} documents, "
        f"{summary.chunks} chunks from {summary.rows} source rows."
    )


if __name__ == "__main__":
    main()
