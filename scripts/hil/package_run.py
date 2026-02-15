#!/usr/bin/env python3
"""Scaffold tool for packaging a HIL run into fixture format.

This script currently validates argument shape and prints target paths.
Future slices will add file-copy/sanitization behavior.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="package_run")
    parser.add_argument("--run-id", required=True, help="Stable run id, e.g. hv60_v4_4_3_2026_02_12")
    parser.add_argument("--reports-dir", default="reports", help="Source report directory")
    parser.add_argument("--dest-root", default="fixtures/hil/runs", help="Fixture root")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    run_dir = Path(args.dest_root) / args.run_id
    print(f"reports_dir={Path(args.reports_dir)}")
    print(f"run_dir={run_dir}")
    print("TODO: implement artifact copy + manifest generation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
