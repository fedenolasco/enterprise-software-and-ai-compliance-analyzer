"""Tests for the multi-provider model adapter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agent_brain.orchestration.model_adapter import (
    MicrosoftFoundryLocalAdapter,
    ModelProvider,
    ModelRequest,
    OpenAIModelAdapter,
    PlaceholderLocalModelAdapter,
    build_model_adapter,
)


def test_placeholder_model_adapter_returns_deterministic_usage() -> None:
    adapter = PlaceholderLocalModelAdapter()

    response = adapter.generate(
        ModelRequest(
            prompt="Draft a governed recommendation.",
            trace_id="trace-model-test",
            safety_flags=("HITL_REQUIRED",),
        )
    )

    assert response.provider == ModelProvider.PLACEHOLDER
    assert response.trace_id == "trace-model-test"
    assert response.prompt_tokens == 4
    assert response.completion_tokens > 0
    assert response.total_tokens == response.prompt_tokens + response.completion_tokens
    assert response.simulated_cost_usd == 0.0
    assert "HITL_REQUIRED" in response.text


def test_build_model_adapter_creates_placeholder_by_default() -> None:
    adapter = build_model_adapter()

    assert isinstance(adapter, PlaceholderLocalModelAdapter)


def test_build_model_adapter_creates_foundry_adapter() -> None:
    adapter = build_model_adapter(
        "microsoft-foundry-local",
        foundry_endpoint="http://localhost:5272",
        model_name="phi-local",
    )

    assert isinstance(adapter, MicrosoftFoundryLocalAdapter)
    assert adapter.endpoint == "http://localhost:5272"
    assert adapter.model_name == "phi-local"


def test_build_model_adapter_requires_foundry_endpoint() -> None:
    with pytest.raises(ValueError, match="foundry_endpoint is required"):
        build_model_adapter("microsoft-foundry-local")


def test_build_model_adapter_creates_openai_adapter() -> None:
    adapter = build_model_adapter(
        "openai",
        openai_api_key="sk-test-key",
        model_name="gpt-4o-mini",
    )

    assert isinstance(adapter, OpenAIModelAdapter)
    assert adapter.api_key == "sk-test-key"
    assert adapter.model_name == "gpt-4o-mini"
    assert adapter.use_responses_api is True


def test_build_model_adapter_requires_openai_api_key() -> None:
    with pytest.raises(ValueError, match="openai_api_key is required"):
        build_model_adapter("openai")


def test_build_model_adapter_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported model provider"):
        build_model_adapter("unknown-provider")


def test_openai_model_provider_enum_value() -> None:
    assert ModelProvider.OPENAI.value == "openai"


def test_foundry_local_adapter_generate_calls_chat_completions() -> None:
    adapter = MicrosoftFoundryLocalAdapter(
        endpoint="http://localhost:5272",
        model_name="phi-3.5-mini",
    )

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "Test recommendation from Foundry Local."
    mock_completion.usage = MagicMock(
        prompt_tokens=10,
        completion_tokens=8,
        total_tokens=18,
    )

    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_class.return_value = mock_client

        response = adapter.generate(
            ModelRequest(prompt="Draft a recommendation.", trace_id="trace-fl-1")
        )

    assert response.text == "Test recommendation from Foundry Local."
    assert response.provider == ModelProvider.MICROSOFT_FOUNDRY_LOCAL
    assert response.model_name == "phi-3.5-mini"
    assert response.prompt_tokens == 10
    assert response.completion_tokens == 8
    assert response.total_tokens == 18
    assert response.simulated_cost_usd == 0.0
    assert response.trace_id == "trace-fl-1"
    assert response.metadata["mode"] == "foundry-local"

    mock_openai_class.assert_called_once_with(
        base_url="http://localhost:5272/v1",
        api_key="local",
    )
    mock_client.chat.completions.create.assert_called_once()


def test_openai_adapter_generate_uses_responses_api_by_default() -> None:
    adapter = OpenAIModelAdapter(
        api_key="sk-test-key",
        model_name="gpt-4o-mini",
    )

    mock_response = MagicMock()
    mock_response.output_text = "Test recommendation from OpenAI Responses API."
    mock_response.usage = MagicMock(
        input_tokens=15,
        output_tokens=12,
        total_tokens=27,
    )

    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_client.responses.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        response = adapter.generate(
            ModelRequest(prompt="Draft a recommendation.", trace_id="trace-oai-1")
        )

    assert response.text == "Test recommendation from OpenAI Responses API."
    assert response.provider == ModelProvider.OPENAI
    assert response.model_name == "gpt-4o-mini"
    assert response.prompt_tokens == 15
    assert response.completion_tokens == 12
    assert response.total_tokens == 27
    assert response.simulated_cost_usd > 0.0
    assert response.trace_id == "trace-oai-1"
    assert response.metadata["mode"] == "openai-responses-api"

    mock_openai_class.assert_called_once_with(
        base_url="https://api.openai.com/v1",
        api_key="sk-test-key",
    )
    mock_client.responses.create.assert_called_once()
    mock_client.chat.completions.create.assert_not_called()


def test_openai_adapter_falls_back_to_chat_completions_when_responses_unavailable() -> None:
    adapter = OpenAIModelAdapter(
        api_key="sk-test-key",
        model_name="gpt-4o-mini",
    )

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "Fallback chat completions response."
    mock_completion.usage = MagicMock(
        prompt_tokens=20,
        completion_tokens=10,
        total_tokens=30,
    )

    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_client.responses.create.side_effect = AttributeError("not supported")
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_class.return_value = mock_client

        response = adapter.generate(ModelRequest(prompt="test"))

    assert response.text == "Fallback chat completions response."
    assert response.prompt_tokens == 20
    assert response.completion_tokens == 10
    assert response.total_tokens == 30
    assert response.metadata["mode"] == "openai-chat-completions-api"


def test_openai_adapter_uses_chat_completions_when_responses_disabled() -> None:
    adapter = OpenAIModelAdapter(
        api_key="sk-test-key",
        model_name="gpt-4o-mini",
        use_responses_api=False,
    )

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "Chat completions response."
    mock_completion.usage = MagicMock(
        prompt_tokens=5,
        completion_tokens=5,
        total_tokens=10,
    )

    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_class.return_value = mock_client

        response = adapter.generate(ModelRequest(prompt="test"))

    assert response.text == "Chat completions response."
    assert response.metadata["mode"] == "openai-chat-completions-api"
    mock_client.responses.create.assert_not_called()
    mock_client.chat.completions.create.assert_called_once()


def test_openai_adapter_calculates_cost_correctly_via_responses_api() -> None:
    adapter = OpenAIModelAdapter(
        api_key="sk-test-key",
        model_name="gpt-4o-mini",
        cost_per_1k_input_tokens_usd=0.00015,
        cost_per_1k_output_tokens_usd=0.0006,
    )

    mock_response = MagicMock()
    mock_response.output_text = "Response"
    mock_response.usage = MagicMock(
        input_tokens=1000,
        output_tokens=500,
        total_tokens=1500,
    )

    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_client.responses.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        response = adapter.generate(ModelRequest(prompt="test"))

    expected_cost = round(1000 / 1000 * 0.00015 + 500 / 1000 * 0.0006, 6)
    assert response.simulated_cost_usd == expected_cost


def test_openai_adapter_calculates_cost_correctly_via_chat_completions() -> None:
    adapter = OpenAIModelAdapter(
        api_key="sk-test-key",
        model_name="gpt-4o-mini",
        cost_per_1k_input_tokens_usd=0.00015,
        cost_per_1k_output_tokens_usd=0.0006,
        use_responses_api=False,
    )

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "Response"
    mock_completion.usage = MagicMock(
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
    )

    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_class.return_value = mock_client

        response = adapter.generate(ModelRequest(prompt="test"))

    expected_cost = round(1000 / 1000 * 0.00015 + 500 / 1000 * 0.0006, 6)
    assert response.simulated_cost_usd == expected_cost
