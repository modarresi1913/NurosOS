"""
Cognitive Metabolism demo — "Is this information worth the cognitive cost?"

This experiment demonstrates the CognitiveMetabolism module (Phase 12):
  1. Sweep the energy budget across multiple values.
  2. For each budget, develop an organism and track reward + refusals.
  3. Show the value-of-information decision rule for various operations.
  4. Demonstrate that resource constraints shape developmental trajectories.

Usage:
    python experiments/metabolism_demo.py --steps 60 --budgets 0.05 0.1 0.2 0.5 1.0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from nuros import _dev


def run_metabolism_demo(
    steps: int = 60,
    budgets: list[float] | None = None,
    env_seed: int = 1,
    width: int = 6,
    height: int = 6,
    genome_name: str = "metabolism_demo",
    out_dir: Path | None = None,
) -> dict:
    """Run the metabolism demo."""
    if budgets is None:
        budgets = [0.05, 0.1, 0.2, 0.5, 1.0]

    # 1. Metabolism sweep
    sweep_json = _dev.run_metabolism_sweep(budgets, n_steps=steps, env_seed=env_seed, width=width, height=height, genome_name=genome_name)
    sweep = json.loads(sweep_json)

    print(f"[1] Metabolism sweep ({len(budgets)} budgets, {steps} steps each)")
    print(f"    {'energy_budget':>14}  {'total_reward':>12}  {'mean_reward':>12}  {'refusals':>9}")
    print(f"    {'-'*14}  {'-'*12}  {'-'*12}  {'-'*9}")
    for r in sweep["results"]:
        print(f"    {r['energy_budget']:>14.2f}  {r['total_reward']:>12.4f}  {r['mean_reward']:>12.4f}  {r['refusals']:>9}")

    # 2. Value-of-information decision rule
    print(f"\n[2] Value-of-Information decision rule")
    print(f"    {'operation':>18}  {'cost':>6}  {'gain':>6}  {'worth_it':>9}")
    print(f"    {'-'*18}  {'-'*6}  {'-'*6}  {'-'*9}")
    voi_results = []
    for op in ["perceive", "predict", "memorize", "plan", "simulate", "act"]:
        for gain in [0.01, 0.05, 0.1, 0.2]:
            voi = json.loads(_dev.evaluate_value_of_information(op, gain))
            voi_results.append(voi)
            print(f"    {voi['operation']:>18}  {voi['cost']:>6.3f}  {voi['expected_info_gain']:>6.3f}  {str(voi['worth_it']):>9}")

    # 3. Interpretation
    print(f"\n[3] Interpretation")
    print(f"    The metabolism sweep shows that tighter energy budgets lead to")
    print(f"    more refusals (operations skipped due to insufficient budget).")
    print(f"    The value-of-information rule lets the organism decide whether")
    print(f"    an operation is worth its cognitive cost BEFORE spending.")
    print(f"\n    Interpretation caveat: This is a computational abstraction")
    print(f"    inspired by resource-constrained organisms. It does NOT")
    print(f"    reproduce biological metabolism.")

    result = {
        "experiment": "metabolism_demo",
        "genome_name": genome_name,
        "genome_hash": sweep["genome_hash"],
        "n_steps": steps,
        "env_seed": env_seed,
        "sweep_results": sweep["results"],
        "value_of_information": voi_results,
        "interpretation": (
            "Cognitive metabolism is a computational abstraction inspired by "
            "resource-constrained organisms. It does NOT reproduce biological "
            "metabolism. The value-of-information rule lets the organism "
            "decide whether an operation is worth its cognitive cost."
        ),
    }

    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "metabolism_result.json").write_text(
            json.dumps(result, indent=2, default=str), encoding="utf-8"
        )
        print(f"\nArtifacts written to: {out_dir}")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="NurosOS Cognitive Metabolism demo")
    parser.add_argument("--steps", type=int, default=60)
    parser.add_argument("--budgets", type=float, nargs="+", default=[0.05, 0.1, 0.2, 0.5, 1.0])
    parser.add_argument("--env-seed", type=int, default=1)
    parser.add_argument("--width", type=int, default=6)
    parser.add_argument("--height", type=int, default=6)
    parser.add_argument("--genome-name", type=str, default="metabolism_demo")
    parser.add_argument("--out-dir", type=str, default=None)
    args = parser.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else (_REPO_ROOT / "experiment_outputs" / "metabolism_demo")
    run_metabolism_demo(
        steps=args.steps,
        budgets=args.budgets,
        env_seed=args.env_seed,
        width=args.width,
        height=args.height,
        genome_name=args.genome_name,
        out_dir=out_dir,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
