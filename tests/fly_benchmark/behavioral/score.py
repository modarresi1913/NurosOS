#!/usr/bin/env python3
"""Fly Benchmark behavioral scoring.

Reads the JSON output of `fly_benchmark/main.rs` and computes an
aggregate score. Used by `make test-fly-benchmark` as the final
gate for PR approval.

Biological correspondence
-------------------------
This is the equivalent of a **behavioral quantification pipeline** in
ethology — the statistical machinery that turns raw video recordings
of fly behavior into a single, comparable "performance" number.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Score the Fly Benchmark")
    parser.add_argument("--json", action="store_true",
                       help="Emit machine-readable JSON instead of human-readable text")
    parser.add_argument("--input", type=Path, default=None,
                       help="Input JSON file (default: read stdin)")
    args = parser.parse_args()

    text = (args.input.read_text(encoding="utf-8") if args.input
            else sys.stdin.read())
    data = json.loads(text)

    results = data.get("results", [])
    aggregate = sum(r["score"] for r in results) / max(len(results), 1)
    all_passed = all(r["passed"] for r in results)

    if args.json:
        out = {
            "aggregate_score": aggregate,
            "all_passed": all_passed,
            "sub_suites": results,
        }
        print(json.dumps(out, indent=2))
    else:
        print(f"Fly Benchmark aggregate score: {aggregate:.3f}")
        print(f"Status: {'PASS' if all_passed else 'FAIL'}")
        for r in results:
            status = "✓" if r["passed"] else "✗"
            print(f"  {status} {r['name']}: {r['score']:.3f} (threshold: {r['threshold']:.3f})")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
