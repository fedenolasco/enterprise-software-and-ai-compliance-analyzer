# ADR 0008: OpenVINO Model Server Provider for Local Inference and Embeddings

## Status

Accepted â€” 2026-06-23

## Context

Microsoft Foundry Local provides a local model runtime and now has a grounded embedding sample using `qwen3-embedding-0.6b`, while OpenVINO Model Server remains the project's NPU-first local serving path for OpenVINO-optimized LLM and embedding models. The product needs local providers that can support both text inference and semantic embeddings, preferably with Intel AI Boost NPU acceleration.

OpenVINO Model Server (OVMS) exposes OpenAI-compatible APIs for text generation and embeddings, and OpenVINO 2026 documentation confirms NPU deployment patterns plus embedding support. Hugging Face hosts public OpenVINO-optimized models, including Qwen text-generation models and Qwen3 embedding models.

## Decision

Add `openvino` as a fourth model and embedding provider alongside `placeholder`, `microsoft-foundry-local`, and `openai`.

The OpenVINO integration uses Architecture A: **OVMS as an external local server**, with native Windows bare-metal OVMS as the primary runtime path.

```text
Application code -> OpenAI-compatible client -> native Windows OpenVINO Model Server -> Intel NPU/GPU/CPU
```

This keeps code changes close to the existing Foundry Local integration because both expose OpenAI-compatible API surfaces. OVMS is intentionally run outside Docker on Windows so it can use Intel AI Boost NPU, Intel GPU, or CPU directly without container device-passthrough limitations.

## Provider configuration

The OpenVINO provider uses these environment variables:

| Variable | Purpose | Default |
|---|---|---|
| `MODEL_PROVIDER` | Selects LLM provider | `openvino` when active |
| `EMBEDDING_PROVIDER` | Selects embedding provider | `openvino` when active |
| `OPENVINO_ENDPOINT` | OVMS base endpoint | `http://localhost:8100` |
| `OPENVINO_MODEL` | Text-generation model ID | `OpenVINO/Qwen3-8B-int4-cw-ov` |
| `OPENVINO_EMBEDDING_MODEL` | Embedding model ID | `OpenVINO/Qwen3-Embedding-0.6B-int8-ov` |
| `OPENVINO_DEVICE` | Preferred target device | `NPU` |
| `OPENVINO_OVMS_PATH` | Optional absolute path to `ovms.exe` when it is not on `PATH` | unset |
| `HF_TOKEN` | Optional Hugging Face token | unset |

`HF_TOKEN` is optional for public OpenVINO models. It is only required for gated/private models or to avoid anonymous download limits.

## Consequences

- **Positive:** The project gains a local embedding provider with a verified OpenVINO embedding model path.
- **Positive:** OpenVINO can target Intel AI Boost NPU, Intel GPU, or CPU.
- **Positive:** The same OpenAI-compatible client pattern can be reused for text and embedding calls.
- **Positive:** When both model and embedding providers are `openvino`, the backend starts one OVMS process with a generated `config.json` that serves both the text-generation and embedding models from the same endpoint.
- **Positive:** The UI can cache Hugging Face models locally and stores the optional token only in gitignored `.env` files.
- **Positive:** Native Windows OVMS avoids Docker `/dev/accel` passthrough issues and gives OVMS direct access to host Intel acceleration devices.
- **Positive:** The Configuration page favors NPU-friendly OpenVINO INT4 models, explains that OVMS downloads/caches missing Hugging Face models, and starts OVMS as a background job with progress logs.
- **Trade-off:** OVMS must be installed and started separately with `scripts/setup-ovms.ps1` before OpenVINO workloads run.
- **Trade-off:** First NPU startup can take several minutes because OVMS may need to download, prepare, compile, and cache the selected model before inference is ready.
- **Trade-off:** The UI can start OVMS only when `ovms.exe` is on the UI backend process `PATH` or `OPENVINO_OVMS_PATH` points to the extracted executable.
- **Trade-off:** The Compose stack now remains focused on data and observability services; OVMS lifecycle is managed as a host process from the Configuration page or PowerShell.
- **Trade-off:** Switching to OpenVINO embeddings changes vector dimension to 1024, requiring schema alignment and data re-ingestion.
- **Trade-off:** If only one provider is `openvino`, OVMS remains in single-model mode for that task. If both providers are `openvino`, an already-running single-model OVMS process is restarted so it can load the multi-model config.

## Implementation files

- `agent-brain/src/agent_brain/config.py` â€” OpenVINO and Hugging Face token settings.
- `agent-brain/src/agent_brain/orchestration/model_adapter.py` â€” `OpenVINOModelAdapter`.
- `agent-brain/src/agent_brain/retrieval/vector.py` â€” OpenVINO embedding generation.
- `database-layer/src/embedding.ts` â€” OpenVINO ingestion embeddings.
- `ui/backend/src/ui_api/routers/provider.py` â€” provider switcher, model catalogs, settings, status, and download endpoints.
- `ui/frontend/src/app/config/page.tsx` â€” OpenVINO UI controls and helper text.
- `scripts/setup-ovms.ps1` â€” native Windows OVMS start/stop/status helper.
- `docker-compose.yml` â€” data, graph, UI, and observability services only; OVMS is no longer a Compose service.


