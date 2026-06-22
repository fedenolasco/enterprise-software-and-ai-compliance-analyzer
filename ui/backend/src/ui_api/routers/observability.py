"""Observability router for traces, usage events, and audit events with provider filtering."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from psycopg import connect

from agent_brain.config import get_settings as get_agent_brain_settings

router = APIRouter(prefix="/api/observability", tags=["observability"])


def _execute_query(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """Execute a PostgreSQL query and return rows as dicts."""
    settings = get_agent_brain_settings()
    with connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)  # type: ignore[arg-type]
            columns = [desc[0] for desc in cur.description] if cur.description else []
            return [dict(zip(columns, row, strict=False)) for row in cur.fetchall()]


@router.get("/audit")
async def get_audit_events(
    provider: str | None = Query(default=None, description="Filter by model provider."),
    limit: int = Query(default=50, ge=1, le=500),
) -> dict[str, Any]:
    """Get audit events from PostgreSQL, optionally filtered by provider."""
    try:
        if provider:
            rows = _execute_query(
                'SELECT "eventType", "status", "actor", "traceId", "message", '
                '"detail", "createdAt" FROM "AuditEvent" '
                'WHERE "detail"->>\'model_provider\' = %s '
                'ORDER BY "createdAt" DESC LIMIT %s',
                (provider, limit),
            )
        else:
            rows = _execute_query(
                'SELECT "eventType", "status", "actor", "traceId", "message", '
                '"detail", "createdAt" FROM "AuditEvent" '
                'ORDER BY "createdAt" DESC LIMIT %s',
                (limit,),
            )
        return {"audit_events": rows, "count": len(rows), "provider_filter": provider}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "service": "postgres",
                "remediation": "Start PostgreSQL: docker compose up postgres",
                "error": str(exc),
            },
        ) from exc


@router.get("/providers")
async def get_providers() -> dict[str, Any]:
    """List all providers that have observability data."""
    try:
        rows = _execute_query(
            'SELECT DISTINCT "detail"->>\'model_provider\' AS provider '
            'FROM "AuditEvent" '
            'WHERE "detail"->>\'model_provider\' IS NOT NULL '
            'ORDER BY provider'
        )
        providers = [row["provider"] for row in rows if row["provider"]]
        # Always include current provider
        settings = get_agent_brain_settings()
        if settings.model_provider not in providers:
            providers.insert(0, settings.model_provider)
        return {"providers": providers}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "service": "postgres",
                "remediation": "Start PostgreSQL: docker compose up postgres",
                "error": str(exc),
            },
        ) from exc


@router.get("/comparison")
async def get_provider_comparison() -> dict[str, Any]:
    """Get side-by-side provider comparison summary."""
    try:
        rows = _execute_query(
            'SELECT "detail"->>\'model_provider\' AS provider, '
            'COUNT(*) AS workflow_runs, '
            'COALESCE(SUM(("detail"->\'model_usage\'->\'usage\')->>\'prompt_tokens\')::int, 0) AS prompt_tokens, '
            'COALESCE(SUM(("detail"->\'model_usage\'->\'usage\')->>\'completion_tokens\')::int, 0) AS completion_tokens, '
            'COALESCE(SUM(("detail"->\'model_usage\'->>\'simulated_cost_usd\')::float, 0) AS simulated_cost, '
            'COUNT(*) FILTER (WHERE "detail"->>\'decision_outcome\' = \'APPROVED\') AS hitl_approvals, '
            'COUNT(*) FILTER (WHERE "detail"->\'safety_flags\' != \'[]\') AS safety_flags_raised '
            'FROM "AuditEvent" '
            'WHERE "detail"->>\'model_provider\' IS NOT NULL '
            'GROUP BY "detail"->>\'model_provider\' '
            'ORDER BY "detail"->>\'model_provider\''
        )
        return {"comparison": rows, "count": len(rows)}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "service": "postgres",
                "remediation": "Start PostgreSQL: docker compose up postgres",
                "error": str(exc),
            },
        ) from exc


@router.get("/traces")
async def get_traces(
    provider: str | None = Query(default=None, description="Filter by provider."),
) -> dict[str, Any]:
    """Get Phoenix trace spans (if Phoenix is enabled)."""
    settings = get_agent_brain_settings()
    if not settings.phoenix_enabled:
        return {
            "traces": [],
            "count": 0,
            "phoenix_enabled": False,
            "message": "Phoenix is not enabled. Set PHOENIX_ENABLED=true to enable.",
            "remediation": "docker compose --profile observability up",
        }
    # Phoenix traces are stored in Phoenix's own database
    # For now, return audit events that contain trace info
    try:
        if provider:
            rows = _execute_query(
                'SELECT "traceId", "eventType", "message", "detail", "createdAt" '
                'FROM "AuditEvent" '
                'WHERE "detail"->>\'model_provider\' = %s '
                'ORDER BY "createdAt" DESC LIMIT 100',
                (provider,),
            )
        else:
            rows = _execute_query(
                'SELECT "traceId", "eventType", "message", "detail", "createdAt" '
                'FROM "AuditEvent" '
                'ORDER BY "createdAt" DESC LIMIT 100'
            )
        return {
            "traces": rows,
            "count": len(rows),
            "phoenix_enabled": True,
            "phoenix_endpoint": settings.phoenix_endpoint,
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


@router.get("/usage")
async def get_usage_events(
    provider: str | None = Query(default=None, description="Filter by provider."),
) -> dict[str, Any]:
    """Get Langfuse usage events (if Langfuse is enabled)."""
    settings = get_agent_brain_settings()
    if not settings.langfuse_enabled:
        return {
            "usage_events": [],
            "count": 0,
            "langfuse_enabled": False,
            "message": "Langfuse is not enabled. Set LANGFUSE_ENABLED=true to enable.",
            "remediation": "docker compose --profile observability up",
        }
    # Langfuse usage is stored in Langfuse's own database
    # For now, return audit events that contain model usage info
    try:
        if provider:
            rows = _execute_query(
                'SELECT "traceId", "detail"->\'model_usage\' AS usage, "createdAt" '
                'FROM "AuditEvent" '
                'WHERE "detail"->\'model_usage\' IS NOT NULL '
                'AND "detail"->>\'model_provider\' = %s '
                'ORDER BY "createdAt" DESC LIMIT 100',
                (provider,),
            )
        else:
            rows = _execute_query(
                'SELECT "traceId", "detail"->\'model_usage\' AS usage, "createdAt" '
                'FROM "AuditEvent" '
                'WHERE "detail"->\'model_usage\' IS NOT NULL '
                'ORDER BY "createdAt" DESC LIMIT 100'
            )
        return {
            "usage_events": rows,
            "count": len(rows),
            "langfuse_enabled": True,
            "langfuse_host": settings.langfuse_host,
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


@router.delete("/audit")
async def clear_audit_events(
    provider: str | None = Query(default=None, description="Clear only events for this provider."),
) -> dict[str, Any]:
    """Clear audit events, optionally filtered by provider."""
    settings = get_agent_brain_settings()
    try:
        with connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                if provider:
                    cur.execute(
                        'DELETE FROM "AuditEvent" WHERE "detail"->>\'model_provider\' = %s',
                        (provider,),
                    )  # type: ignore[arg-type]
                else:
                    cur.execute('DELETE FROM "AuditEvent"')  # type: ignore[arg-type]
                deleted = cur.rowcount
            conn.commit()
        return {"deleted": deleted, "provider_filter": provider}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "service": "postgres",
                "remediation": "Start PostgreSQL: docker compose up postgres",
                "error": str(exc),
            },
        ) from exc
