from datetime import UTC, datetime
from decimal import Decimal

from agent_brain.graph.projection import normalize_projection_row, summarize_projection_rows


def test_normalize_projection_row_converts_database_values() -> None:
    row = {
        "vendor_code": "VND-OPENAI-001",
        "subscription_annual_cost_usd": Decimal("43200.00"),
        "subscription_renewal_date": datetime(2026, 10, 15, tzinfo=UTC),
    }

    normalized = normalize_projection_row(row)

    assert normalized["subscription_annual_cost_usd"] == 43200.0
    assert normalized["subscription_renewal_date"] == "2026-10-15T00:00:00+00:00"


def test_summarize_projection_rows_counts_distinct_graph_entities() -> None:
    rows = [
        {
            "vendor_code": "VND-OPENAI-001",
            "software_code": "SW-OPENAI-CHATGPT-ENT",
            "subscription_code": "SUB-ENG-OPENAI-001",
            "document_code": "DOC-OPENAI-SLA-001",
            "chunk_index": 0,
        },
        {
            "vendor_code": "VND-OPENAI-001",
            "software_code": "SW-OPENAI-CHATGPT-ENT",
            "subscription_code": "SUB-ENG-OPENAI-001",
            "document_code": "DOC-OPENAI-SLA-001",
            "chunk_index": 1,
        },
        {
            "vendor_code": "VND-NOTION-001",
            "software_code": "SW-NOTION-AI",
            "subscription_code": "SUB-PM-NOTION-001",
            "document_code": "DOC-NOTION-SLA-001",
            "chunk_index": 0,
        },
    ]

    summary = summarize_projection_rows(rows)

    assert summary.vendors == 2
    assert summary.software == 2
    assert summary.subscriptions == 2
    assert summary.documents == 2
    assert summary.chunks == 3
    assert summary.rows == 3
