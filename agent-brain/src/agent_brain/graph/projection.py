"""Neo4j graph projection from validated PostgreSQL records."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from neo4j import Driver, GraphDatabase
from psycopg import connect
from psycopg.rows import dict_row

from agent_brain.config import AgentBrainSettings, get_settings

GRAPH_CONSTRAINTS: tuple[str, ...] = (
    "CREATE CONSTRAINT vendor_code IF NOT EXISTS FOR (v:Vendor) REQUIRE v.vendor_code IS UNIQUE",
    "CREATE CONSTRAINT software_code IF NOT EXISTS FOR (s:Software) "
    "REQUIRE s.software_code IS UNIQUE",
    "CREATE CONSTRAINT subscription_code IF NOT EXISTS FOR (s:Subscription) "
    "REQUIRE s.subscription_code IS UNIQUE",
    "CREATE CONSTRAINT compliance_document_code IF NOT EXISTS FOR (d:ComplianceDocument) "
    "REQUIRE d.document_code IS UNIQUE",
    "CREATE CONSTRAINT document_chunk_key IF NOT EXISTS FOR (c:DocumentChunk) "
    "REQUIRE (c.document_code, c.chunk_index) IS UNIQUE",
)


GRAPH_PROJECTION_SQL = """
SELECT
  v."vendorCode" AS vendor_code,
  v."name" AS vendor_name,
  v."legalName" AS vendor_legal_name,
  v."headquartersCountry" AS vendor_headquarters_country,
  v."aiRiskTier"::text AS vendor_ai_risk_tier,
  v."aiProcessingNotes" AS vendor_ai_processing_notes,
  sw."softwareCode" AS software_code,
  sw."name" AS software_name,
  sw."category" AS software_category,
  sw."deploymentModel" AS software_deployment_model,
  sw."isBusinessCritical" AS software_is_business_critical,
  sub."subscriptionCode" AS subscription_code,
  sub."department" AS subscription_department,
  sub."contractOwner" AS subscription_contract_owner,
  sub."annualCostUsd" AS subscription_annual_cost_usd,
  sub."monthlyCostUsd" AS subscription_monthly_cost_usd,
  sub."renewalDate" AS subscription_renewal_date,
  sub."status"::text AS subscription_status,
  doc."documentCode" AS document_code,
  doc."title" AS document_title,
  doc."documentType"::text AS document_type,
  doc."sourcePath" AS document_source_path,
  chunk."chunkIndex" AS chunk_index,
  chunk."chunkText" AS chunk_text,
  chunk."riskCategory"::text AS chunk_risk_category,
  chunk."riskSeverity"::text AS chunk_risk_severity,
  chunk."riskScore" AS chunk_risk_score
FROM "Vendor" v
JOIN "Software" sw ON sw."vendorId" = v."id"
LEFT JOIN "Subscription" sub ON sub."softwareId" = sw."id"
LEFT JOIN "ComplianceDocument" doc ON doc."softwareId" = sw."id"
LEFT JOIN "DocumentChunk" chunk ON chunk."documentId" = doc."id"
ORDER BY
  v."vendorCode",
  sw."softwareCode",
  sub."subscriptionCode",
  doc."documentCode",
  chunk."chunkIndex";
""".strip()


@dataclass(frozen=True)
class GraphProjectionSummary:
    """Counts returned after a graph projection run."""

    vendors: int
    software: int
    subscriptions: int
    documents: int
    chunks: int
    rows: int


def project_graph(settings: AgentBrainSettings | None = None) -> GraphProjectionSummary:
    """Project relational subscription and document evidence rows into Neo4j."""

    active_settings = settings or get_settings()
    rows = fetch_projection_rows(active_settings.database_url)

    driver = GraphDatabase.driver(
        active_settings.neo4j_uri,
        auth=(active_settings.neo4j_username, active_settings.neo4j_password),
    )
    try:
        return write_projection(driver, rows)
    finally:
        driver.close()


def fetch_projection_rows(database_url: str) -> list[dict[str, Any]]:
    """Read projection source rows from PostgreSQL."""

    with connect(_to_psycopg_conninfo(database_url), row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(GRAPH_PROJECTION_SQL)
            return list(cursor.fetchall())


def write_projection(driver: Driver, rows: Sequence[Mapping[str, Any]]) -> GraphProjectionSummary:
    """Write projection rows to Neo4j using idempotent merge statements."""

    normalized_rows = [normalize_projection_row(row) for row in rows]
    with driver.session() as session:
        for constraint in GRAPH_CONSTRAINTS:
            session.run(constraint)

        for row in normalized_rows:
            session.execute_write(_merge_projection_row, row)

    return summarize_projection_rows(normalized_rows)


def normalize_projection_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Convert database-native values into Neo4j-safe primitive values."""

    normalized = dict(row)
    for key, value in tuple(normalized.items()):
        if isinstance(value, Decimal):
            normalized[key] = float(value)
        elif hasattr(value, "isoformat"):
            normalized[key] = value.isoformat()
    return normalized


