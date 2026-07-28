#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyyaml>=6.0.2,<7",
# ]
# ///
"""Resolve one Figma-bound contract against the active project release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from figma_release import FigmaReleaseError, resolve_contract_figma_release


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--contract-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        resolution = resolve_contract_figma_release(
            args.project_root,
            args.contract_file,
        )
    except (FigmaReleaseError, OSError) as exc:
        parser.error(str(exc))
    result = (
        {
            "status": "unconfigured",
            "action": "use-contract-binding",
        }
        if resolution is None
        else resolution.to_dict()
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
