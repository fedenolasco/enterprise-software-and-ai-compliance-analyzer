# ADR 0007: Foundry Local Integration and Configuration UI Improvements

## Status

Accepted — 2026-06-22

## Context

The Enterprise Software and AI Compliance Analyzer's Configuration page had several issues that needed to be addressed:

1. **Redacted API key overlap:** The masked OpenAI API key was as long as the original key (100+ asterisks), causing it to overlap adjacent UI elements.
2. **Database credentials exposure:** The `database_url` containing plaintext PostgreSQL credentials was displayed unmasked in the config table.
3. **Stale embedding parameters:** Switching embedding providers did not update `EMBEDDING_MODEL` or `EMBEDDING_DIMENSION`, leaving the config table showing incorrect values.
4. **No Foundry Local model selection:** Users had no way to select or download Foundry Local models from the UI.
5. **No Foundry Local service management:** The service had to be started manually; there was no health check or auto-start integration.
6. **Scroll position loss:** Switching providers caused the page to unmount (loading spinner), losing the user's scroll position.
7. **No installation guidance:** Users had no in-app guidance for installing Foundry Local.
8. **Interpreter mismatch on Windows:** Installing the SDK with the Python launcher can target a different interpreter than the one running the UI backend, leaving the backend unable to import `foundry_local_sdk`.
9. **Dashboard duplication:** Foundry Local appeared as a generic Dashboard health card even though its relevance depends on the selected model provider and its lifecycle is managed on the Configuration page.
10. **Pricing API startup drift:** The Dashboard could show Pricing API unhealthy because the service is a source-tree FastAPI app, not a Docker service or globally installed console script.

## Decision

### 1. Fixed-length masking for sensitive values

Use a fixed number of asterisks (5) instead of one asterisk per character when masking sensitive values. This prevents layout overflow regardless of key length.

- `provider.py::_mask_key()` → `sk-*****gA`
- `config.py::_mask_sensitive()` → `sk****gA`
- `config.py::_mask_connection_string()` → Redacts only the password in connection URLs, keeping host/db visible: `postgresql://user:****@host:5432/db`

### 2. Mark `database_url` as sensitive

The `database_url` is now marked `sensitive: true` in the config metadata and is masked using a dedicated connection-string masker that preserves the username, host, port, and database name while redacting the password.

### 3. Sync embedding parameters on provider switch

When switching embedding providers, the `switch_provider` endpoint now updates `EMBEDDING_MODEL` and `EMBEDDING_DIMENSION` to match the new provider's defaults:

| Provider | `EMBEDDING_MODEL` | `EMBEDDING_DIMENSION` |
|---|---|---|
| `placeholder` | `deterministic-placeholder` | `8` |
| `microsoft-foundry-local` | `all-MiniLM-L6-v2` | `384` |
| `openai` | `text-embedding-3-small` | `1536` |

### 4. Foundry Local model catalog and selector

A curated catalog of Foundry Local chat-completion models is exposed via the `GET /api/provider` endpoint, including device support information (CPU/GPU/NPU):

| Alias | Device | Description |
|---|---|---|
| `qwen2.5-0.5b` | CPU/GPU/NPU auto-select | Small quick-start model used to validate service startup and local inference. |
| `phi-4-mini` | CPU/GPU/NPU auto-select | Compact Microsoft Phi model with a good quality/performance balance. |
| `qwen3-0.6b` | CPU/GPU/NPU auto-select | Small reasoning-capable Qwen model. |
| `phi-4` | CPU/GPU auto-select | Larger Microsoft Phi model for higher-quality local reasoning. |

The `PUT /api/provider/foundry-model` endpoint:
1. Checks if Foundry Local service is running; starts it if not
2. Checks if the model is downloaded; downloads it if not
3. Updates `LOCAL_MODEL_NAME` in `.env`
4. Returns step-by-step progress

### 5. Auto-start Foundry Local service (no auto-stop)

When switching to `microsoft-foundry-local`, the `switch_provider` endpoint automatically starts the Foundry Local service if it's not running. The service is **not** stopped when switching away, because:

- Other applications may be using the service
- Restarting takes time; frequent switches would cause delays
- The service is lightweight when idle

### 6. Silent refetch to preserve scroll position

The `fetchAll` function accepts a `silent` parameter. When `silent=true`, it skips setting `loading(true)`, preventing the page from unmounting to show the loading spinner. All post-action refetches (provider switch, OpenAI settings save, Foundry model save) use `fetchAll(true)`, preserving scroll position.

### 7. Foundry Local Python SDK installation guidance

- `GET /api/provider/foundry-status` checks SDK availability and service status, then returns an install command for the exact interpreter running the UI backend.
- `POST /api/provider/foundry-install` installs the SDK into the backend interpreter with `python -m pip install ...`, using `foundry-local-sdk-winml==1.2.3` on Windows and `foundry-local-sdk==1.2.3` elsewhere.
- Windows uses the `winml` package because it enables Windows ML hardware acceleration when supported by the device.
- The frontend shows an "Install Foundry Local SDK" button when the backend cannot import the SDK, with a "Copy install command" option for manual installation.
- The Configuration page copy explains that the backend must be restarted after SDK installation so the running process can import it.

