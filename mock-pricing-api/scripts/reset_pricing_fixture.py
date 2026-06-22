"""Reset or validate the deterministic mock pricing fixture.

The mock pricing service currently reads committed JSON fixture data and keeps
records in memory. This script gives demo operators a stable reset command now,
and it can also copy the committed fixture into a mutable fixture path when
`PRICING_FIXTURE_PATH` points somewhere outside the source tree.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mock_pricing_api.config import (  # noqa: E402, I001
    DEFAULT_PRICING_FIXTURE_PATH,
    get_settings,
)
from mock_pricing_api.repository import PricingRepository  # noqa: E402, I001


@dataclass(frozen=True)
class PricingFixtureResetSummary:
    """Summary of pricing fixture reset or validation."""

    source_path: Path
    target_path: Path
    records: int
    copied: bool


def reset_pricing_fixture(
    *,
    source_path: Path = DEFAULT_PRICING_FIXTURE_PATH,
    target_path: Path | None = None,
) -> PricingFixtureResetSummary:
    """Restore the target pricing fixture from source and validate it."""

    target = target_path or get_settings().pricing_fixture_path
    source = source_path.resolve()
    resolved_target = target.resolve()

    _validate_json_fixture(source)
    copied = False
    if source != resolved_target:
        resolved_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, resolved_target)
        copied = True

    repository = PricingRepository(resolved_target)
    return PricingFixtureResetSummary(
        source_path=source,
        target_path=resolved_target,
        records=len(repository.records),
        copied=copied,
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""

    parser = argparse.ArgumentParser(
        description="Reset or validate the deterministic mock pricing fixture."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_PRICING_FIXTURE_PATH,
        help="Source fixture to copy from. Defaults to the committed pricing fixture.",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=None,
        help="Target fixture path. Defaults to PRICING_FIXTURE_PATH or the committed fixture.",
    )
    return parser


def main() -> None:
    """Run the pricing fixture reset command."""

    args = build_parser().parse_args()
    summary = reset_pricing_fixture(source_path=args.source, target_path=args.target)
    action = "copied" if summary.copied else "validated"
    print(
        f"Pricing fixture {action}: {summary.records} records at "
        f"{summary.target_path} from {summary.source_path}."
    )


def _validate_json_fixture(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("pricing"), list):
        raise ValueError(f"{path} must contain a top-level pricing list.")


if __name__ == "__main__":
    main()
