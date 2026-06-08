from agent_brain.config import AgentBrainSettings
from agent_brain.orchestration.state import create_initial_state
from agent_brain.tools.pricing import (
    PricingToolError,
    add_pricing_to_state,
    pricing_tool_result_from_response,
)


def test_pricing_tool_result_from_response_normalizes_api_payload() -> None:
    result = pricing_tool_result_from_response(
        {
            "pricing": {
                "software_code": "SW-NOTION-AI",
                "software_name": "Notion AI",
            },
            "requested_seats": 80,
            "applied_discount_percent": 3.0,
            "estimated_annual_total_usd": 16761.6,
            "source": "mock-pricing-api",
        }
    )

    assert result.software_code == "SW-NOTION-AI"
    assert result.to_live_pricing_context().estimated_annual_total_usd == 16761.6


def test_pricing_tool_result_from_response_rejects_invalid_payload() -> None:
    try:
        pricing_tool_result_from_response({"pricing": "invalid"})
    except PricingToolError as exc:
        assert "invalid response shape" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected PricingToolError")


def test_add_pricing_to_state_appends_live_pricing(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from agent_brain.tools import pricing

    def fake_post_json(
        url: str,
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> dict[str, object]:
        assert url == "http://pricing.test/pricing:lookup"
        assert payload == {"software_code": "SW-OPENAI-CHATGPT-ENT", "requested_seats": 120}
        assert timeout_seconds == 5.0
        return {
            "pricing": {
                "software_code": "SW-OPENAI-CHATGPT-ENT",
                "software_name": "ChatGPT Enterprise",
            },
            "requested_seats": 120,
            "applied_discount_percent": 5.0,
            "estimated_annual_total_usd": 41040.0,
            "source": "mock-pricing-api",
        }

    monkeypatch.setattr(pricing, "_post_json", fake_post_json)
    state = create_initial_state("Should we renew OpenAI?")
    settings = AgentBrainSettings(mock_pricing_api_url="http://pricing.test")

    updated = add_pricing_to_state(state, "SW-OPENAI-CHATGPT-ENT", 120, settings)

    assert len(updated.live_pricing) == 1
    assert updated.live_pricing[0].software_name == "ChatGPT Enterprise"
    assert updated.live_pricing[0].estimated_annual_total_usd == 41040.0
