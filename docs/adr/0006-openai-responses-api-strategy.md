# ADR 0006: OpenAI Responses API as Primary with Chat Completions Fallback

## Status

Accepted

## Context

The OpenAI Python SDK provides two APIs for text generation:

1. **Responses API** (`client.responses.create()`) — the newer, recommended API. Returns `response.output_text` for the generated text and `response.usage` with `input_tokens`, `output_tokens`, and `total_tokens`.
2. **Chat Completions API** (`client.chat.completions.create()`) — the previous standard API. Returns `completion.choices[0].message.content` for the generated text and `completion.usage` with `prompt_tokens`, `completion_tokens`, and `total_tokens`.

OpenAI's official documentation states: "The primary API for interacting with OpenAI models is the Responses API. The Chat Completions API is the previous standard for generating text and is supported indefinitely."

The project needs to decide which API to use for the `OpenAIModelAdapter` in [`agent-brain/src/agent_brain/orchestration/model_adapter.py`](../../agent-brain/src/agent_brain/orchestration/model_adapter.py).

## Decision

Use the **Responses API as the primary** method for text generation in the `OpenAIModelAdapter`, with **Chat Completions API as a fallback** when the Responses API is not available.

### Implementation

- `OpenAIModelAdapter.generate()` calls `client.responses.create()` first when `use_responses_api=True` (the default).
- If the Responses API raises an `AttributeError` (indicating the model or endpoint does not support it), the adapter falls back to `client.chat.completions.create()`.
- When `use_responses_api=False`, the adapter uses Chat Completions directly without attempting the Responses API.
- Token usage is extracted from the appropriate field depending on which API was used:
  - Responses API: `usage.input_tokens`, `usage.output_tokens`, `usage.total_tokens`
  - Chat Completions API: `usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens`
- The `metadata["mode"]` field in the `ModelResponse` indicates which API was used: `"openai-responses-api"` or `"openai-chat-completions-api"`.

### Foundry Local uses Chat Completions only

The `MicrosoftFoundryLocalAdapter` uses Chat Completions API exclusively, not the Responses API. Foundry Local exposes an OpenAI-compatible API at `/v1/chat/completions` but does not implement the Responses API endpoint. This is consistent with Foundry Local's documentation, which shows Chat Completions as the supported interface.

## Consequences

- The project follows OpenAI's recommendation to use the Responses API as the primary method.
- The fallback ensures compatibility with models or endpoints that do not support the Responses API.
- The `ModelResponse` dataclass remains provider-neutral — callers do not need to know which API was used.
- The `metadata["mode"]` field allows observability and audit logging to distinguish which API path was taken.
- Tests cover both the Responses API path and the Chat Completions fallback path.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Responses API not available for a model | Text generation fails | Automatic fallback to Chat Completions API |
| Token field names differ between APIs | Incorrect token accounting | Adapter maps the correct fields based on which API was used |
| Future OpenAI SDK changes | Adapter breaks | Deferred import of `openai` package; tests mock the client |
