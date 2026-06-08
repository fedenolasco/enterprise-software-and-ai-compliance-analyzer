import pytest

from agent_brain.demo.curated_risk_to_cost import (
    CURATED_QUERIES,
    assert_curated_demo_passed,
    curated_result_rows,
    run_curated_demo,
)
from agent_brain.retrieval.hybrid import HybridRetrievalResult


def _result(vendor_name: str) -> HybridRetrievalResult:
    return HybridRetrievalResult(
        vendor_name=vendor_name,
        software_name=f"{vendor_name} Software",
        subscription_code="SUB-001",
        annual_cost_usd=10000.0,
        renewal_date="2026-07-01T00:00:00+00:00",
        subscription_status="ACTIVE",
        risk_tier="HIGH",
        risk_category="DATA_RESIDENCY",
        risk_severity="HIGH",
        evidence_excerpt="evidence excerpt",
        source_document="source.txt",
        recommended_review_action="HITL-required decision",
        priority_score=60.0,
        vector_distance=0.1,
        matched_sources=("graph", "vector"),
    )


def test_curated_queries_match_query_scope_contract() -> None:
    assert [query.query_id for query in CURATED_QUERIES] == ["Q1", "Q2", "Q3", "Q4"]
    assert CURATED_QUERIES[0].expected_vendor_names == ("OpenAI Enterprise", "Notion AI")
    assert "cross-border" in CURATED_QUERIES[2].semantic_phrase


def test_run_curated_demo_reports_expected_matches() -> None:
    def retriever(_: str) -> list[HybridRetrievalResult]:
        return [
            _result("OpenAI Enterprise"),
            _result("Microsoft 365 Copilot"),
            _result("Notion AI"),
        ]

    results = run_curated_demo(retriever)

    assert all(result.passed for result in results)
    assert results[0].matched_expected_vendor_names == ("OpenAI Enterprise", "Notion AI")
    assert curated_result_rows(results[0])[0]["vendor_name"] == "OpenAI Enterprise"


def test_assert_curated_demo_passed_raises_for_missing_expected_vendor() -> None:
    def retriever(_: str) -> list[HybridRetrievalResult]:
        return [_result("OpenAI Enterprise")]

    results = run_curated_demo(retriever, queries=(CURATED_QUERIES[0],))

    with pytest.raises(AssertionError, match="Q1 missing Notion AI"):
        assert_curated_demo_passed(results)
