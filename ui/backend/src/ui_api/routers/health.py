"""Health check router for service status monitoring."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import time
import uuid
from typing import Any, Callable, cast

from fastapi import APIRouter

from ui_api.services.health_checker import (
    ServiceName,
    check_all_services,
    check_foundry_local,
    check_langfuse,
    check_neo4j,
    check_phoenix,
    check_postgres,
    check_pricing_api,
)

router = APIRouter(prefix="/api/health", tags=["health"])

_SERVICE_CHECKERS = {
    ServiceName.POSTGRES.value: check_postgres,
    ServiceName.NEO4J.value: check_neo4j,
    ServiceName.PRICING_API.value: check_pricing_api,
    ServiceName.PHOENIX.value: check_phoenix,
    ServiceName.LANGFUSE.value: check_langfuse,
    ServiceName.FOUNDRY_LOCAL.value: check_foundry_local,
}

_HARDWARE_JOBS: dict[str, dict[str, Any]] = {}
_HARDWARE_CACHE: dict[str, Any] | None = None
_HARDWARE_CACHE_TS = 0.0
_HARDWARE_CACHE_TTL_SECONDS = 15.0


@router.get("")
async def get_health() -> dict[str, Any]:
    """Get aggregate health of all connected services."""
    services = check_all_services()
    return {
        "services": [s.to_dict() for s in services],
        "summary": {
            "total": len(services),
            "healthy": sum(1 for s in services if s.status.value == "healthy"),
            "unhealthy": sum(1 for s in services if s.status.value == "unhealthy"),
            "disabled": sum(1 for s in services if s.status.value == "disabled"),
        },
    }


def _run_powershell_json(command: str, timeout: int = 5) -> Any:
    """Run PowerShell and parse JSON output best-effort."""
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:
        return {"error": str(exc)}
    if proc.returncode != 0 or not proc.stdout.strip():
        return {"error": proc.stderr.strip() or f"PowerShell exited with {proc.returncode}"}
    try:
        return json.loads(proc.stdout)
    except Exception as exc:
        return {"error": f"Could not parse PowerShell JSON: {exc}", "raw": proc.stdout.strip()}


def _collect_hardware_status() -> dict[str, Any]:
    """Collect best-effort local hardware telemetry without blocking page load."""
    result: dict[str, Any] = {
        "platform": platform.platform(),
        "system": platform.system(),
        "cpu": {"logical_cores": os.cpu_count() or 0, "usage_percent": None},
        "memory": {"total_gb": None, "available_gb": None, "used_percent": None},
        "gpu": {"controllers": [], "usage_percent": None},
        "npu": {"controllers": []},
        "local_ai_processes": [],
        "notes": [],
        "collected_at": time.time(),
    }

    if platform.system() != "Windows":
        result["notes"].append("Detailed GPU/NPU telemetry is best-effort on Windows. CPU/RAM fallback is available cross-platform.")
        # Cross-platform lightweight fallback via Python stdlib.
        try:
            getloadavg = getattr(os, "getloadavg", None)
            if callable(getloadavg):
                load_1, _, _ = cast(Callable[[], tuple[float, float, float]], getloadavg)()
                cores = max(1, os.cpu_count() or 1)
                result["cpu"]["usage_percent"] = round(min(100.0, (load_1 / cores) * 100), 1)
        except Exception:
            pass
        return result

    counters = _run_powershell_json(
        "$cpu=(Get-Counter '\\Processor(_Total)\\% Processor Time').CounterSamples.CookedValue;"
        "$os=Get-CimInstance Win32_OperatingSystem;"
        "[pscustomobject]@{cpu=[math]::Round($cpu,1);"
        "total=[math]::Round($os.TotalVisibleMemorySize/1MB,2);"
        "available=[math]::Round($os.FreePhysicalMemory/1MB,2);"
        "used=[math]::Round((($os.TotalVisibleMemorySize-$os.FreePhysicalMemory)/$os.TotalVisibleMemorySize)*100,1)}"
        "|ConvertTo-Json -Compress"
    )
    if isinstance(counters, dict) and "error" not in counters:
        result["cpu"]["usage_percent"] = counters.get("cpu")
        result["memory"].update({
            "total_gb": counters.get("total"),
            "available_gb": counters.get("available"),
            "used_percent": counters.get("used"),
        })
    elif isinstance(counters, dict):
        result["notes"].append(f"CPU/RAM telemetry unavailable: {counters.get('error')}")

    devices = _run_powershell_json(
        "$gpus=Get-CimInstance Win32_VideoController|Select-Object Name,AdapterRAM,DriverVersion;"
        "$npus=Get-PnpDevice -PresentOnly|Where-Object {($_.Class -eq 'ComputeAccelerator' -and $_.FriendlyName -match 'AI Boost|Neural|NPU') -or ($_.FriendlyName -match '\\bNPU\\b|AI Boost|Neural Processor')}|Select-Object FriendlyName,Status,Class,InstanceId;"
        "[pscustomobject]@{gpus=$gpus;npus=$npus}|ConvertTo-Json -Compress -Depth 4"
    )
    if isinstance(devices, dict) and "error" not in devices:
        gpus = devices.get("gpus") or []
        npus = devices.get("npus") or []
        result["gpu"]["controllers"] = [gpus] if isinstance(gpus, dict) else gpus
        result["npu"]["controllers"] = [npus] if isinstance(npus, dict) else npus
    elif isinstance(devices, dict):
        result["notes"].append(f"GPU/NPU inventory unavailable: {devices.get('error')}")

    gpu_usage = _run_powershell_json(
        "$samples=Get-Counter '\\GPU Engine(*)\\Utilization Percentage' -ErrorAction SilentlyContinue;"
        "$sum=0; if ($samples) { $sum=($samples.CounterSamples|Measure-Object CookedValue -Sum).Sum };"
        "[pscustomobject]@{usage=[math]::Round($sum,1)}|ConvertTo-Json -Compress"
    )
    if isinstance(gpu_usage, dict) and "error" not in gpu_usage:
        result["gpu"]["usage_percent"] = gpu_usage.get("usage")

    processes = _run_powershell_json(
        "$names=@('ovms','foundry','python');"
        "$procs=Get-Process|Where-Object {$names -contains $_.ProcessName}|Select-Object ProcessName,Id,@{n='WorkingSetMB';e={[math]::Round($_.WorkingSet64/1MB,1)}};"
        "$procs|ConvertTo-Json -Compress",
    )
    if isinstance(processes, list):
        result["local_ai_processes"] = processes
    elif isinstance(processes, dict) and "error" not in processes:
        result["local_ai_processes"] = [processes]

    mem_used = result["memory"].get("used_percent")
    gpu_used = result["gpu"].get("usage_percent")
    if isinstance(mem_used, (int, float)) and mem_used >= 85:
        result["notes"].append("System memory usage is high. Stop unused local AI runtimes or use a cloud/placeholder provider.")
    if isinstance(gpu_used, (int, float)) and gpu_used >= 85:
        result["notes"].append("GPU utilization is high. Local runtime switching may feel slow.")
    if result["npu"]["controllers"]:
        result["notes"].append("NPU memory availability is not exposed by standard Windows performance counters on this system; OVMS/OpenVINO can use the NPU, but this panel can only show NPU presence.")
    return result


async def _run_hardware_job(job_id: str) -> None:
    """Collect hardware telemetry in a background job."""
    import asyncio

    global _HARDWARE_CACHE, _HARDWARE_CACHE_TS
    job = _HARDWARE_JOBS[job_id]
    job.update({"status": "running", "message": "Collecting CPU/RAM/GPU/NPU telemetry...", "percent": 25})
    try:
        telemetry = await asyncio.to_thread(_collect_hardware_status)
        _HARDWARE_CACHE = telemetry
        _HARDWARE_CACHE_TS = time.time()
        job.update({"status": "complete", "message": "Hardware telemetry refreshed.", "percent": 100, "result": telemetry})
    except Exception as exc:
        job.update({"status": "error", "message": f"Hardware telemetry failed: {exc}", "percent": 100})


@router.post("/hardware/refresh")
async def refresh_hardware_status() -> dict[str, Any]:
    """Queue a background hardware telemetry refresh job."""
    import asyncio

    job_id = str(uuid.uuid4())
    job = {"job_id": job_id, "status": "queued", "message": "Queued hardware telemetry refresh.", "percent": 0}
    _HARDWARE_JOBS[job_id] = job
    asyncio.create_task(_run_hardware_job(job_id))
    return job


@router.get("/hardware/job/{job_id}")
async def get_hardware_job(job_id: str) -> dict[str, Any]:
    """Return current status for a hardware telemetry refresh job."""
    from fastapi import HTTPException

    job = _HARDWARE_JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Hardware telemetry job not found: {job_id}")
    return job


@router.get("/hardware")
async def get_hardware_status() -> dict[str, Any]:
    """Return cached hardware telemetry immediately, or a lightweight placeholder."""
    if _HARDWARE_CACHE is not None and (time.time() - _HARDWARE_CACHE_TS) <= _HARDWARE_CACHE_TTL_SECONDS:
        return {"status": "cached", "result": _HARDWARE_CACHE}
    return {
        "status": "stale",
        "message": "Hardware telemetry is stale or not collected yet. Use /api/health/hardware/refresh to queue a refresh.",
        "result": _HARDWARE_CACHE,
    }


@router.get("/{service}")
async def get_service_health(service: str) -> dict[str, Any]:
    """Get health of a specific service."""
    checker = _SERVICE_CHECKERS.get(service)
    if checker is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Unknown service: {service}. Valid services: {list(_SERVICE_CHECKERS.keys())}",
        )
    result = checker()
    return result.to_dict()
