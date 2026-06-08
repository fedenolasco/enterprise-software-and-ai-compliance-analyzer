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
    embedding_dimension: int = 8
    vector_top_k: int = 5
    graph_result_limit: int = 25


def get_settings() -> AgentBrainSettings:
    """Return settings using environment variables and local `.env` values."""

    load_dotenv()
    return AgentBrainSettings(
        database_url=getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        neo4j_uri=getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_username=getenv("NEO4J_USERNAME", "neo4j"),
        neo4j_password=getenv("NEO4J_PASSWORD", "compliance_password"),
        embedding_dimension=_positive_int_from_env("EMBEDDING_DIMENSION", 8),
        vector_top_k=_positive_int_from_env("VECTOR_TOP_K", 5),
        graph_result_limit=_positive_int_from_env("GRAPH_RESULT_LIMIT", 25),
    )
