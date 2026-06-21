# ADR 0003: Microsoft Foundry Local Model Provider

## Status

Accepted for the next concrete model-runtime implementation

## Context

The repository is designed as a local-first compliance analyzer. The current model boundary in [`agent-brain/src/agent_brain/orchestration/model_adapter.py`](../../agent-brain/src/agent_brain/orchestration/model_adapter.py) supports deterministic offline validation through `PlaceholderLocalModelAdapter` and includes a `MicrosoftFoundryLocalAdapter` boundary that intentionally fails closed until a concrete local client is implemented.

The project owner has access to hosted providers such as OpenAI and OpenRouter, but the product direction prioritizes local execution for early compliance demonstrations. Using hosted providers too early would weaken the local-first story, introduce API-key handling, and make demo behavior depend on external services.

Microsoft Foundry Local is the preferred first concrete model runtime because it aligns with:

- Local-first prototype execution.
- Governed enterprise AI architecture.
- Future Microsoft ecosystem integration.
- Provider-neutral model responses, HITL controls, observability payloads, and audit persistence.

## Decision

Use Microsoft Foundry Local as the first target real model provider for agent reasoning and recommendation drafting.

Keep the deterministic placeholder model as the default provider until the concrete Microsoft Foundry Local client is implemented and validated.

Defer OpenAI and OpenRouter integrations. They may be added later as optional hosted adapters only if the documentation clearly states that those providers are not local-only and require external API calls.

The supported model-provider direction is:

| Provider | Role | Current decision |
|---|---|---|
| `placeholder` | Deterministic offline validation | Keep as default for repeatable local demos. |
| `microsoft-foundry-local` | First concrete real model runtime | Implement next when the local runtime and API contract are available. |
| `openai` | Optional hosted provider | Defer. Do not wire for the current local-first implementation path. |
| `openrouter` | Optional hosted provider aggregator | Defer. Do not wire for the current local-first implementation path. |

## Implementation implications

The Microsoft Foundry Local implementation should:

1. Keep using the existing `ModelAdapter` protocol in [`agent-brain/src/agent_brain/orchestration/model_adapter.py`](../../agent-brain/src/agent_brain/orchestration/model_adapter.py).
2. Keep returning provider-neutral `ModelResponse` objects so HITL, Phoenix-compatible trace payloads, Langfuse-compatible usage payloads, and local audit records do not depend on a specific model provider.
3. Use environment configuration from [`agent-brain/.env.example`](../../agent-brain/.env.example), especially `MODEL_PROVIDER`, `FOUNDRY_LOCAL_ENDPOINT`, and `LOCAL_MODEL_NAME`.
4. Fail closed when the Foundry Local endpoint is missing, unreachable, or returns an unsupported response shape.
5. Preserve the mandatory HITL finalization gate before cancellation or renewal recommendations are treated as final.
6. Add tests that mock Microsoft Foundry Local responses and validate response text, provider metadata, token accounting when available, simulated cost fields, trace IDs, safety flags, and failure behavior.
7. Update [`docs/07-demo-runbook.md`](../07-demo-runbook.md) and [`docs/06-setup-runbook.md`](../06-setup-runbook.md) after the concrete client is validated.

## Configuration policy

The default model configuration remains local and deterministic:

```text
MODEL_PROVIDER=placeholder
LOCAL_MODEL_NAME=deterministic-placeholder-local-model
FOUNDRY_LOCAL_ENDPOINT=http://localhost:5272
```

When Microsoft Foundry Local is implemented and installed locally, demo operators may switch to:

```text
MODEL_PROVIDER=microsoft-foundry-local
LOCAL_MODEL_NAME=<local-foundry-model-name>
FOUNDRY_LOCAL_ENDPOINT=<local-foundry-endpoint>
```

Hosted provider secrets such as OpenAI or OpenRouter API keys should not be added for the current implementation path. If hosted providers are introduced later, API keys must remain in uncommitted environment files only.

## Consequences

- The project preserves its local-first compliance posture.
- Demo behavior remains deterministic until a local model runtime is explicitly installed and validated.
- The current placeholder adapter remains useful for offline tests, CI-style checks, and demos where Foundry Local is unavailable.
- OpenAI and OpenRouter are intentionally deferred, reducing external dependency, data egress, and API-key-management concerns.
- The Microsoft Foundry Local adapter must be treated as a governed integration point, not a hidden dependency.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Foundry Local runtime is unavailable on a demo machine. | Real model demo cannot run. | Keep `placeholder` as the default and document Foundry Local as optional until validated. |
| Foundry Local response shape differs from assumptions. | Adapter may produce incorrect usage or audit metadata. | Fail closed and add mocked contract tests before enabling live demos. |
| Hosted providers are added informally later. | Local-first compliance story becomes ambiguous. | Require a new ADR or update to this ADR before adding OpenAI/OpenRouter adapters. |
| Real model outputs vary across runs. | Curated demo assertions could become non-deterministic. | Keep retrieval assertions deterministic and separate model-output quality checks from retrieval plumbing checks. |

## Future work

Before Microsoft Foundry Local becomes the active provider for demos:

1. Confirm the local runtime installation process and supported endpoint contract.
2. Select the local model name and document hardware expectations.
3. Implement the concrete client inside `MicrosoftFoundryLocalAdapter`.
4. Add mocked and, where practical, local integration tests.
5. Update `.env.example` documentation if additional Foundry Local settings are required.
6. Update runbooks with exact startup, validation, and fallback steps.
7. Add a changelog entry when the provider becomes live.
