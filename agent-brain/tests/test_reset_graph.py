"""Tests for the Neo4j demo graph reset script."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scripts.reset_graph import (
    COUNT_DEMO_NODES_QUERY,
    COUNT_DEMO_RELATIONSHIPS_QUERY,
    DEMO_LABELS,
    DEMO_RELATIONSHIP_TYPES,
    GraphResetSummary,
    _is_confirmed,
    build_parser,
    reset_graph_with_driver,
)


def test_demo_labels_cover_all_projected_node_types() -> None:
    assert set(DEMO_LABELS) == {
        "Vendor",
        "Software",
        "Subscription",
        "ComplianceDocument",
        "DocumentChunk",
    }


def test_demo_relationship_types_cover_all_projected_relationships() -> None:
    assert set(DEMO_RELATIONSHIP_TYPES) == {
        "SELLS",
        "HAS_SUBSCRIPTION",
        "HAS_POLICY",
        "HAS_CHUNK",
        "EVIDENCES_RISK",
    }


def test_count_demo_nodes_query_uses_parameterized_labels() -> None:
    assert "$labels" in COUNT_DEMO_NODES_QUERY
    assert "labels(node)" in COUNT_DEMO_NODES_QUERY


def test_count_demo_relationships_query_uses_parameterized_types() -> None:
    assert "$relationship_types" in COUNT_DEMO_RELATIONSHIPS_QUERY
    assert "type(relationship)" in COUNT_DEMO_RELATIONSHIPS_QUERY


def test_graph_reset_summary_is_frozen_dataclass() -> None:
    summary = GraphResetSummary(nodes_deleted=5, relationships_deleted=3)
    assert summary.nodes_deleted == 5
    assert summary.relationships_deleted == 3


def test_build_parser_includes_yes_flag() -> None:
    parser = build_parser()
    args = parser.parse_args(["--yes"])
    assert args.yes is True


def test_build_parser_defaults_to_unconfirmed() -> None:
    parser = build_parser()
    args = parser.parse_args([])
    assert args.yes is False


def test_is_confirmed_returns_true_when_argument_passed() -> None:
    assert _is_confirmed(True) is True


def test_is_confirmed_returns_false_without_argument_or_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RESET_GRAPH", raising=False)
    assert _is_confirmed(False) is False


@pytest.mark.parametrize("value", ["1", "true", "yes", "on", "TRUE", "Yes"])
def test_is_confirmed_returns_true_from_env(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("RESET_GRAPH", value)
    assert _is_confirmed(False) is True


@pytest.mark.parametrize("value", ["0", "false", "no", "off", "", "maybe"])
def test_is_confirmed_returns_false_from_env(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("RESET_GRAPH", value)
    assert _is_confirmed(False) is False


def _make_count_result(count: int) -> MagicMock:
    """Create a mock session.run result whose .single().data() returns a count."""

    result = MagicMock()
    result.single.return_value = MagicMock(data=MagicMock(return_value={"count": count}))
    return result


def _make_mock_session() -> MagicMock:
    """Create a mock Neo4j session usable as a context manager."""

    session = MagicMock()
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=False)
    return session


def test_reset_graph_with_driver_deletes_nodes_and_relationships() -> None:
    mock_driver = MagicMock()
    mock_session = _make_mock_session()
    mock_driver.session.return_value = mock_session

    mock_session.run.side_effect = [
        _make_count_result(10),   # before nodes
        _make_count_result(7),    # before relationships
        MagicMock(),              # delete query
        _make_count_result(0),    # after nodes
        _make_count_result(0),    # after relationships
    ]

    summary = reset_graph_with_driver(mock_driver)

    assert summary.nodes_deleted == 10
    assert summary.relationships_deleted == 7
    assert mock_session.run.call_count == 5


def test_reset_graph_with_driver_reports_zero_when_graph_already_empty() -> None:
    mock_driver = MagicMock()
    mock_session = _make_mock_session()
    mock_driver.session.return_value = mock_session

    mock_session.run.side_effect = [
        _make_count_result(0),    # before nodes
        _make_count_result(0),    # before relationships
        MagicMock(),              # delete query
        _make_count_result(0),    # after nodes
        _make_count_result(0),    # after relationships
    ]

    summary = reset_graph_with_driver(mock_driver)

    assert summary.nodes_deleted == 0
    assert summary.relationships_deleted == 0


def test_reset_graph_with_driver_uses_correct_delete_query() -> None:
    mock_driver = MagicMock()
    mock_session = _make_mock_session()
    mock_driver.session.return_value = mock_session

    mock_session.run.side_effect = [
        _make_count_result(0),    # before nodes
        _make_count_result(0),    # before relationships
        MagicMock(),              # delete query
        _make_count_result(0),    # after nodes
        _make_count_result(0),    # after relationships
    ]

    reset_graph_with_driver(mock_driver)

    delete_call = mock_session.run.call_args_list[2]
    assert "DETACH DELETE node" in delete_call.args[0]
    assert delete_call.kwargs["labels"] == list(DEMO_LABELS)
