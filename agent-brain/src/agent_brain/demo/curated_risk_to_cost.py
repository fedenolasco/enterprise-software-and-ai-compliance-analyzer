"""Curated Phase 2 risk-to-cost demo aligned to plans/03-query-scope.md."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from agent_brain.retrieval.hybrid import HybridRetrievalResult, explain_result, hybrid_retrieve

HybridRetriever = Callable[[str], list[HybridRetrievalResult]]


@dataclass(frozen=True)
class CuratedQuery:
    """Curated query definition from the Phase 2 query-scope contract."""

    query_id: str
    title: str
    prompt: str
    semantic_phrase: str
    expected_vendor_names: tuple[str, ...]
    purpose: str


@dataclass(frozen=True)
class CuratedDemoResult:
    """One curated demo query execution result."""

    query: CuratedQuery
    results: tuple[HybridRetrievalResult, ...]
    matched_expected_vendor_names: tuple[str, ...]
    missing_expected_vendor_names: tuple[str, ...]
    explanations: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """Return whether all expected positive vendors appeared in the results."""

        return len(self.missing_expected_vendor_names) == 0


CURATED_QUERIES: tuple[CuratedQuery, ...] = (
    CuratedQuery(
        query_id="Q1",
        title="High-risk AI vendors with renewal cost exposure",
        prompt=(
            "Which high-risk AI vendors have active or pending renewal exposure, and what "
            "compliance evidence should be reviewed before renewal?"
        ),
        semantic_phrase=(
            "cross-border processing outside the EU subprocessors automated decision "
            "making retention"
        ),
        expected_vendor_names=("OpenAI Enterprise", "Notion AI"),
        purpose="Validate high-risk renewal exposure with compliance evidence.",
    ),
    CuratedQuery(
        query_id="Q2",
        title="Cost-weighted compliance review queue",
        prompt=(
            "Prioritize AI software renewals for compliance review based on annual cost, "
            "renewal date, and high-severity evidence."
        ),
        semantic_phrase=(
            "high-impact workflow profiling automated decision support subprocessor "
            "cross-border transfer"
        ),
        expected_vendor_names=("Microsoft 365 Copilot", "OpenAI Enterprise", "Notion AI"),
        purpose="Validate cost-weighted prioritization across AI software renewals.",
    ),
    CuratedQuery(
        query_id="Q3",
        title="Data residency and international transfer exposure",
        prompt=(
            "Which vendors have evidence of cross-border processing, outside-EU processing, "
            "or international transfer safeguards?"
        ),
        semantic_phrase=(
            "cross-border outside the EU outside the EEA international transfer safeguards"
        ),
        expected_vendor_names=("OpenAI Enterprise", "Microsoft 365 Copilot", "Notion AI"),
        purpose="Validate international transfer and data residency evidence coverage.",
    ),
    CuratedQuery(
        query_id="Q4",
        title="HITL-required cancellation or renewal recommendation candidates",
        prompt=(
            "Which AI subscriptions should require human approval before any cancellation or "
            "renewal recommendation is finalized?"
        ),
        semantic_phrase=(
            "automated decision making profiling high-impact workflows subprocessors "
            "non-EU processing"
        ),
        expected_vendor_names=("OpenAI Enterprise", "Microsoft 365 Copilot", "Notion AI"),
        purpose="Validate HITL candidate detection before recommendation finalization.",
    ),
)


def run_curated_demo(
    retriever: HybridRetriever | None = None,
    *,
    queries: Sequence[CuratedQuery] = CURATED_QUERIES,
) -> list[CuratedDemoResult]:
    """Run all curated query-scope scenarios and assert expected positive vendors."""

    active_retriever = retriever or _default_hybrid_retriever
    return [run_curated_query(query, active_retriever) for query in queries]


def run_curated_query(query: CuratedQuery, retriever: HybridRetriever) -> CuratedDemoResult:
    """Run one curated query and evaluate expected positive matches."""

    results = tuple(retriever(query.semantic_phrase))
    matched = tuple(
        vendor_name
        for vendor_name in query.expected_vendor_names
        if any(result.vendor_name == vendor_name for result in results)
    )
    missing = tuple(
        vendor_name for vendor_name in query.expected_vendor_names if vendor_name not in matched
    )
    explanations = tuple(explain_result(result) for result in results)
    return CuratedDemoResult(
        query=query,
        results=results,
        matched_expected_vendor_names=matched,
        missing_expected_vendor_names=missing,
        explanations=explanations,
    )


def assert_curated_demo_passed(results: Sequence[CuratedDemoResult]) -> None:
    """Raise an assertion error if any curated query is missing expected vendors."""

    failures = [result for result in results if not result.passed]
    if failures:
        details = "; ".join(
            f"{result.query.query_id} missing {', '.join(result.missing_expected_vendor_names)}"
            for result in failures
        )
        raise AssertionError(f"Curated demo expected matches failed: {details}")


def curated_result_rows(result: CuratedDemoResult) -> list[dict[str, object]]:
    """Return notebook-friendly rows in the expected query-scope shape."""

    return [
        {
            "vendor_name": row.vendor_name,
            "software_name": row.software_name,
            "subscription_code": row.subscription_code,
            "annual_cost_usd": row.annual_cost_usd,
            "renewal_date": row.renewal_date,
            "subscription_status": row.subscription_status,
            "risk_tier": row.risk_tier,
            "risk_category": row.risk_category,
            "risk_severity": row.risk_severity,
            "evidence_excerpt": row.evidence_excerpt,
            "source_document": row.source_document,
            "recommended_review_action": row.recommended_review_action,
        }
        for row in result.results
    ]


def _default_hybrid_retriever(query: str) -> list[HybridRetrievalResult]:
    return hybrid_retrieve(query, top_k=8, graph_limit=50)
