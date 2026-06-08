from fastapi.testclient import TestClient

from mock_pricing_api.app import create_app

client = TestClient(create_app())


def test_health_returns_fixture_count() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "pricing_records": 3}


def test_list_pricing_returns_synthetic_records() -> None:
    response = client.get("/pricing")

    payload = response.json()

    assert response.status_code == 200
    assert len(payload) == 3
    assert {record["software_code"] for record in payload} == {
        "SW-OPENAI-CHATGPT-ENT",
        "SW-MS-COPILOT-M365",
        "SW-NOTION-AI",
    }


def test_get_pricing_by_software_code() -> None:
    response = client.get("/pricing/SW-NOTION-AI")

    assert response.status_code == 200
    assert response.json()["vendor_name"] == "Notion AI"


def test_lookup_applies_volume_discount() -> None:
    response = client.post(
        "/pricing:lookup",
        json={"software_code": "SW-OPENAI-CHATGPT-ENT", "requested_seats": 120},
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["applied_discount_percent"] == 5.0
    assert payload["estimated_annual_total_usd"] == 41040.0


def test_unknown_software_returns_404() -> None:
    response = client.get("/pricing/UNKNOWN")

    assert response.status_code == 404