def summarize_projection_rows(rows: Iterable[Mapping[str, Any]]) -> GraphProjectionSummary:
    """Count distinct projected graph entities from source rows."""

    materialized_rows = list(rows)
    return GraphProjectionSummary(
        vendors=_count_distinct(materialized_rows, "vendor_code"),
        software=_count_distinct(materialized_rows, "software_code"),
        subscriptions=_count_distinct(materialized_rows, "subscription_code"),
        documents=_count_distinct(materialized_rows, "document_code"),
        chunks=len(
            {
                (row.get("document_code"), row.get("chunk_index"))
                for row in materialized_rows
                if row.get("document_code") is not None and row.get("chunk_index") is not None
            }
        ),
        rows=len(materialized_rows),
    )


def _merge_projection_row(transaction: Any, row: Mapping[str, Any]) -> None:
    transaction.run(
        """
        MERGE (vendor:Vendor {vendor_code: $vendor_code})
        SET vendor.name = $vendor_name,
            vendor.legal_name = $vendor_legal_name,
            vendor.headquarters_country = $vendor_headquarters_country,
            vendor.ai_risk_tier = $vendor_ai_risk_tier,
            vendor.ai_processing_notes = $vendor_ai_processing_notes
        MERGE (software:Software {software_code: $software_code})
        SET software.name = $software_name,
            software.category = $software_category,
            software.deployment_model = $software_deployment_model,
            software.is_business_critical = $software_is_business_critical
        MERGE (vendor)-[:SELLS]->(software)
        WITH vendor, software
        FOREACH (_ IN CASE WHEN $subscription_code IS NULL THEN [] ELSE [1] END |
          MERGE (subscription:Subscription {subscription_code: $subscription_code})
          SET subscription.department = $subscription_department,
              subscription.contract_owner = $subscription_contract_owner,
              subscription.annual_cost_usd = $subscription_annual_cost_usd,
              subscription.monthly_cost_usd = $subscription_monthly_cost_usd,
              subscription.renewal_date = $subscription_renewal_date,
              subscription.status = $subscription_status
          MERGE (vendor)-[:HAS_SUBSCRIPTION]->(subscription)
          MERGE (software)-[:HAS_SUBSCRIPTION]->(subscription)
        )
        WITH vendor, software
        FOREACH (_ IN CASE WHEN $document_code IS NULL THEN [] ELSE [1] END |
          MERGE (document:ComplianceDocument {document_code: $document_code})
          SET document.title = $document_title,
              document.document_type = $document_type,
              document.source_path = $document_source_path
          MERGE (vendor)-[:HAS_POLICY]->(document)
          MERGE (software)-[:HAS_POLICY]->(document)
        )
        WITH software
        FOREACH (_ IN CASE
          WHEN $document_code IS NULL OR $chunk_index IS NULL THEN [] ELSE [1]
        END |
          MERGE (document:ComplianceDocument {document_code: $document_code})
          MERGE (chunk:DocumentChunk {document_code: $document_code, chunk_index: $chunk_index})
          SET chunk.text = $chunk_text,
              chunk.risk_category = $chunk_risk_category,
              chunk.risk_severity = $chunk_risk_severity,
              chunk.risk_score = $chunk_risk_score
          MERGE (document)-[:HAS_CHUNK]->(chunk)
          MERGE (chunk)-[:EVIDENCES_RISK]->(software)
        )
        """,
        dict(row),
    )


def _count_distinct(rows: Sequence[Mapping[str, Any]], key: str) -> int:
    return len({row.get(key) for row in rows if row.get(key) is not None})


def _to_psycopg_conninfo(database_url: str) -> str:
    """Remove Prisma-only query parameters before connecting with psycopg."""

    parts = urlsplit(database_url)
    query_pairs = [(key, value) for key, value in parse_qsl(parts.query) if key != "schema"]
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query_pairs), parts.fragment)
    )
