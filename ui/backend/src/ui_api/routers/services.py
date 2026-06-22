"""Service management router for starting services from the UI."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ui_api.config import get_settings as get_ui_settings
from ui_api.services.health_checker import (
    check_foundry_local,
    check_langfuse,
    check_neo4j,
    check_phoenix,
    check_postgres,
    check_pricing_api,
)

router = APIRouter(prefix="/api/services", tags=["services"])

# Map service names to their Docker Compose service names and start commands
_SERVICE_START_CONFIG: dict[str, dict[str, Any]] = {
    "postgres": {
        "docker_service": "postgres",
        "start_command": "docker compose up -d postgres",
        "description": "PostgreSQL with pgvector",
    },
    "neo4j": {
        "docker_service": "neo4j",
        "start_command": "docker compose up -d neo4j",
        "description": "Neo4j graph database",
    },
    "pricing-api": {
        "docker_service": None,  # Not a Docker service — started manually
        "start_command": "cd mock-pricing-api && python -m mock_pricing_api.main",
        "description": "Mock Pricing API (FastAPI)",
    },
    "phoenix": {
        "docker_service": "phoenix",
        "start_command": "docker compose --profile observability up -d phoenix",
        "description": "Phoenix observability (optional)",
    },
    "langfuse": {
        "docker_service": "langfuse",
        "start_command": "docker compose --profile observability up -d langfuse",
        "description": "Langfuse observability (optional)",
    },
    "foundry-local": {
        "docker_service": None,
        "start_command": None,  # Cannot be started from UI — requires manual installation
        "description": "Microsoft Foundry Local (requires manual setup)",
    },
}

# Map service names to their health check functions
def _ensure_env_file(repo_root: Any) -> None:
    """Ensure .env file exists, copying from .env.example if missing."""
    import shutil
    from pathlib import Path

    root = Path(repo_root)
    env_file = root / ".env"
    env_example = root / ".env.example"
    if not env_file.exists() and env_example.exists():
        shutil.copy2(env_example, env_file)


_HEALTH_CHECKERS = {
    "postgres": check_postgres,
    "neo4j": check_neo4j,
    "pricing-api": check_pricing_api,
    "phoenix": check_phoenix,
    "langfuse": check_langfuse,
    "foundry-local": check_foundry_local,
}


class StartServiceResult(BaseModel):
    """Result of a service start attempt."""

    service: str
    success: bool
    message: str
    output: str = ""
    started: bool = False


@router.post("/auto-start-required")
async def auto_start_required_services() -> dict[str, Any]:
    """Automatically attempt to start required services that are unhealthy.

    This endpoint checks all required services and starts any that are unhealthy
    in the background (fire-and-forget). It returns immediately so the frontend
    doesn't time out waiting. The frontend polls /api/health to see when
    services come up.
    """
    from ui_api.services.health_checker import check_all_services

    services_to_auto_start = ["postgres", "neo4j"]

    # Check current health
    health_results = check_all_services()
    health_map = {h.name: h for h in health_results}

    needs_start = []
    for service_name in services_to_auto_start:
        health = health_map.get(service_name)
        if health and health.status.value == "unhealthy":
            needs_start.append(service_name)

    if not needs_start:
        return {
            "auto_started": [],
            "already_healthy": services_to_auto_start,
            "message": "All required services are already healthy.",
            "summary": {
                "total_checked": len(services_to_auto_start),
                "attempted_start": 0,
                "needs_start": [],
            },
        }

    # Start services in the background (fire-and-forget)
    async def _background_start() -> None:
        for service_name in needs_start:
            try:
                await start_service(service_name)
            except Exception:
                pass  # Silent failure — user can manually start via button

    # Schedule background task
    asyncio.create_task(_background_start())

    return {
        "auto_started": needs_start,
        "already_healthy": [s for s in services_to_auto_start if s not in needs_start],
        "message": f"Auto-starting {len(needs_start)} required service(s) in background: {', '.join(needs_start)}. Health will update shortly.",
        "summary": {
            "total_checked": len(services_to_auto_start),
            "attempted_start": len(needs_start),
            "needs_start": needs_start,
        },
    }


@router.get("/startable")
async def get_startable_services() -> dict[str, Any]:
    """List services that can be started from the UI."""
    startable = []
    for name, config in _SERVICE_START_CONFIG.items():
        if config["start_command"]:
            startable.append({
                "name": name,
                "description": config["description"],
                "start_command": config["start_command"],
                "is_docker": config["docker_service"] is not None,
            })
    return {"services": startable}


@router.post("/{service}/start")
async def start_service(service: str) -> dict[str, Any]:
    """Attempt to start a service from the UI."""
    if service not in _SERVICE_START_CONFIG:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown service: {service}. Available: {list(_SERVICE_START_CONFIG.keys())}",
        )

    config = _SERVICE_START_CONFIG[service]

    if not config["start_command"]:
        return {
            "service": service,
            "success": False,
            "message": f"{config['description']} cannot be started from the UI. It requires manual installation and setup.",
            "started": False,
            "manual_steps": True,
        }

    settings = get_ui_settings()

    # Ensure .env file exists before starting Docker services
    _ensure_env_file(settings.repo_root)

    try:
        # Execute the start command
        parts = config["start_command"].split()

        # Handle cd && command pattern for pricing-api
        if "cd" in parts:
            # Find the cd and the directory
            cd_idx = parts.index("cd")
            dir_name = parts[cd_idx + 1]
            working_dir = settings.repo_root / dir_name
            # Remove "cd", dir_name, and "&&" from parts
            remaining_parts = parts[cd_idx + 3:]  # Skip "cd dir &&"
            proc = await asyncio.create_subprocess_exec(
                *remaining_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(working_dir),
            )
        else:
            proc = await asyncio.create_subprocess_exec(
                *parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(settings.repo_root),
            )

        # For Docker services, the command returns quickly (detached with -d)
        # For non-Docker services like pricing-api, the process runs indefinitely
        if config["docker_service"]:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
            output = stdout.decode("utf-8", errors="replace")
            if stderr:
                output += "\n" + stderr.decode("utf-8", errors="replace")
            success = proc.returncode == 0
        else:
            # Non-Docker service (e.g., pricing-api) — starts as a long-running process
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5.0)
                output = stdout.decode("utf-8", errors="replace")
                if stderr:
                    output += "\n" + stderr.decode("utf-8", errors="replace")
                success = proc.returncode == 0
            except asyncio.TimeoutError:
                # Process is still running — this is expected for a server
                output = "Service process started (running in background)"
                success = True

        # Wait for the service to initialize, then check health
        if success:
            wait_times = {"postgres": 10, "neo4j": 20, "pricing-api": 5, "phoenix": 10, "langfuse": 15}
            wait_time = wait_times.get(service, 5)
            await asyncio.sleep(wait_time)
            checker = _HEALTH_CHECKERS.get(service)
            if checker:
                health = checker()
                started = health.status.value == "healthy"
                if started:
                    message = f"Service started successfully. Health: {health.status.value}"
                else:
                    message = (
                        f"Service start command completed, but health check shows: {health.status.value}. "
                        f"The service may still be initializing. Wait a moment and refresh health."
                    )
            else:
                started = True
                message = "Service started successfully."
        else:
            started = False
            message = f"Failed to start service. Exit code: {proc.returncode}"

        return {
            "service": service,
            "success": success,
            "message": message,
            "output": output,
            "started": started,
        }

    except asyncio.TimeoutError:
        return {
            "service": service,
            "success": False,
            "message": "Service start timed out after 60 seconds. The service may still be starting up.",
            "output": "",
            "started": False,
        }
    except Exception as exc:
        return {
            "service": service,
            "success": False,
            "message": f"Error starting service: {exc}",
            "output": "",
            "started": False,
        }


@router.post("/{service}/restart")
async def restart_service(service: str) -> dict[str, Any]:
    """Attempt to restart a Docker service."""
    if service not in _SERVICE_START_CONFIG:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown service: {service}",
        )

    config = _SERVICE_START_CONFIG[service]
    if not config["docker_service"]:
        return {
            "service": service,
            "success": False,
            "message": f"{service} is not a Docker service and cannot be restarted.",
        }

    settings = get_ui_settings()
    docker_service = config["docker_service"]

    try:
        # Restart the Docker service
        profile_flag = []
        if service in ("phoenix", "langfuse"):
            profile_flag = ["--profile", "observability"]

        proc = await asyncio.create_subprocess_exec(
            "docker", "compose", *profile_flag, "restart", docker_service,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(settings.repo_root),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60.0)

        output = stdout.decode("utf-8", errors="replace")
        if stderr:
            output += "\n" + stderr.decode("utf-8", errors="replace")

        success = proc.returncode == 0

        if success:
            await asyncio.sleep(3)
            checker = _HEALTH_CHECKERS.get(service)
            if checker:
                health = checker()
                started = health.status.value == "healthy"
                message = f"Service restarted. Health: {health.status.value}"
            else:
                started = True
                message = "Service restarted successfully."
        else:
            started = False
            message = f"Failed to restart service. Exit code: {proc.returncode}"

        return {
            "service": service,
            "success": success,
            "message": message,
            "output": output,
            "started": started,
        }

    except Exception as exc:
        return {
            "service": service,
            "success": False,
            "message": f"Error restarting service: {exc}",
            "output": "",
            "started": False,
        }
