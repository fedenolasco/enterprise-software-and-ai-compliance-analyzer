"""Command-line entry point for PostgreSQL vector retrieval."""

from argparse import ArgumentParser

from rich.console import Console
from rich.table import Table

from agent_brain.retrieval.vector import vector_search


def main() -> None:
    """Run a documented local pgvector search over compliance chunks."""

    parser = ArgumentParser(
        description="Search PostgreSQL pgvector compliance chunks with deterministic embeddings."
    )
    parser.add_argument("query", help="Query text to embed and search against document chunks.")
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Maximum number of results to return.",
    )
    args = parser.parse_args()

    results = vector_search(args.query, top_k=args.top_k)

    table = Table(title="PostgreSQL vector retrieval results")
    table.add_column("Rank", justify="right")
    table.add_column("Vendor")
    table.add_column("Software")
    table.add_column("Risk")
    table.add_column("Distance", justify="right")
    table.add_column("Evidence excerpt")

    for rank, result in enumerate(results, start=1):
        table.add_row(
            str(rank),
            result.vendor_name or "Unlinked",
            result.software_name or "Unlinked",
            f"{result.risk_category or 'UNKNOWN'} / {result.risk_severity or 'UNKNOWN'}",
            f"{result.distance:.6f}",
            result.evidence_excerpt[:160],
        )

    Console().print(table)


if __name__ == "__main__":
    main()
