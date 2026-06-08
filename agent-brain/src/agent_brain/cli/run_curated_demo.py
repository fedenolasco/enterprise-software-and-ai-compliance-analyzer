"""Command-line entry point for the curated Phase 2 risk-to-cost demo."""

from rich.console import Console
from rich.table import Table

from agent_brain.demo.curated_risk_to_cost import (
    assert_curated_demo_passed,
    curated_result_rows,
    run_curated_demo,
)


def main() -> None:
    """Run the curated Phase 2 demo queries and print deterministic assertions."""

    console = Console()
    demo_results = run_curated_demo()

    for demo_result in demo_results:
        table = Table(title=f"{demo_result.query.query_id}: {demo_result.query.title}")
        table.add_column("Vendor")
        table.add_column("Software")
        table.add_column("Subscription")
        table.add_column("Annual cost", justify="right")
        table.add_column("Risk")
        table.add_column("Action")

        for row in curated_result_rows(demo_result):
            table.add_row(
                str(row["vendor_name"]),
                str(row["software_name"]),
                str(row["subscription_code"] or "Unlinked"),
                f"{row['annual_cost_usd']:.2f}" if row["annual_cost_usd"] else "N/A",
                f"{row['risk_category'] or 'UNKNOWN'} / {row['risk_severity'] or 'UNKNOWN'}",
                str(row["recommended_review_action"]),
            )

        console.print(table)
        console.print(
            f"Matched expected vendors: {', '.join(demo_result.matched_expected_vendor_names)}"
        )
        if demo_result.missing_expected_vendor_names:
            console.print(
                f"[red]Missing expected vendors: "
                f"{', '.join(demo_result.missing_expected_vendor_names)}[/red]"
            )

    assert_curated_demo_passed(demo_results)
    console.print("[green]Curated Phase 2 demo assertions passed.[/green]")


if __name__ == "__main__":
    main()
