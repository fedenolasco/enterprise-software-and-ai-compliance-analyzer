"""CLI launcher router for executing CLI commands from the UI."""

from __future__ import annotations

import asyncio
import shlex
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ui_api.config import get_settings as get_ui_settings

router = APIRouter(prefix="/api/cli", tags=["cli"])

# Mapping of CLI command names to their module paths and working directories
_CLI_COMMANDS: dict[str, dict[str, Any]] = {
    "validate": {
        "module": "agent_brain.cli.validate_scaffold",
        "working_dir": "agent_brain",
        "description": "Validate scaffold and configuration.",
        "cli_name": "agent-brain-validate",
    },
    "project-graph": {
        "module": "agent_brain.cli.project_graph",
        "working_dir": "agent-brain",
        "description": "Project PostgreSQL data into Neo4j graph.",
        "cli_name": "agent-brain-project-graph",
    },
    "search-vectors": {
        "module": "agent_brain.cli.search_vectors",
        "working_dir": "agent-brain",
        "description": "Search PostgreSQL pgvector compliance chunks.",
        "cli_name": "agent-brain-search-vectors",
        "args": [
            {"name": "query", "required": True, "description": "Query text to search."},
            {"name": "--top-k", "required": False, "description": "Maximum results."},
        ],
    },
    "traverse-graph": {
        "module": "agent_brain.cli.traverse_graph",
        "working_dir": "agent-brain",
        "description": "Traverse Neo4j graph relationships.",
        "cli_name": "agent-brain-traverse-graph",
        "args": [
            {"name": "--vendor-code", "required": False, "description": "Vendor code filter."},
            {"name": "--risk-category", "required": False, "description": "Risk category filter."},
            {"name": "--risk-severity", "required": False, "description": "Risk severity filter."},
            {"name": "--limit", "required": False, "description": "Maximum rows."},
        ],
    },
    "hybrid-retrieve": {
        "module": "agent_brain.cli.hybrid_retrieve",
        "working_dir": "agent-brain",
        "description": "Combine vector and graph retrieval.",
        "cli_name": "agent-brain-hybrid-retrieve",
        "args": [
            {"name": "query", "required": True, "description": "Query text."},
            {"name": "--top-k", "required": False, "description": "Maximum vector results."},
            {"name": "--graph-limit", "required": False, "description": "Maximum graph rows."},
        ],
    },
    "run-curated-demo": {
        "module": "agent_brain.cli.run_curated_demo",
        "working_dir": "agent-brain",
        "description": "Run curated Phase 2 demo queries.",
        "cli_name": "agent-brain-run-curated-demo",
    },
}


class CliRunRequest(BaseModel):
    """Request to run a CLI command."""

    command: str = Field(..., description="CLI command name.")
    args: list[str] = Field(default_factory=list, description="Command arguments.")


@router.get("")
async def list_cli_commands() -> dict[str, Any]:
    """List all available CLI commands with their metadata."""
    return {
        "commands": [
            {
                "name": name,
                "cli_name": meta["cli_name"],
                "description": meta["description"],
                "args": meta.get("args", []),
            }
            for name, meta in _CLI_COMMANDS.items()
        ]
    }


@router.post("/{command}")
async def run_cli_command(command: str, request: CliRunRequest) -> dict[str, Any]:
    """Execute a CLI command and return its output."""
    if command not in _CLI_COMMANDS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown CLI command: {command}. Available: {list(_CLI_COMMANDS.keys())}",
        )

    meta = _CLI_COMMANDS[command]
    settings = get_ui_settings()
    working_dir = settings.repo_root / meta["working_dir"]

    # Build the command
    cmd_args = ["python", "-m", meta["module"]] + request.args
    cli_equivalent = meta["cli_name"] + " " + " ".join(shlex.quote(a) for a in request.args)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(working_dir),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60.0)

        return {
            "command": command,
            "cli_equivalent": cli_equivalent.strip(),
            "exit_code": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "success": proc.returncode == 0,
        }
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"CLI command timed out after 60 seconds: {cli_equivalent}",
        ) from None
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(exc),
                "cli_equivalent": cli_equivalent.strip(),
            },
        ) from exc
