"""Reset router for demo data management at 4 granularity levels."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from psycopg import connect
from pydantic import BaseModel

from agent_brain.config import get_settings as get_agent_brain_settings
from ui_api.config import get_settings as get_ui_settings
from ui_api.routers.workflow import _workflow_states

router = APIRouter(prefix="/api/reset", tags=["reset"])


class ResetResult(BaseModel):
    """Result of a reset operation."""

    success: bool
    message: str
    details: dict[str, Any] = {}


def _get_counts() -> dict[str, int]:
    """Get current record counts from PostgreSQL."""
    settings = get_agent_brain_settings()
    counts: dict[str, int] = {}
    tables = [
        "Vendor",
        "Software",
        "Subscription",
        "ComplianceDocument",
        "DocumentChunk",
        "ComplianceRisk",
        "AuditEvent",
    ]
    with connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            for table in tables:
                cur.execute(f'SELECT COUNT(*) FROM "{table}"')  # type: ignore[arg-type]
                row = cur.fetchone()
                counts[table] = row[0] if row else 0
    return counts


@router.get("/preview")
async def get_reset_preview() -> dict[str, Any]:
    """Dry-run preview of what each reset would affect."""
    try:
        counts = _get_counts()
    except Exception:
        counts = {table: 0 for table in [
            "Vendor", "Software", "Subscription",
            "ComplianceDocument", "DocumentChunk", "ComplianceRisk", "AuditEvent"
        ]}

    return {
        "current_counts": counts,
        "reset_options": {
            "full": {
                "description": "Full environment reset: PostgreSQL + Neo4j + pricing + re-ingest",
                "affected": counts,
                "cli_equivalent": "./scripts/reset-demo-environment.ps1",
            },
            "postgresql": {
                "description": "Reset PostgreSQL demo data only (delete + re-ingest)",
                "affected": counts,
                "cli_equivalent": "cd database-layer && npm run reset:demo -- --yes && npm run ingest",
            },
            "graph": {
                "description": "Reset Neo4j graph only (delete + re-project)",
                "affected": {"Neo4j nodes": "all demo labels", "Neo4j relationships": "all demo types"},
                "cli_equivalent": "cd agent-brain && python scripts/reset_graph.py --yes && python -m agent_brain.cli.project_graph",
            },
            "pricing": {
                "description": "Reset pricing fixture only (restore committed JSON)",
                "affected": {"pricing_records": 3},
                "cli_equivalent": "cd mock-pricing-api && python scripts/reset_pricing_fixture.py",
            },
            "audit": {
                "description": "Clear audit events only (preserve all other data)",
                "affected": {"AuditEvent": counts.get("AuditEvent", 0)},
                "cli_equivalent": "DELETE FROM \"AuditEvent\"",
            },
            "workflow-state": {
                "description": "Clear workflow session state (in-memory only)",
                "affected": {"workflow_threads": len(_workflow_states)},
                "cli_equivalent": "N/A (session-level reset)",
            },
        },
    }


@router.post("/postgresql")
async def reset_postgresql() -> dict[str, Any]:
    """Reset PostgreSQL demo data only (Level 2)."""
    settings = get_ui_settings()
    db_dir = settings.database_layer_dir
    try:
        before = _get_counts()
        proc = await asyncio.create_subprocess_exec(
            "npm", "run", "reset:demo", "--", "--yes",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(db_dir),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60.0)

        if proc.returncode != 0:
            # Try re-ingest
            proc2 = await asyncio.create_subprocess_exec(
                "npm", "run", "ingest",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(db_dir),
            )
            await asyncio.wait_for(proc2.communicate(), timeout=60.0)

        after = _get_counts()
        return {
            "success": True,
            "message": "PostgreSQL demo data reset completed",
            "before": before,
            "after": after,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "cli_equivalent": "cd database-layer && npm run reset:demo -- --yes && npm run ingest",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": str(exc), "remediation": "Ensure PostgreSQL is running and database-layer is installed."},
        ) from exc


@router.post("/graph")
async def reset_graph() -> dict[str, Any]:
    """Reset Neo4j graph only (Level 2)."""
    settings = get_ui_settings()
    agent_dir = settings.agent_brain_dir
    try:
        # Reset graph
        proc1 = await asyncio.create_subprocess_exec(
            "python", "scripts/reset_graph.py", "--yes",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(agent_dir),
        )
        stdout1, stderr1 = await asyncio.wait_for(proc1.communicate(), timeout=30.0)

        # Re-project graph
        proc2 = await asyncio.create_subprocess_exec(
            "python", "-m", "agent_brain.cli.project_graph",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(agent_dir),
        )
        stdout2, stderr2 = await asyncio.wait_for(proc2.communicate(), timeout=30.0)

        return {
            "success": proc1.returncode == 0 and proc2.returncode == 0,
            "message": "Neo4j graph reset and re-projected",
            "reset_output": stdout1.decode("utf-8", errors="replace"),
            "project_output": stdout2.decode("utf-8", errors="replace"),
            "cli_equivalent": "cd agent-brain && python scripts/reset_graph.py --yes && python -m agent_brain.cli.project_graph",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": str(exc), "remediation": "Ensure Neo4j is running."},
        ) from exc


@router.post("/pricing")
async def reset_pricing() -> dict[str, Any]:
    """Reset pricing fixture only (Level 2)."""
    settings = get_ui_settings()
    pricing_dir = settings.mock_pricing_dir
    try:
        proc = await asyncio.create_subprocess_exec(
            "python", "scripts/reset_pricing_fixture.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(pricing_dir),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15.0)
        return {
            "success": proc.returncode == 0,
            "message": "Pricing fixture reset completed",
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "cli_equivalent": "cd mock-pricing-api && python scripts/reset_pricing_fixture.py",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": str(exc)},
        ) from exc


@router.post("/audit")
async def reset_audit() -> dict[str, Any]:
    """Clear audit events only (Level 3)."""
    settings = get_agent_brain_settings()
    try:
        with connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT COUNT(*) FROM "AuditEvent"')  # type: ignore[arg-type]
                row = cur.fetchone()
                before = row[0] if row else 0
                cur.execute('DELETE FROM "AuditEvent"')  # type: ignore[arg-type]
                deleted = cur.rowcount
            conn.commit()
        return {
            "success": True,
            "message": "Audit events cleared",
            "before": before,
            "deleted": deleted,
            "cli_equivalent": 'DELETE FROM "AuditEvent"',
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


@router.post("/workflow-state")
async def reset_workflow_state() -> dict[str, Any]:
    """Clear workflow session state (Level 4)."""
    count = len(_workflow_states)
    _workflow_states.clear()
    return {
        "success": True,
        "message": "Workflow session state cleared",
        "cleared_threads": count,
        "cli_equivalent": "N/A (session-level reset)",
    }


@router.post("/full")
async def reset_full() -> dict[str, Any]:
    """Full environment reset (Level 1 — nuclear option)."""
    settings = get_ui_settings()
    steps: list[dict[str, Any]] = []

    # Step 1: Reset PostgreSQL
    try:
        result = await reset_postgresql()
        steps.append({"step": "reset_postgresql", "success": True, "result": result})
    except HTTPException as exc:
        steps.append({"step": "reset_postgresql", "success": False, "error": exc.detail})

    # Step 2: Reset Neo4j graph
    try:
        result = await reset_graph()
        steps.append({"step": "reset_graph", "success": True, "result": result})
    except HTTPException as exc:
        steps.append({"step": "reset_graph", "success": False, "error": exc.detail})

    # Step 3: Reset pricing fixture
    try:
        result = await reset_pricing()
        steps.append({"step": "reset_pricing", "success": True, "result": result})
    except HTTPException as exc:
        steps.append({"step": "reset_pricing", "success": False, "error": exc.detail})

    # Step 4: Clear workflow state
    try:
        result = await reset_workflow_state()
        steps.append({"step": "reset_workflow_state", "success": True, "result": result})
    except Exception as exc:
        steps.append({"step": "reset_workflow_state", "success": False, "error": str(exc)})

    all_success = all(s["success"] for s in steps)
    return {
        "success": all_success,
        "message": "Full environment reset completed" if all_success else "Full reset completed with some failures",
        "steps": steps,
        "cli_equivalent": "./scripts/reset-demo-environment.ps1",
    }
