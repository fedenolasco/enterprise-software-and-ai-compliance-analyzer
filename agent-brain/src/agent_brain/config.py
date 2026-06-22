"""Configuration for the local agent-brain workstream."""

from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

DEFAULT_DATABASE_URL = (
    "postgresql://compliance_user:compliance_password@localhost:5432/"
    "compliance_analyzer?schema=public"
)


def _positive_int_from_env(name: str, default: int) -> int:
    """Read a positive integer from the environment."""

    raw_value = getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default

    try:
        parsed_value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive integer.") from exc

    if parsed_value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return parsed_value


@dataclass(frozen=True)
class AgentBrainSettings:
    """Environment-backed settings for local retrieval services."""

    database_url: str = DEFAULT_DATABASE_URL
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "compliance_password"
    mock_pricing_api_url: str = "http://127.0.0.1:8000"
    embedding_dimension: int = 8
    embedding_model: str = "deterministic-placeholder"
    embedding_provider: str = "placeholder"
    vector_top_k: int = 5
    graph_result_limit: int = 25
    model_provider: str = "placeholder"
    foundry_local_endpoint: str | None = None
    local_model_name: str = "deterministic-placeholder-local-model"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    phoenix_enabled: bool = False
    phoenix_endpoint: str = "http://localhost:6006"
    phoenix_grpc_endpoint: str = "http://localhost:4317"
    langfuse_enabled: bool = False
    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None


def get_settings() -> AgentBrainSettings:
    """Return settings using environment variables and local `.env` values."""

    load_dotenv()
    return AgentBrainSettings(
        database_url=getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        neo4j_uri=getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_username=getenv("NEO4J_USERNAME", "neo4j"),
        neo4j_password=getenv("NEO4J_PASSWORD", "compliance_password"),
        mock_pricing_api_url=getenv("MOCK_PRICING_API_URL", "http://127.0.0.1:8000"),
        embedding_dimension=_positive_int_from_env("EMBEDDING_DIMENSION", 8),
        embedding_model=getenv("EMBEDDING_MODEL", "deterministic-placeholder"),
        embedding_provider=getenv("EMBEDDING_PROVIDER", "placeholder"),
        vector_top_k=_positive_int_from_env("VECTOR_TOP_K", 5),
        graph_result_limit=_positive_int_from_env("GRAPH_RESULT_LIMIT", 25),
        model_provider=getenv("MODEL_PROVIDER", "placeholder"),
        foundry_local_endpoint=getenv("FOUNDRY_LOCAL_ENDPOINT"),
        local_model_name=getenv("LOCAL_MODEL_NAME", "deterministic-placeholder-local-model"),
        openai_api_key=getenv("OPENAI_API_KEY"),
        openai_model=getenv("OPENAI_MODEL", "gpt-4o-mini"),
        openai_base_url=getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        phoenix_enabled=_bool_from_env("PHOENIX_ENABLED", False),
        phoenix_endpoint=getenv("PHOENIX_ENDPOINT", "http://localhost:6006"),
        phoenix_grpc_endpoint=getenv("PHOENIX_GRPC_ENDPOINT", "http://localhost:4317"),
        langfuse_enabled=_bool_from_env("LANGFUSE_ENABLED", False),
        langfuse_host=getenv("LANGFUSE_HOST", "http://localhost:3000"),
        langfuse_public_key=getenv("LANGFUSE_PUBLIC_KEY"),
        langfuse_secret_key=getenv("LANGFUSE_SECRET_KEY"),
    )


def _bool_from_env(name: str, default: bool) -> bool:
    """Read a boolean from the environment."""

    raw_value = getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value.")
