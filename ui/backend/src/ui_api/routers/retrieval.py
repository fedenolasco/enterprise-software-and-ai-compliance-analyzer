"""Retrieval router for vector, graph, and hybrid search."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/retrieval", tags=["retrieval"])


class VectorSearchRequest(BaseModel):
    """Request body for vector search."""

    query: str = Field(..., min_length=1, description="Query text to embed and search.")
    top_k: int | None = Field(default=None, ge=1, description="Maximum results to return.")


class GraphTraversalRequest(BaseModel):
    """Request body for graph traversal."""

    vendor_code: str | None = Field(default=None, description="Optional vendor code filter.")
    risk_category: str | None = Field(default=None, description="Optional risk category filter.")
    risk_severity: str | None = Field(default=None, description="Optional risk severity filter.")
    limit: int | None = Field(default=None, ge=1, description="Maximum rows to return.")


class HybridRetrievalRequest(BaseModel):
    """Request body for hybrid retrieval."""

    query: str = Field(..., min_length=1, description="Query text for hybrid retrieval.")
    top_k: int | None = Field(default=None, ge=1, description="Maximum vector results.")
    graph_limit: int | None = Field(default=None, ge=1, description="Maximum graph rows.")


def _result_to_dict(result: Any) -> dict[str, Any]:
    """Convert a dataclass result to a dict."""
    if hasattr(result, "__dict__"):
        return {k: v for k, v in result.__dict__.items() if not k.startswith("_")}
    return dict(result)


@router.post("/vector")
async def vector_search(request: VectorSearchRequest) -> dict[str, Any]:
    """Run PostgreSQL pgvector semantic search."""
    try:
        from agent_brain.retrieval.vector import vector_search as _vector_search

        results = _vector_search(request.query, top_k=request.top_k)
        return {
            "results": [_result_to_dict(r) for r in results],
            "count": len(results),
            "query": request.query,
            "cli_equivalent": (
                f'agent-brain-search-vectors "{request.query}"'
                + (f" --top-k {request.top_k}" if request.top_k else "")
            ),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "service": "postgres",
                "remediation": "Start PostgreSQL: docker compose up postgres",
                "error": str(exc),
            },
        ) from exc


@router.post("/graph")
async def graph_traversal(request: GraphTraversalRequest) -> dict[str, Any]:
    """Run Neo4j graph traversal."""
    try:
        from agent_brain.graph.traversal import traverse_risk_context

        results = traverse_risk_context(
            vendor_code=request.vendor_code,
            risk_category=request.risk_category,
            risk_severity=request.risk_severity,
            limit=request.limit,
        )
        return {
            "results": [_result_to_dict(r) for r in results],
            "count": len(results),
            "cli_equivalent": (
                "agent-brain-traverse-graph"
                + (f" --vendor-code {request.vendor_code}" if request.vendor_code else "")
                + (
                    f" --risk-category {request.risk_category}"
                    if request.risk_category
                    else ""
                )
                + (
                    f" --risk-severity {request.risk_severity}"
                    if request.risk_severity
                    else ""
                )
                + (f" --limit {request.limit}" if request.limit else "")
            ),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "service": "neo4j",
                "remediation": "Start Neo4j: docker compose up neo4j",
                "error": str(exc),
            },
        ) from exc


@router.post("/hybrid")
async def hybrid_retrieval(request: HybridRetrievalRequest) -> dict[str, Any]:
    """Run hybrid vector + graph retrieval."""
    try:
        from agent_brain.retrieval.hybrid import hybrid_retrieve

        results = hybrid_retrieve(
            request.query,
            top_k=request.top_k,
            graph_limit=request.graph_limit,
        )
        return {
            "results": [_result_to_dict(r) for r in results],
            "count": len(results),
            "query": request.query,
            "cli_equivalent": (
                f'agent-brain-hybrid-retrieve "{request.query}"'
                + (f" --top-k {request.top_k}" if request.top_k else "")
                + (f" --graph-limit {request.graph_limit}" if request.graph_limit else "")
            ),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "service": "postgres",
                "remediation": "Start PostgreSQL and Neo4j: docker compose up",
                "error": str(exc),
            },
        ) from exc


@router.get("/curated")
async def get_curated_queries() -> dict[str, Any]:
    """Get curated demo query presets."""
    return {
        "queries": [
            {
                "id": "query-1",
                "title": "High-risk AI vendors with renewal cost exposure",
                "natural_language": "Which high-risk AI vendors have active or pending renewal exposure, and what compliance evidence should be reviewed before renewal?",
                "semantic_phrase": "cross-border processing outside the EU subprocessors automated decision making retention",
                "cli_equivalent": "agent-brain-run-curated-demo",
            },
            {
                "id": "query-2",
                "title": "Cost-weighted compliance review queue",
                "natural_language": "Prioritize AI software renewals for compliance review based on annual cost, renewal date, and high-severity evidence.",
                "semantic_phrase": "high-impact workflow profiling automated decision support subprocessor cross-border transfer",
                "cli_equivalent": "agent-brain-run-curated-demo",
            },
            {
                "id": "query-3",
                "title": "Data residency and international transfer exposure",
                "natural_language": "Which vendors have evidence of cross-border processing, outside-EU processing, or international transfer safeguards?",
                "semantic_phrase": "cross-border outside the EU outside the EEA international transfer safeguards",
                "cli_equivalent": "agent-brain-run-curated-demo",
            },
            {
                "id": "query-4",
                "title": "HITL-required cancellation or renewal recommendation candidates",
                "natural_language": "Which AI subscriptions should require human approval before any cancellation or renewal recommendation is finalized?",
                "semantic_phrase": "automated decision making profiling high-impact workflows subprocessors non-EU processing",
                "cli_equivalent": "agent-brain-run-curated-demo",
            },
        ]
    }


@router.post("/curated/run")
async def run_curated_demo() -> dict[str, Any]:
    """Run the curated Phase 2 demo queries."""
    try:
        from agent_brain.demo.curated_risk_to_cost import run_curated_demo

        demo_results = run_curated_demo()
        return {
            "results": [
                {
                    "query_id": r.query.query_id,
                    "title": r.query.title,
                    "matched_expected_vendors": list(r.matched_expected_vendor_names),
                    "missing_expected_vendors": list(r.missing_expected_vendor_names),
                    "rows": [
                        {
                            "vendor_name": row["vendor_name"],
                            "software_name": row["software_name"],
                            "subscription_code": row.get("subscription_code"),
                            "annual_cost_usd": row.get("annual_cost_usd"),
                            "risk_category": row.get("risk_category"),
                            "risk_severity": row.get("risk_severity"),
                            "recommended_review_action": row["recommended_review_action"],
                        }
                        for row in [
                            {
                                "vendor_name": getattr(r, "vendor_name", ""),
                            }
                        ]
                    ],
                }
                for r in demo_results
            ],
            "cli_equivalent": "agent-brain-run-curated-demo",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "service": "postgres",
                "remediation": "Start PostgreSQL and Neo4j: docker compose up",
                "error": str(exc),
            },
        ) from exc
