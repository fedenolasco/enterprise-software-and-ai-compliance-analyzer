import pytest

from agent_brain.orchestration.model_adapter import (
    MicrosoftFoundryLocalAdapter,
    ModelProvider,
    ModelRequest,
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


def test_build_model_adapter_creates_foundry_boundary() -> None:
    adapter = build_model_adapter(
        "microsoft-foundry-local",
        foundry_endpoint="http://localhost:5272",
        model_name="phi-local",
    )

    assert isinstance(adapter, MicrosoftFoundryLocalAdapter)
    assert adapter.endpoint == "http://localhost:5272"
    assert adapter.model_name == "phi-local"


def test_foundry_boundary_fails_closed_until_client_is_implemented() -> None:
    adapter = MicrosoftFoundryLocalAdapter(
        endpoint="http://localhost:5272",
        model_name="phi-local",
    )

    with pytest.raises(RuntimeError, match="concrete local client is not implemented"):
        adapter.generate(ModelRequest(prompt="hello"))


def test_build_model_adapter_requires_foundry_endpoint() -> None:
    with pytest.raises(ValueError, match="foundry_endpoint is required"):
        build_model_adapter("microsoft-foundry-local")
