# ADR 0008: OpenVINO Model Server Provider for Local Inference and Embeddings

## Status

Accepted — 2026-06-23

## Context

Microsoft Foundry Local provides a local model runtime, but the current Foundry public model catalog does not clearly verify `all-MiniLM-L6-v2` as a supported local embedding model. The product needs a local provider that can support both text inference and semantic embeddings, preferably with Intel AI Boost NPU acceleration.

OpenVINO Model Server (OVMS) exposes OpenAI-compatible APIs for text generation and embeddings, and OpenVINO 2026 documentation confirms NPU deployment patterns plus embedding support. Hugging Face hosts public OpenVINO-optimized models, including Qwen text-generation models and Qwen3 embedding models.

## Decision

Add `openvino` as a fourth model and embedding provider alongside `placeholder`, `microsoft-foundry-local`, and `openai`.

The OpenVINO integration uses Architecture A: **OVMS as an external local server**.

```text
Application code -> OpenAI-compatible client -> OpenVINO Model Server -> Intel NPU/GPU/CPU
```

This keeps code changes close to the existing Foundry Local integration because both expose OpenAI-compatible API surfaces.

## Provider configuration

The OpenVINO provider uses these environment variables:

| Variable | Purpose | Default |
|---|---|---|
| `MODEL_PROVIDER` | Selects LLM provider | `openvino` when active |
| `EMBEDDING_PROVIDER` | Selects embedding provider | `openvino` when active |
| `OPENVINO_ENDPOINT` | OVMS base endpoint | `http://localhost:8100` |
| `OPENVINO_MODEL` | Text-generation model ID | `OpenVINO/Qwen3-8B-int4-cw-ov` |
| `OPENVINO_EMBEDDING_MODEL` | Embedding model ID | `OpenVINO/Qwen3-Embedding-0.6B` |
| `OPENVINO_DEVICE` | Preferred target device | `NPU` |
| `HF_TOKEN` | Optional Hugging Face token | unset |

`HF_TOKEN` is optional for public OpenVINO models. It is only required for gated/private models or to avoid anonymous download limits.

## Consequences

- **Positive:** The project gains a local embedding provider with a verified OpenVINO embedding model path.
- **Positive:** OpenVINO can target Intel AI Boost NPU, Intel GPU, or CPU.
- **Positive:** The same OpenAI-compatible client pattern can be reused for text and embedding calls.
- **Positive:** The UI can cache Hugging Face models locally and stores the optional token only in gitignored `.env` files.
- **Trade-off:** OVMS must be started separately and configured with the required models.
- **Trade-off:** Docker NPU passthrough is host-dependent; native Windows OVMS may be preferable where Docker cannot access `/dev/accel`.
- **Trade-off:** Switching to OpenVINO embeddings changes vector dimension to 1024, requiring schema alignment and data re-ingestion.

## Implementation files

- `agent-brain/src/agent_brain/config.py` — OpenVINO and Hugging Face token settings.
- `agent-brain/src/agent_brain/orchestration/model_adapter.py` — `OpenVINOModelAdapter`.
- `agent-brain/src/agent_brain/retrieval/vector.py` — OpenVINO embedding generation.
- `database-layer/src/embedding.ts` — OpenVINO ingestion embeddings.
- `ui/backend/src/ui_api/routers/provider.py` — provider switcher, model catalogs, settings, status, and download endpoints.
- `ui/frontend/src/app/config/page.tsx` — OpenVINO UI controls and helper text.
- `docker-compose.yml` — optional OVMS profile.

