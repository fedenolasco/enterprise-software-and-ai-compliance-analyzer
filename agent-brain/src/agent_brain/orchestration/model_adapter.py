"""Local model adapter boundary for governed recommendation drafting."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class ModelProvider(StrEnum):
    """Supported local model provider modes."""

    PLACEHOLDER = "placeholder"
    MICROSOFT_FOUNDRY_LOCAL = "microsoft-foundry-local"


@dataclass(frozen=True)
class ModelRequest:
    """Provider-neutral model request payload."""

    prompt: str
    trace_id: str | None = None
    safety_flags: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelResponse:
    """Provider-neutral model response and token accounting."""

    text: str
    provider: ModelProvider
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    simulated_cost_usd: float
    trace_id: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)


class ModelAdapter(Protocol):
    """Protocol implemented by local and future Foundry Local adapters."""

    @property
    def provider(self) -> ModelProvider:
        """Return the provider implemented by this adapter."""
        ...

    @property
    def model_name(self) -> str:
        """Return the configured model name."""
        ...

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response for the supplied request."""
        ...


@dataclass(frozen=True)
class PlaceholderLocalModelAdapter:
    """Deterministic local adapter used when Foundry Local is unavailable."""

    model_name: str = "deterministic-placeholder-local-model"
    cost_per_1k_tokens_usd: float = 0.0
    provider: ModelProvider = ModelProvider.PLACEHOLDER

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Return a deterministic response with approximate token accounting."""

        prompt_tokens = _estimate_tokens(request.prompt)
        safety_suffix = (
            f" Safety flags: {', '.join(request.safety_flags)}."
            if request.safety_flags
            else " Safety flags: none."
        )
        response_text = (
            "Placeholder local model response for governed compliance analysis. "
            "Use this deterministic output until Microsoft Foundry Local is enabled."
            f"{safety_suffix}"
        )
        completion_tokens = _estimate_tokens(response_text)
        total_tokens = prompt_tokens + completion_tokens
        return ModelResponse(
            text=response_text,
            provider=self.provider,
            model_name=self.model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            simulated_cost_usd=round(total_tokens / 1000 * self.cost_per_1k_tokens_usd, 6),
            trace_id=request.trace_id,
            metadata={"mode": "offline-placeholder", **request.metadata},
        )


@dataclass(frozen=True)
class MicrosoftFoundryLocalAdapter:
    """Explicit boundary for future Microsoft Foundry Local integration."""

    endpoint: str
    model_name: str
    cost_per_1k_tokens_usd: float = 0.0
    provider: ModelProvider = ModelProvider.MICROSOFT_FOUNDRY_LOCAL

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Fail closed until a concrete Foundry Local client is wired in."""

        raise RuntimeError(
            "Microsoft Foundry Local adapter boundary is configured, but the concrete "
            "local client is not implemented yet. Use PlaceholderLocalModelAdapter for "
            "offline Phase 4 validation."
        )


def build_model_adapter(
    provider: str = ModelProvider.PLACEHOLDER.value,
    *,
    foundry_endpoint: str | None = None,
    model_name: str | None = None,
) -> ModelAdapter:
    """Create a model adapter from environment-style configuration values."""

    normalized = provider.strip().lower()
    if normalized == ModelProvider.PLACEHOLDER.value:
        return PlaceholderLocalModelAdapter(
            model_name=model_name or "deterministic-placeholder-local-model"
        )
    if normalized == ModelProvider.MICROSOFT_FOUNDRY_LOCAL.value:
        if foundry_endpoint is None or foundry_endpoint.strip() == "":
            raise ValueError("foundry_endpoint is required for Microsoft Foundry Local.")
        return MicrosoftFoundryLocalAdapter(
            endpoint=foundry_endpoint,
            model_name=model_name or "foundry-local-model",
        )
    raise ValueError(f"Unsupported model provider: {provider}")


def _estimate_tokens(text: str) -> int:
    """Return a deterministic token estimate suitable for local FinOps logging."""

    return max(1, len(text.split()))