The UI backend also enforces Python 3.11 at startup. This makes the Foundry Local SDK interpreter choice deterministic: install the SDK into the Python 3.11 backend environment, and run the backend with Python 3.11.

### 8. Model cache directory configuration

- `GET /api/provider/foundry-status` returns the current model cache directory
- `PUT /api/provider/foundry-cache` changes the cache directory via `foundry cache cd <path>`
- The frontend provides a folder picker (using `<input type="file" webkitdirectory>`) so users can browse and select a directory instead of typing a path

### 9. Config page layout reorganization

The config page was reorganized to group related parameters with their switchers:

- **Model Provider Switcher** card contains:
  - Provider selection buttons
  - OpenAI API Key & Model section (only when `openai` is active)
  - Foundry Local Model selector + params (only when `microsoft-foundry-local` is active)
- **Embedding Provider Switcher** card contains:
  - Provider selection buttons
  - Embeddings config table
- Remaining categories (Database, Graph, Observability, Pricing API, Retrieval) rendered in alphabetical order

Duplicate parameters (already shown in status cards or switcher active states) are filtered out from the config tables:
- `model_provider`, `embedding_provider`, `openai_api_key`, `openai_model`, `phoenix_enabled`, `langfuse_enabled`

### 10. Dashboard service-health scope

The Dashboard health grid focuses on always-relevant local services: PostgreSQL, Neo4j, the mock Pricing API, and optional observability tools. Foundry Local is hidden from the Dashboard because it is provider-dependent and already managed on the Configuration page. This avoids a redundant red card when Foundry is disabled or when an SDK-managed endpoint is not currently running.

### 11. Pricing API startup from the UI

The mock Pricing API is treated as a required local service and is included in the Dashboard's required-service auto-start workflow. It is launched from its source tree with the same Python interpreter as the UI backend plus `mock-pricing-api/src` on `PYTHONPATH`, so users do not need a globally installed `mock-pricing-api` command for the Dashboard start button to work.

### 12. Gitignore for large model files

Added patterns to `.gitignore` to exclude Foundry Local model caches and large model artifacts:
- `**/.foundry-local/`, `**/.cache/foundry-local/`
- `*.onnx`, `*.gguf`, `*.bin` (with test fixture exceptions)
- `**/models/*.pt`, `*.pth`, `*.safetensors`
- `**/docker-data/`, `**/pgdata/`, `**/neo4j-data/`

## Consequences

- **Positive:** Users can manage Foundry Local entirely from the UI — install, start, select models, download models, and configure cache location.
- **Positive:** Foundry Local SDK installation targets the actual backend interpreter, reducing Windows Python-version mismatch failures.
- **Positive:** Sensitive credentials are properly masked, preventing accidental exposure.
- **Positive:** The config page is context-aware — only showing relevant sections for the active provider.
- **Positive:** Dashboard health now focuses on the always-relevant local services and no longer duplicates Foundry provider state.
- **Positive:** The mock Pricing API can be started from the UI without a separate manual terminal.
- **Positive:** Scroll position is preserved during provider switches.
- **Positive:** Large model files are excluded from git.
- **Negative:** The Foundry Local SDK-managed web service is process/session scoped, so a backend restart can require starting the service again from the Configuration page.
- **Negative:** Model downloads can take several minutes (2-10 GB), requiring long timeouts and graceful error handling.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Backend Python differs from project baseline Python | SDK installs but backend cannot import it | Installation command uses `sys.executable` from the running backend process |
| Backend accidentally starts with Python 3.14 or another non-baseline interpreter | Foundry SDK appears missing even though it is installed for Python 3.11 | UI backend exits early unless `sys.version_info` is Python 3.11 |
| SDK-managed Foundry endpoint stops after backend restart | Config page shows "Start Service Now" again | Treat the Configuration page as the source of truth and restart the service/model there |
| Model download times out | User sees error but model may still be downloading | 10-minute timeout with clear error message and manual instructions |
| Foundry Local service fails to start | Auto-start warning shown | Warning includes manual start instructions; user can retry |
| Custom model name not in catalog | Model may not be available | Warning returned; user instructed to download manually |
| Pricing API is not installed globally | Dashboard start button fails | Start from source tree with Python 3.11 and explicit `PYTHONPATH` |

## Implementation files

- `ui/backend/src/ui_api/routers/provider.py` — Foundry Local integration, model catalog, install/status/cache endpoints, auto-start
- `ui/backend/src/ui_api/routers/services.py` — Dashboard service startup, including source-tree Pricing API launch
- `ui/backend/src/ui_api/services/health_checker.py` — Dashboard health status details and Pricing API health copy
- `ui/backend/src/ui_api/routers/config.py` — Sensitive value masking, connection string masking
- `ui/frontend/src/app/config/page.tsx` — Config page layout, provider-specific sections, install UI, cache directory picker
- `ui/frontend/src/app/page.tsx` — Dashboard health grid filtering and required-service auto-start messaging
- `.gitignore` — Large model file exclusions
