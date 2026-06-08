from agent_brain.config import AgentBrainSettings, get_settings


def test_default_settings_match_local_service_defaults() -> None:
    settings = AgentBrainSettings()

    assert settings.database_url.startswith("postgresql://compliance_user:")
    assert settings.neo4j_uri == "bolt://localhost:7687"
    assert settings.neo4j_username == "neo4j"
    assert settings.mock_pricing_api_url == "http://127.0.0.1:8000"
    assert settings.embedding_dimension == 8
    assert settings.vector_top_k == 5
    assert settings.graph_result_limit == 25


def test_get_settings_reads_environment_values(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("NEO4J_URI", "bolt://example.test:7687")
    monkeypatch.setenv("VECTOR_TOP_K", "7")

    settings = get_settings()

    assert settings.neo4j_uri == "bolt://example.test:7687"
    assert settings.vector_top_k == 7
