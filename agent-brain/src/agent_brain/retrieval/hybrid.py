"""Hybrid retrieval combining PostgreSQL vector search with Neo4j graph traversal."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime

from agent_brain.config import AgentBrainSettings, get_settings
from agent_brain.graph.traversal import GraphTraversalResult, traverse_risk_context
from agent_brain.retrieval.vector import VectorSearchResult, vector_search

DEMO_REFERENCE_DATE = date(2026, 6, 1)

AI_RISK_WEIGHTS = {
    "CRITICAL": 40.0,
    "HIGH": 30.0,
    "MEDIUM": 15.0,
    "LOW": 5.0,
}

EVIDENCE_SEVERITY_WEIGHTS = {
    "CRITICAL": 30.0,
    "HIGH": 20.0,
    "MEDIUM": 10.0,
    "LOW": 3.0,
}


@dataclass(frozen=True)
class HybridRetrievalResult:
    """Merged risk-to-cost context row for Phase 2 demos and future agent workflows."""

    vendor_name: str
    software_name: str
    subscription_code: str | None
    annual_cost_usd: float | None
    renewal_date: str | None
    subscription_status: str | None
    risk_tier: str | None
    risk_category: str | None
    risk_severity: str | None
    evidence_excerpt: str | None
    source_document: str | None
    recommended_review_action: str
    priority_score: float
    vector_distance: float | None
    matched_sources: tuple[str, ...]


@dataclass(frozen=True)
class _MutableHybridRow:
    vendor_name: str
    software_name: str
    subscription_code: str | None
    annual_cost_usd: float | None
    renewal_date: str | None
    subscription_status: str | None
    risk_tier: str | None
    risk_category: str | None
    risk_severity: str | None
    evidence_excerpt: str | None
    source_document: str | None
    vector_distance: float | None
    matched_sources: tuple[str, ...]


def hybrid_retrieve(
    query: str,
    settings: AgentBrainSettings | None = None,
    *,
    top_k: int | None = None,
    graph_limit: int | None = None,
) -> list[HybridRetrievalResult]:
    """Retrieve and merge vector evidence with Neo4j graph relationship context."""

    active_settings = settings or get_settings()
    vector_results = vector_search(query, active_settings, top_k=top_k)
    graph_results = traverse_risk_context(
        active_settings,
        limit=graph_limit or active_settings.graph_result_limit,
    )
    return merge_retrieval_results(vector_results, graph_results)


def merge_retrieval_results(
    vector_results: Sequence[VectorSearchResult],
    graph_results: Sequence[GraphTraversalResult],
) -> list[HybridRetrievalResult]:
    """Merge vector and graph results into the query-scope result shape."""

    rows: dict[tuple[str | None, ...], _MutableHybridRow] = {}

    for graph_result in graph_results:
        key = _graph_key(graph_result)
        rows[key] = _merge_row(rows.get(key), _row_from_graph_result(graph_result))

    for vector_result in vector_results:
        key = _vector_key(vector_result)
        rows[key] = _merge_row(rows.get(key), _row_from_vector_result(vector_result))

    merged = [_finalize_row(row) for row in rows.values()]
    return sorted(
        merged,
        key=lambda row: (
            -row.priority_score,
            -(row.annual_cost_usd or 0.0),
            row.vector_distance if row.vector_distance is not None else float("inf"),
            row.vendor_name,
            row.software_name,
        ),
    )


def calculate_priority_score(
    *,
    risk_tier: str | None,
    risk_severity: str | None,
    annual_cost_usd: float | None,
    renewal_date: str | None,
    subscription_status: str | None,
) -> float:
    """Apply deterministic ranking logic documented in the Phase 2 query scope."""

    score = AI_RISK_WEIGHTS.get((risk_tier or "").upper(), 0.0)
    score += EVIDENCE_SEVERITY_WEIGHTS.get((risk_severity or "").upper(), 0.0)
    score += min((annual_cost_usd or 0.0) / 5000.0, 25.0)
    score += _renewal_urgency_weight(renewal_date)
    if (subscription_status or "").upper() == "PENDING_RENEWAL":
        score += 15.0
    return round(score, 2)


def recommend_review_action(
    *,
    risk_tier: str | None,
    risk_category: str | None,
    risk_severity: str | None,
    annual_cost_usd: float | None,
    subscription_status: str | None,
) -> str:
    """Return a deterministic review action for the merged result row."""

    tier = (risk_tier or "").upper()
    category = (risk_category or "").upper()
    severity = (risk_severity or "").upper()
    status = (subscription_status or "").upper()
    cost = annual_cost_usd or 0.0

    if tier in {"HIGH", "CRITICAL"} and (severity in {"HIGH", "CRITICAL"} or cost >= 25000):
        return "HITL-required decision"
    if category == "DATA_RESIDENCY":
        return "Data residency review"
    if severity in {"HIGH", "CRITICAL"}:
        return "Governance review"
    if status in {"ACTIVE", "PENDING_RENEWAL"}:
        return "Renewal review"
    return "Governance review"


def _row_from_vector_result(result: VectorSearchResult) -> _MutableHybridRow:
    return _MutableHybridRow(
        vendor_name=result.vendor_name or "Unknown vendor",
        software_name=result.software_name or "Unknown software",
        subscription_code=result.subscription_code,
        annual_cost_usd=result.annual_cost_usd,
        renewal_date=result.renewal_date,
        subscription_status=result.subscription_status,
        risk_tier=result.vendor_ai_risk_tier,
        risk_category=result.risk_category,
        risk_severity=result.risk_severity,
        evidence_excerpt=result.evidence_excerpt,
        source_document=result.source_path or result.document_title,
        vector_distance=result.distance,
        matched_sources=("vector",),
    )


def _row_from_graph_result(result: GraphTraversalResult) -> _MutableHybridRow:
    return _MutableHybridRow(
        vendor_name=result.vendor_name,
        software_name=result.software_name,
        subscription_code=result.subscription_code,
        annual_cost_usd=result.annual_cost_usd,
        renewal_date=result.renewal_date,
        subscription_status=result.subscription_status,
        risk_tier=result.vendor_ai_risk_tier,
        risk_category=result.risk_category,
        risk_severity=result.risk_severity,
        evidence_excerpt=result.evidence_excerpt,
        source_document=result.source_path or result.document_title,
        vector_distance=None,
        matched_sources=("graph",),
    )


def _merge_row(
    existing: _MutableHybridRow | None,
    incoming: _MutableHybridRow,
) -> _MutableHybridRow:
    if existing is None:
        return incoming

    return _MutableHybridRow(
        vendor_name=_prefer(existing.vendor_name, incoming.vendor_name) or "Unknown vendor",
        software_name=_prefer(existing.software_name, incoming.software_name) or "Unknown software",
        subscription_code=_prefer(existing.subscription_code, incoming.subscription_code),
        annual_cost_usd=_prefer_number(existing.annual_cost_usd, incoming.annual_cost_usd),
        renewal_date=_prefer(existing.renewal_date, incoming.renewal_date),
        subscription_status=_prefer(existing.subscription_status, incoming.subscription_status),
        risk_tier=_prefer(existing.risk_tier, incoming.risk_tier),
        risk_category=_prefer(existing.risk_category, incoming.risk_category),
        risk_severity=_prefer(existing.risk_severity, incoming.risk_severity),
        evidence_excerpt=_prefer(existing.evidence_excerpt, incoming.evidence_excerpt),
        source_document=_prefer(existing.source_document, incoming.source_document),
        vector_distance=_prefer_number(
            existing.vector_distance,
            incoming.vector_distance,
            lower_is_better=True,
        ),
        matched_sources=tuple(sorted(set(existing.matched_sources + incoming.matched_sources))),
    )


def _finalize_row(row: _MutableHybridRow) -> HybridRetrievalResult:
    priority_score = calculate_priority_score(
        risk_tier=row.risk_tier,
        risk_severity=row.risk_severity,
        annual_cost_usd=row.annual_cost_usd,
        renewal_date=row.renewal_date,
        subscription_status=row.subscription_status,
    )
    return HybridRetrievalResult(
        vendor_name=row.vendor_name,
        software_name=row.software_name,
        subscription_code=row.subscription_code,
        annual_cost_usd=row.annual_cost_usd,
        renewal_date=row.renewal_date,
        subscription_status=row.subscription_status,
        risk_tier=row.risk_tier,
        risk_category=row.risk_category,
        risk_severity=row.risk_severity,
        evidence_excerpt=row.evidence_excerpt,
        source_document=row.source_document,
        recommended_review_action=recommend_review_action(
            risk_tier=row.risk_tier,
            risk_category=row.risk_category,
            risk_severity=row.risk_severity,
            annual_cost_usd=row.annual_cost_usd,
            subscription_status=row.subscription_status,
        ),
        priority_score=priority_score,
        vector_distance=row.vector_distance,
        matched_sources=row.matched_sources,
    )


def _vector_key(result: VectorSearchResult) -> tuple[str | None, ...]:
    return (
        result.vendor_code,
        result.software_code,
        result.subscription_code,
        result.document_code,
        str(result.chunk_index),
    )


def _graph_key(result: GraphTraversalResult) -> tuple[str | None, ...]:
    return (
        result.vendor_code,
        result.software_code,
        result.subscription_code,
        result.document_code,
        str(result.chunk_index) if result.chunk_index is not None else None,
    )


def _renewal_urgency_weight(renewal_date: str | None) -> float:
    parsed = _parse_date(renewal_date)
    if parsed is None:
        return 0.0

    days_until_renewal = (parsed - DEMO_REFERENCE_DATE).days
    if days_until_renewal < 0:
        return 0.0
    if days_until_renewal <= 30:
        return 20.0
    if days_until_renewal <= 90:
        return 15.0
    if days_until_renewal <= 180:
        return 10.0
    if days_until_renewal <= 365:
        return 5.0
    return 0.0


def _parse_date(value: str | None) -> date | None:
    if value is None or value.strip() == "":
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.date()


def _prefer(existing: str | None, incoming: str | None) -> str | None:
    return existing if existing not in {None, ""} else incoming


def _prefer_number(
    existing: float | None,
    incoming: float | None,
    *,
    lower_is_better: bool = False,
) -> float | None:
    if existing is None:
        return incoming
    if incoming is None:
        return existing
    if lower_is_better:
        return min(existing, incoming)
    return max(existing, incoming)


def explain_result(result: HybridRetrievalResult) -> str:
    """Build a deterministic human-readable explanation for a hybrid result."""

    parts = [
        f"{result.vendor_name} / {result.software_name}",
        f"risk tier={result.risk_tier or 'UNKNOWN'}",
        f"risk={result.risk_category or 'UNKNOWN'}:{result.risk_severity or 'UNKNOWN'}",
    ]
    if result.annual_cost_usd is not None:
        parts.append(f"annual cost=${result.annual_cost_usd:,.2f}")
    if result.renewal_date:
        parts.append(f"renewal={result.renewal_date}")
    parts.append(f"action={result.recommended_review_action}")
    parts.append(f"sources={','.join(result.matched_sources)}")
    return "; ".join(parts)
