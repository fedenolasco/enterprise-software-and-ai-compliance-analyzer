# ADR 0005: Multi-Provider Model and Embedding Strategy

## Status

Accepted — supersedes [ADR 0002](0002-placeholder-embedding-strategy.md) and updates [ADR 0003](0003-microsoft-foundry-local-model-provider.md).

## Context

ADR 0002 established deterministic placeholder embeddings for Phase 1 scaffolding. ADR 0003 selected Microsoft Foundry Local as the first concrete model runtime and deferred OpenAI and OpenRouter.

The project now needs to support multiple model and embedding providers so that:

- Demo operators can choose between offline, local real-model, and cloud API modes.
- The local-first governance story is preserved for offline demonstrations.
- Cloud API access is available when higher model quality is needed.
- The existing `ModelAdapter` protocol and `ModelResponse` dataclass remain provider-neutral.

## Decision

Support three configurable providers for both LLM text generation and embedding generation:

| Provider | `MODEL_PROVIDER` / `EMBEDDING_PROVIDER` | LLM | Embeddings | API key | Offline |
|---|---|---|---|---|---|
| Placeholder | `placeholder` | Deterministic | 8-dim placeholder | None | Yes |
| Microsoft Foundry Local | `microsoft-foundry-local` | Phi-3.5-mini / Qwen2.5 | all-MiniLM-L6-v2 (384-dim) | None | Yes |
| OpenAI | `openai` | gpt-4o-mini | text-embedding-3-small (1536-dim) | Required | No |

The placeholder provider remains the default for offline validation, CI, and deterministic demos. Foundry Local and OpenAI are opt-in via environment configuration.

### Implementation

- The `ModelProvider` enum in [`agent-brain/src/agent_brain/orchestration/model_adapter.py`](../../agent-brain/src/agent_brain/orchestration/model_adapter.py) includes `PLACEHOLDER`, `MICROSOFT_FOUNDRY_LOCAL`, and `OPENAI`.
- `build_model_adapter()` creates the correct adapter from environment-style configuration.
- Embedding functions in [`database-layer/src/embedding.ts`](../../database-layer/src/embedding.ts) and [`agent-brain/src/agent_brain/retrieval/vector.py`](../../agent-brain/src/agent_brain/retrieval/vector.py) dispatch to the configured provider with deterministic placeholder fallback.
- Provider setup scripts at [`scripts/setup-provider.ps1`](../../scripts/setup-provider.ps1) and [`scripts/setup-provider.sh`](../../scripts/setup-provider.sh) securely configure API keys and switch providers.

### Foundry Local API usage

Foundry Local exposes an OpenAI-compatible API at `http://localhost:5272/v1` with `/v1/chat/completions` and `/v1/embeddings` endpoints. The `openai` Python and npm packages are used as clients with `base_url` pointed at the local endpoint. No real API key is needed — Foundry Local accepts any value (conventionally `"local"`).

### OpenAI API usage

The OpenAI adapter uses the Responses API (`client.responses.create()`) as the primary method, as recommended by OpenAI. The Chat Completions API (`client.chat.completions.create()`) is supported as a fallback when the Responses API is not available for the selected model. See [ADR 0006](0006-openai-responses-api-strategy.md) for details.

## Consequences

- The project supports offline, local real-model, and cloud API modes from a single codebase.
- Switching embedding providers changes the vector dimension, requiring a schema migration, reset, and re-ingestion.
- The placeholder provider remains useful for CI, offline tests, and deterministic demos.
- Foundry Local requires native installation and model downloads — it is not a Docker service.
- OpenAI requires an API key and network access — it is not offline-capable.
- All three providers map to the same provider-neutral `ModelResponse` dataclass, so HITL, observability, and audit logic do not depend on the active provider.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Embedding dimension mismatch after provider switch | Vector search returns errors | Setup scripts warn about dimension change; reset orchestration re-ingests data |
| OpenAI API key exposure | Security incident | Key is written only to gitignored `.env` files; setup script uses masked input |
| Foundry Local unavailable | Cannot use local real-model mode | Placeholder provider remains the default; OpenAI is an alternative |
| OpenAI API costs | Unexpected charges | Cost is tracked in `ModelResponse.simulated_cost_usd`; gpt-4o-mini is low-cost |
