"""Provider switching router for changing model and embedding providers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent_brain.config import get_settings as get_agent_brain_settings
from ui_api.config import get_settings as get_ui_settings

router = APIRouter(prefix="/api/provider", tags=["provider"])

VALID_MODEL_PROVIDERS = ["placeholder", "microsoft-foundry-local", "openai"]
VALID_EMBEDDING_PROVIDERS = ["placeholder", "microsoft-foundry-local", "openai"]


class SwitchProviderRequest(BaseModel):
    """Request to switch the model or embedding provider."""

    model_provider: str | None = Field(
        default=None, description="New model provider: placeholder, microsoft-foundry-local, or openai."
    )
    embedding_provider: str | None = Field(
        default=None, description="New embedding provider: placeholder, microsoft-foundry-local, or openai."
    )
    openai_api_key: str | None = Field(
        default=None, description="OpenAI API key (required when switching to openai)."
    )


class UpdateOpenAISettingsRequest(BaseModel):
    """Request to update OpenAI API key and/or model independently of provider switching."""

    openai_api_key: str | None = Field(
        default=None, description="New OpenAI API key. Set to empty string to remove the key."
    )
    openai_model: str | None = Field(
        default=None, description="New OpenAI model name (e.g. gpt-4o-mini, gpt-4o, gpt-4-turbo)."
    )


def _update_env_file(updates: dict[str, str]) -> None:
    """Update the .env file with new values."""
    settings = get_ui_settings()
    env_file = settings.repo_root / ".env"

    if not env_file.exists():
        raise HTTPException(
            status_code=500,
            detail=".env file not found. The backend should have created it on startup.",
        )

    # Read current .env content
    lines = env_file.read_text(encoding="utf-8").splitlines()
    env_keys = {line.split("=", 1)[0].strip() for line in lines if "=" in line and not line.startswith("#")}

    # Update existing keys
    updated_lines = []
    for line in lines:
        if "=" in line and not line.startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in updates:
                updated_lines.append(f"{key}={updates[key]}")
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Add new keys that don't exist yet
    for key, value in updates.items():
        if key not in env_keys:
            updated_lines.append(f"{key}={value}")

    env_file.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")

    # Also update the current process environment so the change takes effect immediately
    for key, value in updates.items():
        os.environ[key] = value


# Curated list of Foundry Local chat-completion model aliases available through
# the Foundry Local SDK/CLI.  Newer CLI preview builds load models with
# ``foundry model load <alias>`` or ``foundry run <alias>``.  See
# https://www.foundrylocal.ai/models for the full catalog.
#
# Foundry Local auto-selects the best variant for the user's hardware (CPU,
# GPU, or NPU) when the base alias is used.  Some models are only available
# on specific devices (e.g. deepseek-r1-14b is NPU-only).  The ``device``
# field indicates which device(s) the model supports.
FOUNDRY_LOCAL_MODELS: list[dict[str, str]] = [
    {
        "alias": "qwen2.5-0.5b",
        "label": "Qwen 2.5 0.5B (small, recommended quick start)",
        "description": "Small chat-completion model used in the Foundry Local README quickstart. Best first download for testing service startup.",
        "device": "CPU/GPU/NPU auto-select",
    },
    {
        "alias": "phi-4-mini",
        "label": "Phi-4 Mini",
        "description": "Compact Microsoft Phi chat model referenced by Foundry Local SDK samples. Good balance of quality and local performance.",
        "device": "CPU/GPU/NPU auto-select",
    },
    {
        "alias": "qwen3-0.6b",
        "label": "Qwen 3 0.6B (reasoning)",
        "description": "Small Qwen reasoning model referenced by Foundry Local CLI 0.10 quick start and SDK tests.",
        "device": "CPU/GPU/NPU auto-select",
    },
    {
        "alias": "phi-4",
        "label": "Phi-4",
        "description": "Larger Microsoft Phi model from the Foundry Local catalog. Higher quality but requires more disk and memory.",
        "device": "CPU/GPU auto-select",
    },
]

_FOUNDRY_DOWNLOAD_JOBS: dict[str, dict[str, Any]] = {}
_FOUNDRY_MANAGER: Any | None = None


@router.get("")
async def get_provider_info() -> dict[str, Any]:
    """Get current provider configuration and available options."""
    settings = get_agent_brain_settings()
    return {
        "current": {
            "model_provider": settings.model_provider,
            "embedding_provider": settings.embedding_provider,
            "foundry_local_endpoint": settings.foundry_local_endpoint,
            "local_model_name": settings.local_model_name,
            "openai_configured": settings.openai_api_key is not None,
            "openai_key_masked": _mask_key(settings.openai_api_key) if settings.openai_api_key else None,
            "openai_model": settings.openai_model,
        },
        "available_model_providers": [
            {
                "value": "placeholder",
                "label": "Placeholder (deterministic, offline)",
                "description": "Uses deterministic placeholder responses. No API key or local model needed. Default for offline validation.",
                "requires_api_key": False,
                "requires_local_runtime": False,
            },
            {
                "value": "microsoft-foundry-local",
                "label": "Microsoft Foundry Local (local AI)",
                "description": "Uses the Foundry Local Python SDK with Windows ML hardware acceleration when available. No cloud API needed; managed on this Configuration page.",
                "requires_api_key": False,
                "requires_local_runtime": True,
            },
            {
                "value": "openai",
                "label": "OpenAI (cloud API)",
                "description": "Uses gpt-4o-mini via the OpenAI API. Requires an API key. Cloud-dependent.",
                "requires_api_key": True,
                "requires_local_runtime": False,
            },
        ],
        "available_embedding_providers": [
            {
                "value": "placeholder",
                "label": "Placeholder (8-dim deterministic)",
                "description": "Uses deterministic 8-dimensional vectors. No API key needed. Default for offline validation.",
                "requires_api_key": False,
            },
            {
                "value": "microsoft-foundry-local",
                "label": "Foundry Local (384-dim)",
                "description": "Uses all-MiniLM-L6-v2 via Foundry Local. Requires Foundry Local installed.",
                "requires_api_key": False,
            },
            {
                "value": "openai",
                "label": "OpenAI (1536-dim)",
                "description": "Uses text-embedding-3-small via OpenAI API. Requires API key. Note: changing embedding dimension requires schema migration and re-ingestion.",
                "requires_api_key": True,
            },
        ],
        "foundry_local_models": FOUNDRY_LOCAL_MODELS,
    }


@router.post("/switch")
async def switch_provider(request: SwitchProviderRequest) -> dict[str, Any]:
    """Switch the model or embedding provider by updating the .env file."""
    updates: dict[str, str] = {}

    if request.model_provider is not None:
        if request.model_provider not in VALID_MODEL_PROVIDERS:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid model provider: {request.model_provider}. Valid options: {VALID_MODEL_PROVIDERS}",
            )

        # Validate OpenAI provider requires API key
        if request.model_provider == "openai":
            settings = get_agent_brain_settings()
            if not settings.openai_api_key and not request.openai_api_key:
                raise HTTPException(
                    status_code=422,
                    detail="OpenAI API key is required when switching to the openai provider. Provide openai_api_key in the request.",
                )
            if request.openai_api_key:
                updates["OPENAI_API_KEY"] = request.openai_api_key

        updates["MODEL_PROVIDER"] = request.model_provider

    if request.embedding_provider is not None:
        if request.embedding_provider not in VALID_EMBEDDING_PROVIDERS:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid embedding provider: {request.embedding_provider}. Valid options: {VALID_EMBEDDING_PROVIDERS}",
            )

        if request.embedding_provider == "openai":
            settings = get_agent_brain_settings()
            if not settings.openai_api_key and not request.openai_api_key:
                raise HTTPException(
                    status_code=422,
                    detail="OpenAI API key is required when switching to the openai embedding provider.",
                )
            if request.openai_api_key and "OPENAI_API_KEY" not in updates:
                updates["OPENAI_API_KEY"] = request.openai_api_key

        updates["EMBEDDING_PROVIDER"] = request.embedding_provider

        # Keep EMBEDDING_MODEL and EMBEDDING_DIMENSION in sync with the new
        # provider so the Embeddings section of the config table stays accurate.
        _EMBEDDING_DEFAULTS: dict[str, dict[str, str]] = {
            "placeholder": {"EMBEDDING_MODEL": "deterministic-placeholder", "EMBEDDING_DIMENSION": "8"},
            "microsoft-foundry-local": {"EMBEDDING_MODEL": "all-MiniLM-L6-v2", "EMBEDDING_DIMENSION": "384"},
            "openai": {"EMBEDDING_MODEL": "text-embedding-3-small", "EMBEDDING_DIMENSION": "1536"},
        }
        defaults = _EMBEDDING_DEFAULTS.get(request.embedding_provider)
        if defaults:
            updates.update(defaults)

    if not updates:
        raise HTTPException(
            status_code=422,
            detail="No provider changes requested. Provide model_provider or embedding_provider.",
        )

    # Update the .env file
    _update_env_file(updates)

    # Read back the updated settings
    # Force reload by clearing any cached settings
    import importlib
    import agent_brain.config as config_module
    importlib.reload(config_module)
    new_settings = config_module.get_settings()

    # Check for embedding dimension mismatch warning
    warnings: list[str] = []

    # Auto-start Foundry Local service when switching to microsoft-foundry-local.
    # We do NOT auto-stop when switching away — the service is lightweight when
    # idle and other applications may be using it.
    foundry_auto_started = False
    if (
        (request.model_provider == "microsoft-foundry-local" or request.embedding_provider == "microsoft-foundry-local")
        and new_settings.foundry_local_endpoint
    ):
        is_running = await _check_foundry_running(new_settings.foundry_local_endpoint)
        if not is_running:
            start_success, start_message, sdk_endpoint = await _start_foundry_runtime(new_settings.foundry_local_endpoint)
            if start_success:
                import asyncio as _asyncio
                await _asyncio.sleep(3)
                foundry_auto_started = True
                if sdk_endpoint and sdk_endpoint.rstrip("/") != new_settings.foundry_local_endpoint.rstrip("/"):
                    updates["FOUNDRY_LOCAL_ENDPOINT"] = sdk_endpoint
                    _update_env_file({"FOUNDRY_LOCAL_ENDPOINT": sdk_endpoint})
            else:
                warnings.append(
                    "Could not auto-start Foundry Local service. "
                    f"Details: {start_message}"
                )
    if request.embedding_provider == "openai" and new_settings.embedding_dimension != 1536:
        warnings.append(
            "Embedding dimension change detected. Switching to OpenAI embeddings (1536-dim) requires "
            "a schema migration, data reset, and re-ingestion. Current dimension is "
            f"{new_settings.embedding_dimension}. Run 'Reset PostgreSQL data' after switching."
        )
    if request.embedding_provider == "microsoft-foundry-local" and new_settings.embedding_dimension != 384:
        warnings.append(
            "Embedding dimension change detected. Foundry Local embeddings use 384-dim. "
            f"Current dimension is {new_settings.embedding_dimension}. A schema migration and re-ingestion may be needed."
        )

    return {
        "success": True,
        "message": "Provider updated successfully. The change takes effect immediately for new workflow runs.",
        "updates": updates,
        "new_settings": {
            "model_provider": new_settings.model_provider,
            "embedding_provider": new_settings.embedding_provider,
        },
        "warnings": warnings,
        "foundry_auto_started": foundry_auto_started,
        "note": "Previous observability data is preserved and tagged with the previous provider. Visit the Observability page to compare providers.",
    }


def _reload_settings() -> Any:
    """Force-reload agent_brain config and return fresh settings."""
    import importlib
    import agent_brain.config as config_module
    importlib.reload(config_module)
    return config_module.get_settings()


class UpdateFoundryModelRequest(BaseModel):
    """Request to update the Foundry Local model name (LOCAL_MODEL_NAME)."""

    local_model_name: str = Field(
        ...,
        description="The Foundry Local model alias to use (e.g. qwen2.5-0.5b, phi-4-mini).",
    )


class DownloadFoundryModelRequest(BaseModel):
    """Request to download a Foundry Local model alias."""

    local_model_name: str = Field(
        ...,
        description="The Foundry Local model alias to download/load (e.g. qwen2.5-0.5b).",
    )


@router.get("/foundry-status")
async def get_foundry_status() -> dict[str, Any]:
    """Check if Foundry Local CLI is installed and the service is running.

    Returns installation status, service status, model cache directory, and
    platform-specific installation instructions if not installed.
    """
    import platform

    # Check if foundry CLI is available
    foundry_installed, version_output = await _run_foundry_cli(["--version"], timeout=10)
    sdk_available = _foundry_sdk_available()

    settings = get_agent_brain_settings()
    endpoint = settings.foundry_local_endpoint
    service_running = await _check_foundry_running(endpoint) if endpoint else False

    # Get current model cache directory
    cache_dir = ""
    if foundry_installed:
        cache_success, cache_output = await _run_foundry_cli(["cache", "location"], timeout=10)
        if cache_success:
            # The CLI output may include extra formatting text; extract the path.
            # Look for a drive letter or path-like pattern in the output.
            import re
            path_match = re.search(r'([A-Za-z]:\\[^\s]+|/[^\s]+|~/[^\s]+)', cache_output)
            if path_match:
                cache_dir = path_match.group(1)
            else:
                cache_dir = cache_output.strip()
    if not cache_dir:
        cache_dir = str(Path.home() / ".foundry" / "cache" / "models")

    # Platform-specific install instructions.  The in-app installer should add
    # the SDK to the same interpreter that is running the UI backend; otherwise
    # installing with the Windows Python launcher can leave the backend unable
    # to import the package until its own virtual environment is updated.
    import sys

    backend_python = sys.executable
    system = platform.system()
    if system == "Windows":
        install_command = f'"{backend_python}" -m pip install foundry-local-sdk-winml==1.2.3'
        install_instructions = (
            "Install the Foundry Local Python SDK into the same Python environment that runs the UI backend:\n"
            f"  {install_command}\n\n"
            "If you are recreating the backend virtual environment from scratch, use the project baseline Python 3.11:\n"
            "  py -3.11 -m pip install -e ui/backend\n\n"
            "The winml package is recommended on Windows for local hardware acceleration. Restart the UI backend after installation."
        )
    elif system == "Darwin":
        install_command = f'"{backend_python}" -m pip install foundry-local-sdk==1.2.3'
        install_instructions = (
            "Install the Foundry Local Python SDK into the same Python environment that runs the UI backend:\n"
            f"  {install_command}\n\n"
            "If you also need the optional legacy CLI on macOS, use Homebrew:\n"
            "  brew tap microsoft/foundrylocal\n"
            "  brew install foundrylocal\n\n"
            "Restart the UI backend after installing the SDK."
        )
    else:
        install_command = f'"{backend_python}" -m pip install foundry-local-sdk==1.2.3'
        install_instructions = (
            "Install the Foundry Local Python SDK into the same Python environment that runs the UI backend:\n"
            f"  {install_command}\n\n"
            "Restart the UI backend after installing the SDK."
        )

    return {
        "installed": foundry_installed or sdk_available,
        "cli_installed": foundry_installed,
        "sdk_available": sdk_available,
        "version": version_output if foundry_installed else "Python SDK",
        "service_running": service_running,
        "endpoint": endpoint,
        "platform": system,
        "install_command": install_command,
        "install_instructions": install_instructions,
        "cache_dir": cache_dir,
    }


class UpdateFoundryCacheRequest(BaseModel):
    """Request to change the Foundry Local model cache directory."""

    cache_dir: str = Field(
        ...,
        description="The new directory path for the Foundry Local model cache.",
    )


@router.put("/foundry-cache")
async def update_foundry_cache(request: UpdateFoundryCacheRequest) -> dict[str, Any]:
    """Change the Foundry Local model cache directory.

    Uses ``foundry cache cd <path>`` to set a custom location for downloaded
    models.  This is useful when the default drive has limited space.
    """
    cache_path = request.cache_dir.strip()
    if not cache_path:
        raise HTTPException(
            status_code=422,
            detail="Cache directory path cannot be empty.",
        )

    # The foundry cache cd CLI command hangs on some systems. Instead of using
    # the CLI, we write directly to the Foundry Local config file
    # (~/.foundry/foundry.config.json) which is more reliable.
    import json
    import pathlib

    config_path = pathlib.Path.home() / ".foundry" / "foundry.config.json"
    default_dir = pathlib.Path.home() / ".foundry" / "cache" / "models"
    requested_path = pathlib.Path(cache_path)
    is_default_reset = requested_path == default_dir

    # Read existing config or create a new one
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            config = {}
    else:
        config = {}

    if is_default_reset:
        # The Foundry default is represented by no custom cacheDirectoryPath.
        # Writing the default path as a custom value can leave Foundry reporting
        # the previous custom path, so remove the override instead.
        if "serviceSettings" in config and "cacheDirectoryPath" in config["serviceSettings"]:
            del config["serviceSettings"]["cacheDirectoryPath"]
    else:
        # Create the directory if it doesn't exist
        try:
            requested_path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Cannot create directory '{cache_path}': {exc}. Please ensure the path is valid and you have write permissions.",
            )

        # Update the cache directory path in the service settings
        if "serviceSettings" not in config:
            config["serviceSettings"] = {}
        config["serviceSettings"]["cacheDirectoryPath"] = cache_path

    # Write the config back
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    # If the service was running, restart it so it picks up the new cache dir
    is_running = await _check_foundry_running(get_agent_brain_settings().foundry_local_endpoint)
    if is_running:
        await _run_foundry_cli_first([["server", "stop"], ["service", "stop"]], timeout=60)
        import asyncio as _asyncio
        await _asyncio.sleep(2)
        await _run_foundry_cli_first([["server", "start"], ["service", "start"]], timeout=120)
        await _asyncio.sleep(3)
        is_running = await _check_foundry_running(get_agent_brain_settings().foundry_local_endpoint)

    if is_default_reset:
        new_cache = str(default_dir)
        message = f"Model cache directory reset to default: {new_cache}"
    else:
        # Verify by reading back the new location
        verify_success, verify_output = await _run_foundry_cli(["cache", "location"], timeout=10)
        # Parse the path from the output (may include extra formatting text)
        if verify_success:
            import re
            path_match = re.search(r'([A-Za-z]:\\[^\s]+|/[^\s]+|~/[^\s]+)', verify_output)
            new_cache = path_match.group(1) if path_match else verify_output.strip()
        else:
            new_cache = cache_path
        message = f"Model cache directory set to '{new_cache}'."

    return {
        "success": True,
        "message": message,
        "cache_dir": new_cache,
    }


@router.post("/foundry-cache/reset")
@router.delete("/foundry-cache")
async def reset_foundry_cache() -> dict[str, Any]:
    """Reset the Foundry Local model cache directory to the default location.

    Removes the ``cacheDirectoryPath`` from the Foundry Local config file,
    reverting to the default (~/.foundry/cache/models).
    """
    import json
    import pathlib

    config_path = pathlib.Path.home() / ".foundry" / "foundry.config.json"

    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            config = {}
    else:
        config = {}

    # Remove the cacheDirectoryPath to revert to default
    if "serviceSettings" in config and "cacheDirectoryPath" in config["serviceSettings"]:
        del config["serviceSettings"]["cacheDirectoryPath"]
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    # If the service was running, restart it so it picks up the default cache dir
    is_running = await _check_foundry_running(get_agent_brain_settings().foundry_local_endpoint)
    if is_running:
        await _run_foundry_cli_first([["server", "stop"], ["service", "stop"]], timeout=60)
        import asyncio as _asyncio
        await _asyncio.sleep(2)
        await _run_foundry_cli_first([["server", "start"], ["service", "start"]], timeout=120)
        await _asyncio.sleep(3)

    # Get the default cache directory
    default_dir = str(pathlib.Path.home() / ".foundry" / "cache" / "models")

    return {
        "success": True,
        "message": f"Model cache directory reset to default: {default_dir}",
        "cache_dir": default_dir,
    }


@router.post("/foundry-install")
async def install_foundry_local() -> dict[str, Any]:
    """Attempt to install the Foundry Local SDK into the backend interpreter.

    On Windows this uses the winml SDK package for local acceleration. On macOS
    and Linux this uses the regular Foundry Local SDK package.
    The installation runs as a subprocess and may take several minutes.
    """
    import asyncio
    import platform
    import sys

    system = platform.system()
    backend_python = sys.executable

    if system == "Windows":
        cmd = [backend_python, "-m", "pip", "install", "foundry-local-sdk-winml==1.2.3"]
        timeout = 300  # 5 minutes
    elif system == "Darwin":
        cmd = [backend_python, "-m", "pip", "install", "foundry-local-sdk==1.2.3"]
        timeout = 120
    else:
        cmd = [backend_python, "-m", "pip", "install", "foundry-local-sdk==1.2.3"]
        timeout = 120

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=_get_full_env(),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = (stdout.decode("utf-8", errors="replace") + stderr.decode("utf-8", errors="replace")).strip()

        if proc.returncode == 0:
            return {
                "success": True,
                "message": "Foundry Local Python SDK installed successfully. Restart the UI backend so the SDK can be imported by the running process.",
                "output": output,
                "installed": True,
            }
        else:
            # pip can return non-zero when the package is already installed and
            # no upgrade is available. Treat this as success.
            already_installed_markers = [
                "already installed",
                "Requirement already satisfied",
                "No available upgrade",
                "No newer package versions",
            ]
            if any(m in output for m in already_installed_markers):
                return {
                    "success": True,
                    "message": "Foundry Local Python SDK is already installed. No upgrade needed.",
                    "output": output,
                    "installed": True,
                }
            return {
                "success": False,
                "message": f"Installation failed (exit code {proc.returncode}). See output for details.",
                "output": output,
                "installed": False,
            }
    except FileNotFoundError:
        return {
            "success": False,
            "message": f"Python interpreter not found for the running backend on {system}: {backend_python}. Please install the Foundry Local Python SDK manually in the backend environment.",
            "output": "",
            "installed": False,
        }
    except asyncio.TimeoutError:
        return {
            "success": False,
            "message": f"Installation timed out after {timeout}s. The process may still be running in the background.",
            "output": "",
            "installed": False,
        }


async def _run_foundry_cli_cmd(args: list[str], timeout: int = 120) -> tuple[bool, str]:
    """Run an arbitrary CLI command (used for brew tap)."""
    import asyncio

    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = (stdout.decode("utf-8", errors="replace") + stderr.decode("utf-8", errors="replace")).strip()
        return proc.returncode == 0, output
    except FileNotFoundError:
        return False, f"Command not found: {args[0]}"
    except asyncio.TimeoutError:
        return False, f"Command timed out after {timeout}s."
    except Exception as exc:
        return False, f"Error: {exc}"


def _get_full_env() -> dict[str, str]:
    """Return the full environment including user-specific PATH entries.

    On Windows, the ``AppData\\Local\\Microsoft\\WindowsApps`` directory (where
    Foundry Local's ``foundry.exe`` is installed via winget) may not be in the
    subprocess PATH.  This function augments the environment with common
    Windows app execution alias paths.
    """
    import os
    import pathlib

    env = dict(os.environ)

    # On Windows, add common app execution alias directories to PATH
    if os.name == "nt":
        home = pathlib.Path.home()
        extra_paths = [
            str(home / "AppData" / "Local" / "Microsoft" / "WindowsApps"),
            str(home / "AppData" / "Local" / "FoundryLocal"),
            str(home / ".local" / "bin"),
        ]
        current_path = env.get("PATH", "")
        for p in extra_paths:
            if p not in current_path:
                current_path = current_path + os.pathsep + p
        env["PATH"] = current_path

    return env


async def _run_foundry_cli(args: list[str], timeout: int = 120) -> tuple[bool, str]:
    """Run a Foundry Local CLI command and return (success, output).

    Args:
        args: CLI arguments to pass to the ``foundry`` command.
        timeout: Maximum seconds to wait for the command.

    Returns:
        A tuple of (success, combined stdout+stderr output).
    """
    import asyncio

    try:
        proc = await asyncio.create_subprocess_exec(
            "foundry", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=_get_full_env(),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = (stdout.decode("utf-8", errors="replace") + stderr.decode("utf-8", errors="replace")).strip()
        return proc.returncode == 0, output
    except FileNotFoundError:
        return False, "Foundry Local CLI ('foundry') not found. Please install Foundry Local first."
    except asyncio.TimeoutError:
        return False, f"Foundry Local command timed out after {timeout}s."
    except Exception as exc:
        return False, f"Error running foundry command: {exc}"


async def _run_foundry_cli_first(commands: list[list[str]], timeout: int = 120) -> tuple[bool, str]:
    """Run Foundry CLI commands in order and return the first successful result.

    This keeps compatibility with both the older service-based CLI and the newer
    CLI 0.10 preview command surface.
    """
    outputs: list[str] = []
    for args in commands:
        success, output = await _run_foundry_cli(args, timeout=timeout)
        if success:
            return True, output
        outputs.append(f"foundry {' '.join(args)}: {output}")
    return False, "\n".join(outputs)


async def _check_foundry_running(endpoint: str | None) -> bool:
    """Check if Foundry Local service is running by hitting its endpoint."""
    if not endpoint:
        return False
    import urllib.request

    try:
        req = urllib.request.Request(f"{endpoint.rstrip('/')}/v1/models", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


async def _check_model_downloaded(alias: str) -> bool:
    """Best-effort check if a model alias appears locally available.

    Newer Foundry Local CLI builds use ``model list`` for the available catalog,
    so callers that need to ensure local readiness should still run
    ``foundry model load <alias>``. Loading is idempotent and downloads on first
    use when needed.
    """
    success, output = await _run_foundry_cli(["model", "list"], timeout=30)
    if not success:
        return False
    # The output contains lines like: "qwen2.5-0.5b  CPU  chat-completion  ..."
    # Check if the alias appears in the list (and is cached/available).
    return alias in output


def _model_alias_is_curated(alias: str) -> bool:
    """Return whether the alias is in the curated downloadable Foundry list."""
    return alias in {m["alias"] for m in FOUNDRY_LOCAL_MODELS}


def _get_foundry_manager() -> Any:
    """Return a lazily initialized Foundry Local SDK manager.

    The SDK is the preferred model-management path.  CLI functions remain as a
    compatibility fallback for environments where the SDK is not installed yet.
    """
    global _FOUNDRY_MANAGER
    if _FOUNDRY_MANAGER is not None:
        return _FOUNDRY_MANAGER

    from foundry_local_sdk import Configuration, FoundryLocalManager  # type: ignore[import-not-found]

    config = Configuration(app_name="enterprise_compliance_analyzer_ui")
    FoundryLocalManager.initialize(config)
    _FOUNDRY_MANAGER = FoundryLocalManager.instance
    return _FOUNDRY_MANAGER


def _try_get_foundry_model(alias: str) -> Any | None:
    """Return a Foundry SDK model object, or None if SDK/catalog lookup fails."""
    try:
        manager = _get_foundry_manager()
        return manager.catalog.get_model(alias)
    except Exception:
        return None


def _foundry_sdk_available() -> bool:
    """Return whether the Foundry Local Python SDK can be imported and initialized."""
    try:
        _get_foundry_manager()
        return True
    except Exception:
        return False


def _start_foundry_sdk_web_service() -> tuple[bool, str, str | None]:
    """Start the SDK-managed OpenAI-compatible web service if possible."""
    try:
        manager = _get_foundry_manager()
        manager.start_web_service()
        urls = getattr(manager, "urls", []) or []
        endpoint = str(urls[0]).rstrip("/") if urls else None
        return True, f"Foundry Local SDK web service started at {endpoint or 'an SDK-managed URL'}.", endpoint
    except Exception as exc:
        return False, f"Could not start Foundry Local SDK web service: {exc}", None


async def _start_foundry_runtime(endpoint: str | None = None) -> tuple[bool, str, str | None]:
    """Start Foundry Local using the Python SDK first, then CLI fallback.

    Returns ``(success, message, endpoint)``.  The endpoint is the SDK web
    service URL when the SDK path succeeds; otherwise it is the configured
    endpoint supplied by the caller.
    """
    sdk_success, sdk_message, sdk_endpoint = _start_foundry_sdk_web_service()
    if sdk_success:
        return True, sdk_message, sdk_endpoint

    cli_success, cli_output = await _run_foundry_cli_first([
        ["server", "start"],
        ["service", "start"],
    ], timeout=60)
    if cli_success:
        return True, cli_output or "Foundry Local CLI service started.", endpoint

    return False, f"{sdk_message}\n{cli_output}", endpoint


def _append_sdk_progress(job: dict[str, Any], percent: float) -> None:
    """Store SDK progress in the shared download-job shape used by the UI."""
    safe_percent = max(0, min(100, int(float(percent))))
    job["percent"] = safe_percent
    message = f"Downloading... {safe_percent}%"
    job["message"] = message
    job["output"].append(message)


async def _run_foundry_download_job(job_id: str, alias: str) -> None:
    """Download/load a Foundry model in the background and store progress lines."""
    import asyncio
    import re

    job = _FOUNDRY_DOWNLOAD_JOBS[job_id]
    job["status"] = "running"
    job["message"] = f"Loading {alias}; Foundry downloads it automatically if needed..."

    model = _try_get_foundry_model(alias)
    if model is not None:
        try:
            job["message"] = f"Downloading {alias} with Foundry Local Python SDK..."
            await asyncio.to_thread(model.download, lambda p: _append_sdk_progress(job, p))
            job["message"] = f"Loading {alias} with Foundry Local Python SDK..."
            await asyncio.to_thread(model.load)
            job.update({
                "status": "complete",
                "message": f"Model '{alias}' downloaded and loaded successfully.",
                "percent": 100,
            })
            return
        except Exception as exc:
            job["output"].append(f"SDK path failed, falling back to CLI: {exc}")
            job["message"] = "SDK path failed, falling back to CLI..."

    try:
        proc = await asyncio.create_subprocess_exec(
            "foundry", "model", "load", alias,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=_get_full_env(),
        )
    except FileNotFoundError:
        job.update({
            "status": "error",
            "message": "Foundry Local CLI ('foundry') not found. Please install Foundry Local first.",
            "percent": 0,
        })
        return
    except Exception as exc:
        job.update({"status": "error", "message": f"Could not start download: {exc}", "percent": 0})
        return

    assert proc.stdout is not None
    percent_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*%")

    while True:
        raw = await proc.stdout.readline()
        if not raw:
            break
        line = raw.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        job["output"].append(line)
        job["message"] = line
        match = percent_pattern.search(line)
        if match:
            job["percent"] = max(0, min(100, int(float(match.group(1)))))

    return_code = await proc.wait()
    if return_code == 0:
        job.update({
            "status": "complete",
            "message": f"Model '{alias}' loaded successfully.",
            "percent": 100,
        })
    else:
        job.update({
            "status": "error",
            "message": f"Model '{alias}' load failed with exit code {return_code}.",
        })


@router.post("/foundry-model/download")
async def start_foundry_model_download(request: DownloadFoundryModelRequest) -> dict[str, Any]:
    """Start loading a curated Foundry Local model alias in the background.

    Foundry Local CLI 0.10 downloads the model automatically as part of
    ``foundry model load <alias>`` when it is not already cached.
    """
    import asyncio
    import uuid

    alias = request.local_model_name.strip()
    if not alias:
        raise HTTPException(status_code=422, detail="Foundry Local model alias cannot be empty.")
    if not _model_alias_is_curated(alias):
        raise HTTPException(
            status_code=422,
            detail=f"'{alias}' is not in the verified downloadable Foundry Local alias list.",
        )
    existing = next(
        (
            job
            for job in _FOUNDRY_DOWNLOAD_JOBS.values()
            if job.get("model") == alias and job.get("status") in {"queued", "running"}
        ),
        None,
    )
    if existing:
        return existing

    job_id = str(uuid.uuid4())
    job: dict[str, Any] = {
        "job_id": job_id,
        "model": alias,
        "status": "queued",
        "message": f"Queued load for {alias}.",
        "percent": 0,
        "output": [],
    }
    _FOUNDRY_DOWNLOAD_JOBS[job_id] = job
    asyncio.create_task(_run_foundry_download_job(job_id, alias))
    return job


@router.get("/foundry-model/download/{job_id}")
async def get_foundry_model_download(job_id: str) -> dict[str, Any]:
    """Return current status for a Foundry Local model download job."""
    job = _FOUNDRY_DOWNLOAD_JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Download job not found: {job_id}")
    return job


@router.put("/foundry-model")
async def update_foundry_model(request: UpdateFoundryModelRequest) -> dict[str, Any]:
    """Update the Foundry Local model name and ensure the runtime is ready.

    This endpoint:
    1. Validates the model name.
    2. Checks if Foundry Local service is running; if not, attempts to start it.
    3. Checks if the selected model is downloaded; if not, triggers a download.
    4. Updates LOCAL_MODEL_NAME in .env.
    5. Returns status information for the frontend to display.
    """
    model = request.local_model_name.strip()
    if not model:
        raise HTTPException(
            status_code=422,
            detail="Foundry Local model name cannot be empty.",
        )

    # Validate against the curated catalog (allow custom names too, but warn).
    catalog_warning = None
    if not _model_alias_is_curated(model):
        catalog_warning = (
            f"'{model}' is not in the curated Foundry Local catalog. "
            "Make sure the model is available in the Foundry Local catalog."
        )

    # Get current settings for the endpoint
    settings = get_agent_brain_settings()
    endpoint = settings.foundry_local_endpoint

    steps: list[dict[str, str]] = []
    warnings: list[str] = []

    # Step 1: Check if Foundry Local service is running
    is_running = await _check_foundry_running(endpoint)
    if is_running:
        steps.append({"step": "service_check", "status": "ok", "message": "Foundry Local service is running."})
    else:
        steps.append({"step": "service_check", "status": "warning", "message": "Foundry Local service is not running. Attempting to start..."})
        # Try to start the SDK-managed web service first, with CLI fallback for older installs.
        start_success, start_output, sdk_endpoint = await _start_foundry_runtime(endpoint)
        if start_success:
            steps.append({"step": "service_start", "status": "ok", "message": "Foundry Local service started successfully."})
            if sdk_endpoint and (endpoint is None or sdk_endpoint.rstrip("/") != endpoint.rstrip("/")):
                endpoint = sdk_endpoint
                _update_env_file({"FOUNDRY_LOCAL_ENDPOINT": sdk_endpoint})
            # Wait a moment for the service to initialize
            import asyncio
            await asyncio.sleep(3)
            is_running = await _check_foundry_running(endpoint)
            if not is_running:
                steps.append({"step": "service_verify", "status": "warning", "message": "Service started but endpoint not yet responding. It may still be initializing."})
        else:
            steps.append({"step": "service_start", "status": "error", "message": f"Could not start Foundry Local service: {start_output}"})
            warnings.append(
                "Foundry Local service could not be started automatically. "
                "The old native CLI has been removed; restart the UI backend under Python 3.11 so it can import foundry-local-sdk-winml. "
                f"Details: {start_output}"
            )

    # Step 2: Load the model. Newer Foundry Local CLI builds automatically
    # download on first load, so loading is the most reliable readiness check.
    model_downloaded = await _check_model_downloaded(model)
    steps.append({"step": "model_download", "status": "info", "message": f"Loading '{model}'. Foundry downloads it automatically if needed..."})
    sdk_model = _try_get_foundry_model(model)
    if sdk_model is not None:
        import asyncio
        try:
            await asyncio.to_thread(sdk_model.download)
            await asyncio.to_thread(sdk_model.load)
            download_success = True
            download_output = "Loaded with Foundry Local Python SDK."
        except Exception as exc:
            download_success = False
            download_output = f"Foundry Local Python SDK load failed: {exc}"
    else:
        download_success, download_output = await _run_foundry_cli_first([
            ["model", "load", model],
            ["model", "download", model],
        ], timeout=600)
    if download_success:
        model_downloaded = True
        steps.append({"step": "model_download_complete", "status": "ok", "message": f"Model '{model}' loaded successfully."})
    else:
        steps.append({"step": "model_download_complete", "status": "error", "message": f"Model load failed: {download_output}"})
        warnings.append(
            f"Model '{model}' could not be loaded automatically. "
            "Restart the UI backend under Python 3.11 so it can import foundry-local-sdk-winml, then use the Download Model button."
        )

    # Step 3: Update LOCAL_MODEL_NAME in .env
    _update_env_file({"LOCAL_MODEL_NAME": model})
    new_settings = _reload_settings()

    if catalog_warning:
        warnings.append(catalog_warning)

    return {
        "success": True,
        "message": f"Foundry Local model set to '{model}'. Changes take effect immediately for new workflow runs.",
        "local_model_name": new_settings.local_model_name,
        "warning": catalog_warning,
        "warnings": warnings,
        "steps": steps,
        "service_running": is_running,
        "model_downloaded": model_downloaded,
    }


@router.put("/openai-settings")
async def update_openai_settings(request: UpdateOpenAISettingsRequest) -> dict[str, Any]:
    """Update the OpenAI API key and/or model independently of provider switching.

    Writes changes to the root .env file and updates the running process
    environment so the change takes effect immediately.
    """
    updates: dict[str, str] = {}

    if request.openai_api_key is not None:
        key = request.openai_api_key.strip()
        if key:
            # Basic validation: OpenAI keys start with "sk-"
            if not key.startswith("sk-"):
                raise HTTPException(
                    status_code=422,
                    detail="OpenAI API key should start with 'sk-'. Please check the key and try again.",
                )
            updates["OPENAI_API_KEY"] = key
        else:
            # Empty string means remove the key
            updates["OPENAI_API_KEY"] = ""

    if request.openai_model is not None:
        model = request.openai_model.strip()
        if not model:
            raise HTTPException(
                status_code=422,
                detail="OpenAI model name cannot be empty.",
            )
        updates["OPENAI_MODEL"] = model

    if not updates:
        raise HTTPException(
            status_code=422,
            detail="No changes requested. Provide openai_api_key and/or openai_model.",
        )

    # Write to .env file
    _update_env_file(updates)

    # Reload settings to reflect changes
    new_settings = _reload_settings()

    # Build response
    key_status = "configured" if new_settings.openai_api_key else "not_set"
    masked_key = _mask_key(new_settings.openai_api_key) if new_settings.openai_api_key else None

    changed: list[str] = []
    if "OPENAI_API_KEY" in updates:
        changed.append("API key")
    if "OPENAI_MODEL" in updates:
        changed.append("model")

    return {
        "success": True,
        "message": f"OpenAI {' and '.join(changed)} updated successfully. Changes take effect immediately for new workflow runs.",
        "openai_configured": new_settings.openai_api_key is not None,
        "openai_key_status": key_status,
        "openai_key_masked": masked_key,
        "openai_model": new_settings.openai_model,
        "updates": updates,
    }


@router.delete("/openai-key")
async def remove_openai_key() -> dict[str, Any]:
    """Remove the OpenAI API key from the .env file.

    This comments out or clears the OPENAI_API_KEY line in .env and
    removes it from the running process environment.
    """
    # Clear from process environment
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]

    # Write empty value to .env (effectively removes the key)
    _update_env_file({"OPENAI_API_KEY": ""})

    # Reload settings
    new_settings = _reload_settings()

    return {
        "success": True,
        "message": "OpenAI API key removed. The key is no longer available for new workflow runs.",
        "openai_configured": new_settings.openai_api_key is not None,
        "openai_key_status": "not_set",
        "openai_key_masked": None,
        "openai_model": new_settings.openai_model,
    }


def _mask_key(key: str) -> str:
    """Mask an API key for display, showing only first 3 and last 2 characters.

    Uses a fixed number of asterisks so the masked representation does not grow
    with the key length (which previously caused the displayed value to overlap
    adjacent UI elements such as the OpenAI model box).
    """
    if not key:
        return ""
    if len(key) <= 5:
        return "*" * len(key)
    return key[:3] + "*****" + key[-2:]
