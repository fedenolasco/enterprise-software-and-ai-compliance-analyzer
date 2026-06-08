from datetime import UTC, datetime
from decimal import Decimal

from agent_brain.retrieval.vector import (
    create_deterministic_embedding,
    to_pgvector_literal,
    vector_search_result_from_row,
)


def test_create_deterministic_embedding_matches_database_layer_algorithm() -> None:
    embedding = create_deterministic_embedding("abc", 8)

    assert embedding == [0.097, 0.049, 0.033, 0.0, 0.0, 0.0, 0.0, 0.0]


def test_to_pgvector_literal_formats_fixed_precision_values() -> None:
    literal = to_pgvector_literal([0.097, 0.049, 0.033])

    assert literal == "[0.097000,0.049000,0.033000]"


def test_vector_search_result_from_row_normalizes_database_values() -> None:
    result = vector_search_result_from_row(
        {
            "vendor_code": "VND-OPENAI-001",
            "vendor_name": "OpenAI Enterprise",
            "vendor_ai_risk_tier": "HIGH",
            "software_code": "SW-OPENAI-CHATGPT-ENT",
            "software_name": "ChatGPT Enterprise",
            "subscription_code": "SUB-ENG-OPENAI-001",
            "annual_cost_usd": Decimal("43200.00"),
            "renewal_date": datetime(2026, 10, 15, tzinfo=UTC),
            "subscription_status": "ACTIVE",
            "document_code": "DOC-OPENAI-SLA-001",
            "document_title": "OpenAI Enterprise SLA",
            "source_path": "database-layer/data/documents/openai-enterprise-sla.txt",
            "chunk_index": 0,
            "evidence_excerpt": "cross-border transfer evidence",
            "risk_category": "DATA_RESIDENCY",
            "risk_severity": "HIGH",
            "risk_score": Decimal("0.82"),
            "distance": Decimal("0.123456"),
        }
    )

    assert result.vendor_name == "OpenAI Enterprise"
    assert result.annual_cost_usd == 43200.0
    assert result.renewal_date == "2026-10-15T00:00:00+00:00"
    assert result.risk_score == 0.82
    assert result.distance == 0.123456
