"""Local and API-based model adapter boundary for governed recommendation drafting."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class ModelProvider(StrEnum):
    """Supported model provider modes."""

    PLACEHOLDER = "placeholder"
    MICROSOFT_FOUNDRY_LOCAL = "microsoft-foundry-local"
    OPENAI = "openai"


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
    """Protocol implemented by placeholder, Foundry Local, and OpenAI adapters."""

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
    """Deterministic local adapter used when no real model provider is configured."""

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
            "Use this deterministic output until Microsoft Foundry Local or OpenAI is enabled."
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
    """Concrete adapter for Microsoft Foundry Local using the OpenAI-compatible API.

    Foundry Local exposes ``/v1/chat/completions`` on a local endpoint.  The
    ``openai`` Python package is used as the client with ``base_url`` pointed
    at the local server.  No real API key is needed — Foundry Local accepts
    any value (conventionally ``"local"``).

    Foundry Local uses the Chat Completions API format, not the newer
    Responses API, so this adapter calls ``client.chat.completions.create()``.
    """

    endpoint: str
    model_name: str
    cost_per_1k_tokens_usd: float = 0.0
    provider: ModelProvider = ModelProvider.MICROSOFT_FOUNDRY_LOCAL

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Call the Foundry Local chat completions endpoint and return a typed response."""

        from openai import OpenAI  # noqa: PLC0415 — deferred import for optional dependency

        client = OpenAI(
            base_url=f"{self.endpoint.rstrip('/')}/v1",
            api_key="local",
        )
        completion = client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": request.prompt}],
        )
        response_text = completion.choices[0].message.content or ""
        usage = completion.usage
        prompt_tokens = usage.prompt_tokens if usage else _estimate_tokens(request.prompt)
        completion_tokens = (
            usage.completion_tokens if usage else _estimate_tokens(response_text)
        )
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
            metadata={"mode": "foundry-local", "endpoint": self.endpoint, **request.metadata},
        )


@dataclass(frozen=True)
class OpenAIModelAdapter:
    """Concrete adapter for the hosted OpenAI API.

    Uses the OpenAI Responses API (``client.responses.create()``) as the
    primary method for text generation, as recommended by OpenAI.  The Chat
    Completions API is supported as a fallback when the Responses API is not
    available for the selected model.

    Token usage and cost are extracted from the API response ``usage`` field.
    The Responses API uses ``input_tokens`` and ``output_tokens``; the Chat
    Completions API uses ``prompt_tokens`` and ``completion_tokens``.
    """

    api_key: str
    model_name: str = "gpt-4o-mini"
    base_url: str = "https://api.openai.com/v1"
    cost_per_1k_input_tokens_usd: float = 0.00015
    cost_per_1k_output_tokens_usd: float = 0.0006
    use_responses_api: bool = True
    provider: ModelProvider = ModelProvider.OPENAI

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Call the OpenAI API and return a typed response.

        Uses the Responses API by default.  Falls back to Chat Completions
        when ``use_responses_api`` is ``False`` or when the Responses API
        raises an ``AttributeError`` (indicating the model or endpoint does
        not support it).
        """

        from openai import OpenAI  # noqa: PLC0415 — deferred import for optional dependency

        client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

        if self.use_responses_api:
            try:
                return self._generate_via_responses_api(client, request)
            except AttributeError:
                pass

        return self._generate_via_chat_completions(client, request)

    def _generate_via_responses_api(
        self,
        client: object,
        request: ModelRequest,
    ) -> ModelResponse:
        """Generate using the OpenAI Responses API."""

        response = client.responses.create(  # type: ignore[attr-defined]
            model=self.model_name,
            input=request.prompt,
        )
        response_text = response.output_text
        usage = response.usage
        prompt_tokens = usage.input_tokens if usage else _estimate_tokens(request.prompt)
        completion_tokens = (
            usage.output_tokens if usage else _estimate_tokens(response_text)
        )
        total_tokens = usage.total_tokens if usage else prompt_tokens + completion_tokens
        cost_usd = round(
            prompt_tokens / 1000 * self.cost_per_1k_input_tokens_usd
            + completion_tokens / 1000 * self.cost_per_1k_output_tokens_usd,
            6,
        )
        return ModelResponse(
            text=response_text,
            provider=self.provider,
            model_name=self.model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            simulated_cost_usd=cost_usd,
            trace_id=request.trace_id,
            metadata={"mode": "openai-responses-api", **request.metadata},
        )

    def _generate_via_chat_completions(
        self,
        client: object,
        request: ModelRequest,
    ) -> ModelResponse:
        """Generate using the OpenAI Chat Completions API (fallback)."""

        completion = client.chat.completions.create(  # type: ignore[attr-defined]
            model=self.model_name,
            messages=[{"role": "user", "content": request.prompt}],
        )
        response_text = completion.choices[0].message.content or ""
        usage = completion.usage
        prompt_tokens = usage.prompt_tokens if usage else _estimate_tokens(request.prompt)
        completion_tokens = (
            usage.completion_tokens if usage else _estimate_tokens(response_text)
        )
        total_tokens = usage.total_tokens if usage else prompt_tokens + completion_tokens
        cost_usd = round(
            prompt_tokens / 1000 * self.cost_per_1k_input_tokens_usd
            + completion_tokens / 1000 * self.cost_per_1k_output_tokens_usd,
            6,
        )
        return ModelResponse(
            text=response_text,
            provider=self.provider,
            model_name=self.model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            simulated_cost_usd=cost_usd,
            trace_id=request.trace_id,
            metadata={"mode": "openai-chat-completions-api", **request.metadata},
        )


def build_model_adapter(
    provider: str = ModelProvider.PLACEHOLDER.value,
    *,
    foundry_endpoint: str | None = None,
    model_name: str | None = None,
    openai_api_key: str | None = None,
    openai_base_url: str = "https://api.openai.com/v1",
    use_responses_api: bool = True,
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
    if normalized == ModelProvider.OPENAI.value:
        if openai_api_key is None or openai_api_key.strip() == "":
            raise ValueError("openai_api_key is required for the OpenAI provider.")
        return OpenAIModelAdapter(
            api_key=openai_api_key,
            model_name=model_name or "gpt-4o-mini",
            base_url=openai_base_url,
            use_responses_api=use_responses_api,
        )
    raise ValueError(f"Unsupported model provider: {provider}")


def _estimate_tokens(text: str) -> int:
    """Return a deterministic token estimate suitable for local FinOps logging."""

    return max(1, len(text.split()))
