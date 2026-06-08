from agent_brain.graph.traversal import GraphTraversalResult
from agent_brain.retrieval.hybrid import (
    calculate_priority_score,
    explain_result,
    merge_retrieval_results,
    recommend_review_action,
)
from agent_brain.retrieval.vector import VectorSearchResult


def test_calculate_priority_score_uses_query_scope_weights() -> None:
    score = calculate_priority_score(
        risk_tier="HIGH",
        risk_severity="HIGH",
        annual_cost_usd=43200.0,
        renewal_date="2026-10-15T00:00:00+00:00",
        subscription_status="ACTIVE",
    )

    assert score == 68.64


def test_recommend_review_action_flags_high_risk_cost_context_for_hitl() -> None:
    action = recommend_review_action(
        risk_tier="HIGH",
        risk_category="DATA_RESIDENCY",
        risk_severity="HIGH",
        annual_cost_usd=43200.0,
        subscription_status="ACTIVE",
    )

    assert action == "HITL-required decision"


def test_merge_retrieval_results_combines_vector_and_graph_rows() -> None:
    vector_result = VectorSearchResult(
        vendor_code="VND-OPENAI-001",
        vendor_name="OpenAI Enterprise",
        vendor_ai_risk_tier="HIGH",
        software_code="SW-OPENAI-CHATGPT-ENT",
        software_name="ChatGPT Enterprise",
        subscription_code="SUB-ENG-OPENAI-001",
        annual_cost_usd=43200.0,
        renewal_date="2026-10-15T00:00:00+00:00",
        subscription_status="ACTIVE",
        document_code="DOC-OPENAI-SLA-001",
        document_title="OpenAI Enterprise SLA",
        source_path="database-layer/data/documents/openai-enterprise-sla.txt",
        chunk_index=0,
        evidence_excerpt="cross-border transfer evidence",
        risk_category="DATA_RESIDENCY",
        risk_severity="HIGH",
        risk_score=0.82,
        distance=0.12,
    )
    graph_result = GraphTraversalResult(
        vendor_code="VND-OPENAI-001",
        vendor_name="OpenAI Enterprise",
        vendor_ai_risk_tier="HIGH",
        software_code="SW-OPENAI-CHATGPT-ENT",
        software_name="ChatGPT Enterprise",
        subscription_code="SUB-ENG-OPENAI-001",
        annual_cost_usd=43200.0,
        renewal_date="2026-10-15T00:00:00+00:00",
        subscription_status="ACTIVE",
        document_code="DOC-OPENAI-SLA-001",
        document_title="OpenAI Enterprise SLA",
        source_path="database-layer/data/documents/openai-enterprise-sla.txt",
        chunk_index=0,
        risk_category="DATA_RESIDENCY",
        risk_severity="HIGH",
        risk_score=0.82,
        evidence_excerpt="cross-border transfer evidence",
    )

    results = merge_retrieval_results([vector_result], [graph_result])

    assert len(results) == 1
    assert results[0].vendor_name == "OpenAI Enterprise"
    assert results[0].matched_sources == ("graph", "vector")
    assert results[0].recommended_review_action == "HITL-required decision"
    assert results[0].priority_score == 68.64
    assert "OpenAI Enterprise / ChatGPT Enterprise" in explain_result(results[0])


def test_merge_retrieval_results_sorts_by_priority_descending() -> None:
    lower_priority = GraphTraversalResult(
        vendor_code="VND-MS-001",
        vendor_name="Microsoft 365 Copilot",
        vendor_ai_risk_tier="MEDIUM",
        software_code="SW-MS-COPILOT-M365",
        software_name="Microsoft 365 Copilot",
        subscription_code="SUB-OPS-MS-001",
        annual_cost_usd=90000.0,
        renewal_date="2026-09-01T00:00:00+00:00",
        subscription_status="ACTIVE",
        document_code="DOC-MS-DPA-001",
        document_title="Microsoft 365 Copilot DPA",
        source_path="database-layer/data/documents/microsoft-copilot-dpa.txt",
        chunk_index=0,
        risk_category="SECURITY_CONTROLS",
        risk_severity="LOW",
        risk_score=0.28,
        evidence_excerpt="security controls evidence",
    )
    higher_priority = GraphTraversalResult(
        vendor_code="VND-NOTION-001",
        vendor_name="Notion AI",
        vendor_ai_risk_tier="HIGH",
        software_code="SW-NOTION-AI",
        software_name="Notion AI",
        subscription_code="SUB-PM-NOTION-001",
        annual_cost_usd=17280.0,
        renewal_date="2026-07-01T00:00:00+00:00",
        subscription_status="PENDING_RENEWAL",
        document_code="DOC-NOTION-SLA-001",
        document_title="Notion AI SLA",
        source_path="database-layer/data/documents/notion-ai-sla.txt",
        chunk_index=0,
        risk_category="SUBPROCESSOR_RISK",
        risk_severity="HIGH",
        risk_score=0.78,
        evidence_excerpt="subprocessor evidence",
    )

    results = merge_retrieval_results([], [lower_priority, higher_priority])

    assert [result.vendor_name for result in results] == ["Notion AI", "Microsoft 365 Copilot"]
