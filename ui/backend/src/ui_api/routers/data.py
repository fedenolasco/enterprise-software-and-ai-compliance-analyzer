"""Data browsing router for vendors, software, subscriptions, documents, and pricing."""

from __future__ import annotations

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from psycopg import connect
from psycopg.sql import SQL, Identifier

from agent_brain.config import get_settings as get_agent_brain_settings

router = APIRouter(prefix="/api/data", tags=["data"])


def _execute_query(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """Execute a PostgreSQL query and return rows as dicts."""
    settings = get_agent_brain_settings()
    with connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)  # type: ignore[arg-type]
            columns = [desc[0] for desc in cur.description] if cur.description else []
            return [dict(zip(columns, row, strict=False)) for row in cur.fetchall()]


@router.get("/vendors")
async def get_vendors() -> dict[str, Any]:
    """Browse vendors from PostgreSQL."""
    try:
        rows = _execute_query(
            'SELECT "vendorCode", "name", "country", "aiRiskTier", '
            '"aiProcessingPosture" FROM "Vendor" ORDER BY "name"'
        )
        return {"vendors": rows, "count": len(rows)}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "service": "postgres",
                "remediation": "Start PostgreSQL: docker compose up postgres",
                "error": str(exc),
            },
        ) from exc


@router.get("/software")
async def get_software() -> dict[str, Any]:
    """Browse software products from PostgreSQL."""
    try:
        rows = _execute_query(
            'SELECT "softwareCode", "name", "vendorCode", "category" '
            'FROM "Software" ORDER BY "name"'
        )
        return {"software": rows, "count": len(rows)}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "service": "postgres",
                "remediation": "Start PostgreSQL: docker compose up postgres",
                "error": str(exc),
            },
        ) from exc


@router.get("/subscriptions")
async def get_subscriptions() -> dict[str, Any]:
    """Browse subscriptions with cost and renewal info."""
    try:
        rows = _execute_query(
            'SELECT "subscriptionCode", "vendorCode", "softwareCode", '
            '"contractType", "seats", "annualCostUsd", "renewalDate", '
            '"status", "owner" FROM "Subscription" ORDER BY "annualCostUsd" DESC'
        )
        return {"subscriptions": rows, "count": len(rows)}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "service": "postgres",
                "remediation": "Start PostgreSQL: docker compose up postgres",
                "error": str(exc),
            },
        ) from exc


@router.get("/documents")
async def get_documents() -> dict[str, Any]:
    """Browse compliance document corpus."""
    try:
        docs = _execute_query(
            'SELECT "documentCode", "title", "documentType", "vendorCode", '
            '"sourcePath" FROM "ComplianceDocument" ORDER BY "title"'
        )
        chunks = _execute_query(
            'SELECT COUNT(*) as count FROM "DocumentChunk"'
        )
        chunk_count = chunks[0]["count"] if chunks else 0
        return {"documents": docs, "document_count": len(docs), "chunk_count": chunk_count}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "service": "postgres",
                "remediation": "Start PostgreSQL: docker compose up postgres",
                "error": str(exc),
            },
        ) from exc


@router.get("/pricing")
async def get_pricing() -> dict[str, Any]:
    """Browse mock pricing records from the pricing API."""
    settings = get_agent_brain_settings()
    try:
        response = httpx.get(f"{settings.mock_pricing_api_url}/pricing", timeout=5.0)
        if response.status_code == 200:
            records = response.json()
            return {"pricing": records, "count": len(records)}
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Pricing API returned status {response.status_code}",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "service": "pricing-api",
                "remediation": "Start pricing API: cd mock-pricing-api && python -m mock_pricing_api.main",
                "error": str(exc),
            },
        ) from exc


@router.get("/graph")
async def get_graph_summary() -> dict[str, Any]:
    """Get Neo4j graph node and relationship summary."""
    from neo4j import GraphDatabase

    settings = get_agent_brain_settings()
    try:
        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )
        try:
            with driver.session() as session:
                # Count nodes by label
                node_result = session.run(
                    "MATCH (n) UNWIND labels(n) AS label "
                    "RETURN label, count(n) AS count ORDER BY label"
                )
                nodes = {record["label"]: record["count"] for record in node_result}

                # Count relationships by type
                rel_result = session.run(
                    "MATCH ()-[r]->() "
                    "RETURN type(r) AS type, count(r) AS count ORDER BY type"
                )
                relationships = {
                    record["type"]: record["count"] for record in rel_result
                }

            return {
                "nodes": nodes,
                "relationships": relationships,
                "total_nodes": sum(nodes.values()),
                "total_relationships": sum(relationships.values()),
            }
        finally:
            driver.close()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "service": "neo4j",
                "remediation": "Start Neo4j: docker compose up neo4j",
                "error": str(exc),
            },
        ) from exc


@router.get("/audit")
async def get_audit_events(limit: int = 50) -> dict[str, Any]:
    """Get recent audit events from PostgreSQL."""
    try:
        rows = _execute_query(
            'SELECT "eventType", "status", "actor", "traceId", "message", '
            '"detail", "createdAt" FROM "AuditEvent" '
            'ORDER BY "createdAt" DESC LIMIT %s',
            (limit,),
        )
        return {"audit_events": rows, "count": len(rows)}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "service": "postgres",
                "remediation": "Start PostgreSQL: docker compose up postgres",
                "error": str(exc),
            },
        ) from exc
