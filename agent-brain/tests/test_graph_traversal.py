import pytest

from agent_brain.graph.traversal import (
    build_traversal_parameters,
    graph_traversal_result_from_record,
)


def test_build_traversal_parameters_normalizes_empty_filters() -> None:
    parameters = build_traversal_parameters(
        vendor_code="",
        risk_category="DATA_RESIDENCY",
        risk_severity=None,
        limit=5,
    )

    assert parameters == {
        "vendor_code": None,
        "risk_category": "DATA_RESIDENCY",
        "risk_severity": None,
        "limit": 5,
    }


def test_build_traversal_parameters_rejects_non_positive_limit() -> None:
    with pytest.raises(ValueError, match="limit must be a positive integer"):
        build_traversal_parameters(limit=0)


def test_graph_traversal_result_from_record_normalizes_optional_values() -> None:
    result = graph_traversal_result_from_record(
        {
            "vendor_code": "VND-OPENAI-001",
            "vendor_name": "OpenAI Enterprise",
            "vendor_ai_risk_tier": "HIGH",
            "software_code": "SW-OPENAI-CHATGPT-ENT",
            "software_name": "ChatGPT Enterprise",
            "subscription_code": "SUB-ENG-OPENAI-001",
            "annual_cost_usd": 43200,
            "renewal_date": "2026-10-15T00:00:00+00:00",
            "subscription_status": "ACTIVE",
            "document_code": "DOC-OPENAI-SLA-001",
            "document_title": "OpenAI Enterprise SLA",
            "source_path": "database-layer/data/documents/openai-enterprise-sla.txt",
            "chunk_index": 2,
            "risk_category": "DATA_RESIDENCY",
            "risk_severity": "HIGH",
            "risk_score": 0.82,
            "evidence_excerpt": "cross-border transfer evidence",
        }
    )

    assert result.vendor_name == "OpenAI Enterprise"
    assert result.annual_cost_usd == 43200.0
    assert result.chunk_index == 2
    assert result.risk_category == "DATA_RESIDENCY"
