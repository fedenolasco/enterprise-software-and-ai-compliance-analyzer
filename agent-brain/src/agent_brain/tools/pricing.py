"""Tool wrapper for the local mock pricing API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, SupportsInt, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from agent_brain.config import AgentBrainSettings, get_settings
from agent_brain.orchestration.state import AgentBrainState, LivePricingContext


class PricingToolError(RuntimeError):
    """Raised when the mock pricing API cannot return a usable response."""


@dataclass(frozen=True)
class PricingToolResult:
    """Normalized pricing lookup result returned by the local pricing tool."""

    software_code: str
    software_name: str
    requested_seats: int | None
    estimated_annual_total_usd: float
    applied_discount_percent: float
    source: str

    def to_live_pricing_context(self) -> LivePricingContext:
        """Convert the tool result into agent state pricing context."""

        return LivePricingContext(
            software_code=self.software_code,
            software_name=self.software_name,
            requested_seats=self.requested_seats,
            estimated_annual_total_usd=self.estimated_annual_total_usd,
            applied_discount_percent=self.applied_discount_percent,
            source=self.source,
        )


def lookup_pricing(
    software_code: str,
    requested_seats: int | None = None,
    settings: AgentBrainSettings | None = None,
    timeout_seconds: float = 5.0,
) -> PricingToolResult:
    """Call the local mock pricing API and return normalized pricing context."""

    if software_code.strip() == "":
        raise ValueError("software_code must not be empty.")

    active_settings = settings or get_settings()
    payload: dict[str, object] = {"software_code": software_code}
    if requested_seats is not None:
        if requested_seats < 0:
            raise ValueError("requested_seats must be non-negative.")
        payload["requested_seats"] = requested_seats

    response = _post_json(
        f"{active_settings.mock_pricing_api_url.rstrip('/')}/pricing:lookup",
        payload,
        timeout_seconds,
    )
    return pricing_tool_result_from_response(response)


def add_pricing_to_state(
    state: AgentBrainState,
    software_code: str,
    requested_seats: int | None = None,
    settings: AgentBrainSettings | None = None,
) -> AgentBrainState:
    """Return a copy of state with a pricing lookup appended to live pricing context."""

    result = lookup_pricing(software_code, requested_seats, settings)
    return AgentBrainState(
        user_query=state.user_query,
        retrieved_context=list(state.retrieved_context),
        compliance_risks=list(state.compliance_risks),
        live_pricing=list(state.live_pricing) + [result.to_live_pricing_context()],
        recommendation_draft=state.recommendation_draft,
        human_approval_status=state.human_approval_status,
        final_output=state.final_output,
        trace_id=state.trace_id,
        safety_flags=list(state.safety_flags),
    )


def pricing_tool_result_from_response(response: dict[str, Any]) -> PricingToolResult:
    """Normalize the mock pricing API response into a typed tool result."""

    try:
        pricing = response["pricing"]
        if not isinstance(pricing, dict):
            raise TypeError("pricing must be an object")
        return PricingToolResult(
            software_code=str(pricing["software_code"]),
            software_name=str(pricing["software_name"]),
            requested_seats=_optional_int(response.get("requested_seats")),
            estimated_annual_total_usd=float(response["estimated_annual_total_usd"]),
            applied_discount_percent=float(response["applied_discount_percent"]),
            source=str(response.get("source", "mock-pricing-api")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PricingToolError("Mock pricing API returned an invalid response shape.") from exc


def _post_json(url: str, payload: dict[str, object], timeout_seconds: float) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw_body = response.read().decode("utf-8")
    except HTTPError as exc:
        raise PricingToolError(f"Mock pricing API returned HTTP {exc.code}.") from exc
    except URLError as exc:
        raise PricingToolError("Mock pricing API is unreachable.") from exc

    parsed = json.loads(raw_body)
    if not isinstance(parsed, dict):
        raise PricingToolError("Mock pricing API returned a non-object response.")
    return parsed


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, str | bytes | bytearray):
        return int(value)
    return int(cast(SupportsInt, value))
