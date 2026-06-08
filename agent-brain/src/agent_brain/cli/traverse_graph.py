"""Command-line entry point for Neo4j graph traversal."""

from argparse import ArgumentParser

from rich.console import Console
from rich.table import Table

from agent_brain.graph.traversal import traverse_risk_context


def main() -> None:
    """Run a documented local Neo4j traversal over projected risk context."""

    parser = ArgumentParser(
        description="Traverse Neo4j vendor, software, subscription, and evidence relationships."
    )
    parser.add_argument("--vendor-code", default=None, help="Optional vendor code filter.")
    parser.add_argument("--risk-category", default=None, help="Optional risk category filter.")
    parser.add_argument("--risk-severity", default=None, help="Optional risk severity filter.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum rows to return.")
    args = parser.parse_args()

    results = traverse_risk_context(
        vendor_code=args.vendor_code,
        risk_category=args.risk_category,
        risk_severity=args.risk_severity,
        limit=args.limit,
    )

    table = Table(title="Neo4j graph traversal results")
    table.add_column("Vendor")
    table.add_column("Software")
    table.add_column("Subscription")
    table.add_column("Annual cost", justify="right")
    table.add_column("Risk")
    table.add_column("Evidence excerpt")

    for result in results:
        table.add_row(
            result.vendor_name,
            result.software_name,
            result.subscription_code or "Unlinked",
            f"{result.annual_cost_usd:.2f}" if result.annual_cost_usd is not None else "N/A",
            f"{result.risk_category or 'UNKNOWN'} / {result.risk_severity or 'UNKNOWN'}",
            (result.evidence_excerpt or "")[:160],
        )

    Console().print(table)


if __name__ == "__main__":
    main()
