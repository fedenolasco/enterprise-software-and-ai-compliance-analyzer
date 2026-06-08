"""Validate that the Python scaffold can load local configuration."""

from rich.console import Console
from rich.table import Table

from agent_brain.config import get_settings


def build_settings_table() -> Table:
    """Build a redacted settings summary table for local validation output."""

    settings = get_settings()
    table = Table(title="agent-brain scaffold validation")
    table.add_column("Setting")
    table.add_column("Value")
    table.add_row("database_url", settings.database_url.split("?")[0])
    table.add_row("neo4j_uri", settings.neo4j_uri)
    table.add_row("neo4j_username", settings.neo4j_username)
    table.add_row("neo4j_password", "***redacted***")
    table.add_row("embedding_dimension", str(settings.embedding_dimension))
    table.add_row("vector_top_k", str(settings.vector_top_k))
    table.add_row("graph_result_limit", str(settings.graph_result_limit))
    return table


def main() -> None:
    """Run the scaffold validation command."""

    console = Console()
    console.print(build_settings_table())
    console.print("[green]agent-brain scaffold is importable and configured.[/green]")


if __name__ == "__main__":
    main()
