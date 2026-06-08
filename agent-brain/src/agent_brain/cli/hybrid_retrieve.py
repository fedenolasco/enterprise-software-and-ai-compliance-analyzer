"""Command-line entry point for hybrid graph and vector retrieval."""

from argparse import ArgumentParser

from rich.console import Console
from rich.table import Table

from agent_brain.retrieval.hybrid import explain_result, hybrid_retrieve


def main() -> None:
    """Run hybrid retrieval and print merged risk-to-cost context rows."""

    parser = ArgumentParser(
        description="Combine PostgreSQL vector evidence with Neo4j graph risk-to-cost context."
    )
    parser.add_argument("query", help="Query text used for PostgreSQL vector retrieval.")
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Maximum vector results to retrieve.",
    )
    parser.add_argument(
        "--graph-limit",
        type=int,
        default=None,
        help="Maximum graph rows to traverse.",
    )
    args = parser.parse_args()

    results = hybrid_retrieve(args.query, top_k=args.top_k, graph_limit=args.graph_limit)

    table = Table(title="Hybrid risk-to-cost retrieval results")
    table.add_column("Priority", justify="right")
    table.add_column("Vendor")
    table.add_column("Software")
    table.add_column("Subscription")
    table.add_column("Annual cost", justify="right")
    table.add_column("Risk")
    table.add_column("Action")
    table.add_column("Sources")

    for result in results:
        table.add_row(
            f"{result.priority_score:.2f}",
            result.vendor_name,
            result.software_name,
            result.subscription_code or "Unlinked",
            f"{result.annual_cost_usd:.2f}" if result.annual_cost_usd is not None else "N/A",
            f"{result.risk_category or 'UNKNOWN'} / {result.risk_severity or 'UNKNOWN'}",
            result.recommended_review_action,
            ",".join(result.matched_sources),
        )

    console = Console()
    console.print(table)
    for result in results:
        console.print(f"- {explain_result(result)}")


if __name__ == "__main__":
    main()
