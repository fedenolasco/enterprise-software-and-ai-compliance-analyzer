"""Neo4j graph traversal for compliance evidence and subscription exposure."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from neo4j import GraphDatabase

from agent_brain.config import AgentBrainSettings, get_settings

GRAPH_TRAVERSAL_QUERY = """
MATCH (vendor:Vendor)-[:SELLS]->(software:Software)
OPTIONAL MATCH (vendor)-[:HAS_SUBSCRIPTION]->(subscription:Subscription)
OPTIONAL MATCH (vendor)-[:HAS_POLICY]->(document:ComplianceDocument)
OPTIONAL MATCH (document)-[:HAS_CHUNK]->(chunk:DocumentChunk)
OPTIONAL MATCH (chunk)-[:EVIDENCES_RISK]->(software)
WHERE ($vendor_code IS NULL OR vendor.vendor_code = $vendor_code)
  AND ($risk_category IS NULL OR chunk.risk_category = $risk_category)
  AND ($risk_severity IS NULL OR chunk.risk_severity = $risk_severity)
RETURN
  vendor.vendor_code AS vendor_code,
  vendor.name AS vendor_name,
  vendor.ai_risk_tier AS vendor_ai_risk_tier,
  software.software_code AS software_code,
  software.name AS software_name,
  subscription.subscription_code AS subscription_code,
  subscription.annual_cost_usd AS annual_cost_usd,
  subscription.renewal_date AS renewal_date,
  subscription.status AS subscription_status,
  document.document_code AS document_code,
  document.title AS document_title,
  document.source_path AS source_path,
  chunk.chunk_index AS chunk_index,
  chunk.risk_category AS risk_category,
  chunk.risk_severity AS risk_severity,
  chunk.risk_score AS risk_score,
  chunk.text AS evidence_excerpt
ORDER BY
  coalesce(subscription.annual_cost_usd, 0) DESC,
  vendor.vendor_code ASC,
  software.software_code ASC,
  document.document_code ASC,
  chunk.chunk_index ASC
LIMIT $limit;
""".strip()


@dataclass(frozen=True)
class GraphTraversalResult:
    """One graph traversal row linking vendor context to evidence and cost exposure."""

    vendor_code: str
    vendor_name: str
    vendor_ai_risk_tier: str | None
    software_code: str
    software_name: str
    subscription_code: str | None
    annual_cost_usd: float | None
    renewal_date: str | None
    subscription_status: str | None
    document_code: str | None
    document_title: str | None
    source_path: str | None
    chunk_index: int | None
    risk_category: str | None
    risk_severity: str | None
    risk_score: float | None
    evidence_excerpt: str | None


def traverse_risk_context(
    settings: AgentBrainSettings | None = None,
    *,
    vendor_code: str | None = None,
    risk_category: str | None = None,
    risk_severity: str | None = None,
    limit: int | None = None,
) -> list[GraphTraversalResult]:
    """Traverse Neo4j from vendors and software to evidence chunks and subscriptions."""

    active_settings = settings or get_settings()
    query_limit = limit or active_settings.graph_result_limit
    driver = GraphDatabase.driver(
        active_settings.neo4j_uri,
        auth=(active_settings.neo4j_username, active_settings.neo4j_password),
    )
    try:
        with driver.session() as session:
            records = session.run(
                GRAPH_TRAVERSAL_QUERY,
                build_traversal_parameters(
                    vendor_code=vendor_code,
                    risk_category=risk_category,
                    risk_severity=risk_severity,
                    limit=query_limit,
                ),
            )
            return [graph_traversal_result_from_record(record.data()) for record in records]
    finally:
        driver.close()


def build_traversal_parameters(
    *,
    vendor_code: str | None = None,
    risk_category: str | None = None,
    risk_severity: str | None = None,
    limit: int,
) -> dict[str, Any]:
    """Build normalized Cypher parameters for graph traversal."""

    if limit <= 0:
        raise ValueError("limit must be a positive integer.")

    return {
        "vendor_code": _empty_to_none(vendor_code),
        "risk_category": _empty_to_none(risk_category),
        "risk_severity": _empty_to_none(risk_severity),
        "limit": limit,
    }


def graph_traversal_result_from_record(record: Mapping[str, Any]) -> GraphTraversalResult:
    """Convert a Neo4j record mapping into a typed traversal result."""

    return GraphTraversalResult(
        vendor_code=str(record["vendor_code"]),
        vendor_name=str(record["vendor_name"]),
        vendor_ai_risk_tier=_optional_str(record.get("vendor_ai_risk_tier")),
        software_code=str(record["software_code"]),
        software_name=str(record["software_name"]),
        subscription_code=_optional_str(record.get("subscription_code")),
        annual_cost_usd=_optional_float(record.get("annual_cost_usd")),
        renewal_date=_optional_str(record.get("renewal_date")),
        subscription_status=_optional_str(record.get("subscription_status")),
        document_code=_optional_str(record.get("document_code")),
        document_title=_optional_str(record.get("document_title")),
        source_path=_optional_str(record.get("source_path")),
        chunk_index=_optional_int(record.get("chunk_index")),
        risk_category=_optional_str(record.get("risk_category")),
        risk_severity=_optional_str(record.get("risk_severity")),
        risk_score=_optional_float(record.get("risk_score")),
        evidence_excerpt=_optional_str(record.get("evidence_excerpt")),
    )


def _empty_to_none(value: str | None) -> str | None:
    if value is None or value.strip() == "":
        return None
    return value


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
