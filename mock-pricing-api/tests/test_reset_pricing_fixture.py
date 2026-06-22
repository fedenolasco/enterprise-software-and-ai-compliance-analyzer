"""Tests for the mock pricing fixture reset script."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mock_pricing_api.config import DEFAULT_PRICING_FIXTURE_PATH  # noqa: I001
from scripts.reset_pricing_fixture import (  # noqa: I001
    PricingFixtureResetSummary,
    _validate_json_fixture,
    build_parser,
    reset_pricing_fixture,
)


def test_validate_json_fixture_accepts_valid_pricing_file(tmp_path: Path) -> None:
    fixture = tmp_path / "pricing.json"
    fixture.write_text(
        json.dumps({"pricing": [{"software_code": "SW-TEST"}]}), encoding="utf-8"
    )

    _validate_json_fixture(fixture)


def test_validate_json_fixture_rejects_missing_pricing_key(tmp_path: Path) -> None:
    fixture = tmp_path / "bad.json"
    fixture.write_text(json.dumps({"items": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="top-level pricing list"):
        _validate_json_fixture(fixture)


def test_validate_json_fixture_rejects_non_dict_payload(tmp_path: Path) -> None:
    fixture = tmp_path / "bad.json"
    fixture.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    with pytest.raises(ValueError, match="top-level pricing list"):
        _validate_json_fixture(fixture)


def test_reset_pricing_fixture_validates_committed_fixture_without_copying() -> None:
    summary = reset_pricing_fixture(
        source_path=DEFAULT_PRICING_FIXTURE_PATH,
        target_path=DEFAULT_PRICING_FIXTURE_PATH,
    )

    assert summary.copied is False
    assert summary.records == 3
    assert summary.source_path == summary.target_path


def test_reset_pricing_fixture_copies_to_target_when_paths_differ(tmp_path: Path) -> None:
    target = tmp_path / "mutable" / "pricing.json"

    summary = reset_pricing_fixture(
        source_path=DEFAULT_PRICING_FIXTURE_PATH,
        target_path=target,
    )

    assert summary.copied is True
    assert summary.records == 3
    assert summary.target_path.exists()
    assert summary.source_path != summary.target_path


def test_reset_pricing_fixture_summary_is_frozen_dataclass() -> None:
    summary = PricingFixtureResetSummary(
        source_path=Path("/a"),
        target_path=Path("/b"),
        records=5,
        copied=True,
    )
    assert summary.records == 5
    assert summary.copied is True


def test_build_parser_defaults_source_to_committed_fixture() -> None:
    parser = build_parser()
    args = parser.parse_args([])

    assert args.source == DEFAULT_PRICING_FIXTURE_PATH
    assert args.target is None


def test_build_parser_accepts_source_and_target(tmp_path: Path) -> None:
    parser = build_parser()
    custom_source = tmp_path / "custom_source.json"
    custom_target = tmp_path / "custom_target.json"

    args = parser.parse_args(["--source", str(custom_source), "--target", str(custom_target)])

    assert args.source == custom_source
    assert args.target == custom_target
