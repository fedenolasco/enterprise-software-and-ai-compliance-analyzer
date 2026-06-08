"""PostgreSQL pgvector retrieval over compliance document chunks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from psycopg import connect
from psycopg.rows import dict_row

from agent_brain.config import AgentBrainSettings, get_settings

VECTOR_SEARCH_SQL = """
WITH query_embedding AS (
  SELECT %s::vector AS embedding
)
SELECT
  vendor."vendorCode" AS vendor_code,
  vendor."name" AS vendor_name,
  vendor."aiRiskTier"::text AS vendor_ai_risk_tier,
  software."softwareCode" AS software_code,
  software."name" AS software_name,
  subscription."subscriptionCode" AS subscription_code,
  subscription."annualCostUsd" AS annual_cost_usd,
  subscription."renewalDate" AS renewal_date,
  subscription."status"::text AS subscription_status,
  document."documentCode" AS document_code,
  document."title" AS document_title,
  document."sourcePath" AS source_path,
  chunk."chunkIndex" AS chunk_index,
  chunk."chunkText" AS evidence_excerpt,
  chunk."riskCategory"::text AS risk_category,
  chunk."riskSeverity"::text AS risk_severity,
  chunk."riskScore" AS risk_score,
  chunk.embedding <=> query_embedding.embedding AS distance
FROM "DocumentChunk" chunk
JOIN query_embedding ON TRUE
JOIN "ComplianceDocument" document ON document."id" = chunk."documentId"
LEFT JOIN "Vendor" vendor ON vendor."id" = document."vendorId"
LEFT JOIN "Software" software ON software."id" = document."softwareId"
LEFT JOIN "Subscription" subscription ON subscription."softwareId" = software."id"
WHERE chunk.embedding IS NOT NULL
ORDER BY chunk.embedding <=> query_embedding.embedding ASC,
  vendor."vendorCode" ASC,
  document."documentCode" ASC,
  chunk."chunkIndex" ASC
LIMIT %s;
""".strip()


@dataclass(frozen=True)
class VectorSearchResult:
    """One ranked evidence chunk returned from PostgreSQL vector retrieval."""

    vendor_code: str | None
    vendor_name: str | None
    vendor_ai_risk_tier: str | None
    software_code: str | None
    software_name: str | None
    subscription_code: str | None
    annual_cost_usd: float | None
    renewal_date: str | None
    subscription_status: str | None
    document_code: str
    document_title: str
    source_path: str
    chunk_index: int
    evidence_excerpt: str
    risk_category: str | None
    risk_severity: str | None
    risk_score: float | None
    distance: float


def vector_search(
    query: str,
    settings: AgentBrainSettings | None = None,
    top_k: int | None = None,
) -> list[VectorSearchResult]:
    """Return top matching document chunks for a query string."""

    active_settings = settings or get_settings()
    limit = top_k or active_settings.vector_top_k
    query_embedding = create_deterministic_embedding(query, active_settings.embedding_dimension)
    rows = fetch_vector_search_rows(
        active_settings.database_url,
        to_pgvector_literal(query_embedding),
        limit,
    )
    return [vector_search_result_from_row(row) for row in rows]


def fetch_vector_search_rows(
    database_url: str,
    query_embedding_literal: str,
    top_k: int,
) -> list[dict[str, Any]]:
    """Execute the pgvector similarity query and return raw rows."""

    with connect(_to_psycopg_conninfo(database_url), row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(VECTOR_SEARCH_SQL, (query_embedding_literal, top_k))
            return list(cursor.fetchall())


def vector_search_result_from_row(row: Mapping[str, Any]) -> VectorSearchResult:
    """Convert a database row into a typed vector search result."""

    return VectorSearchResult(
        vendor_code=_optional_str(row.get("vendor_code")),
        vendor_name=_optional_str(row.get("vendor_name")),
        vendor_ai_risk_tier=_optional_str(row.get("vendor_ai_risk_tier")),
        software_code=_optional_str(row.get("software_code")),
        software_name=_optional_str(row.get("software_name")),
        subscription_code=_optional_str(row.get("subscription_code")),
        annual_cost_usd=_optional_float(row.get("annual_cost_usd")),
        renewal_date=_optional_isoformat(row.get("renewal_date")),
        subscription_status=_optional_str(row.get("subscription_status")),
        document_code=str(row["document_code"]),
        document_title=str(row["document_title"]),
        source_path=str(row["source_path"]),
        chunk_index=int(row["chunk_index"]),
        evidence_excerpt=str(row["evidence_excerpt"]),
        risk_category=_optional_str(row.get("risk_category")),
        risk_severity=_optional_str(row.get("risk_severity")),
        risk_score=_optional_float(row.get("risk_score")),
        distance=float(row["distance"]),
    )


def create_deterministic_embedding(input_text: str, dimension: int) -> list[float]:
    """Create the same deterministic placeholder vector used by database ingestion."""

    vector = [0.0 for _ in range(dimension)]
    for index, character in enumerate(input_text):
        slot = index % dimension
        vector[slot] += ord(character) * 0.001
    return [round(value / (index + 1), 6) for index, value in enumerate(vector)]


def to_pgvector_literal(values: Sequence[float]) -> str:
    """Format a Python vector as a pgvector literal."""

    return f"[{','.join(f'{value:.6f}' for value in values)}]"


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _optional_isoformat(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    return str(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _to_psycopg_conninfo(database_url: str) -> str:
    """Remove Prisma-only query parameters before connecting with psycopg."""

    parts = urlsplit(database_url)
    query_pairs = [(key, value) for key, value in parse_qsl(parts.query) if key != "schema"]
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query_pairs), parts.fragment)
    )
