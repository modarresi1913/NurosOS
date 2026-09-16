"""
Artificial Aging demo — "How does accumulated computational history affect future cognition?"

This experiment demonstrates the AgingModel module (Phase 13):
  1. Develop two organisms from the same genome: one with no aging, one with rapid aging.
  2. Compare their final developmental states.
  3. Show the deltas across all 5 aging dimensions.

Usage:
    python experiments/aging_demo.py --steps 80 --model rapid
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

# Predefined aging models
AGING_MODELS = {
    "none": {},  # empty JSON → all defaults = gentle aging
    "rapid": {
        "memory_degradation_rate": 0.01,
        "memory_degradation_onset": 10,
        "plasticity_decay_rate": 0.005,
        "plasticity_decay_onset": 10,
        "plasticity_floor": 0.01,
        "cognitive_load_increase": 0.005,
        "energy_efficiency_decay": 0.005,
        "max_cognitive_load": 0.9,
        "stability_improvement_rate": 0.005,
        "max_stability": 0.99,
        "prediction_accuracy_improvement": 0.002,
        "self_model_consolidation_rate": 0.005,
        "max_self_model_stability": 0.95,
    },
    "gentle": {
        "memory_degradation_rate": 0.001,
        "memory_degradation_onset": 100,
        "plasticity_decay_rate": 0.0005,
        "plasticity_decay_onset": 50,
        "plasticity_floor": 0.05,
        "cognitive_load_increase": 0.0001,
        "energy_efficiency_decay": 0.0002,
        "max_cognitive_load": 0.8,
        "stability_improvement_rate": 0.001,
        "max_stability": 0.95,
        "prediction_accuracy_improvement": 0.0005,
        "self_model_consolidation_rate": 0.0008,
        "max_self_model_stability": 0.9,
    },
}


def run_aging_demo(
    steps: int = 80,
    model_name: str = "rapid",
    env_seed: int = 1,
    width: int = 6,
    height: int = 6,
    genome_name: str = "aging_demo",
    out_dir: Path | None = None,
) -> dict:
    """Run the aging demo."""
    model = AGING_MODELS.get(model_name)
    if model is None:
        raise ValueError(f"unknown model: {model_name}. Available: {list(AGING_MODELS.keys())}")

    result_json = _dev.run_aging_comparison(
        json.dumps(model), n_steps=steps, env_seed=env_seed, width=width, height=height, genome_name=genome_name
    )
    result = json.loads(result_json)

    print(f"=== Aging Comparison ({steps} steps, model={model_name}) ===")
    print(f"  {'metric':<22} {'no_aging':>10} {'with_aging':>12} {'delta':>10}")
    print(f"  {'-'*22} {'-'*10} {'-'*12} {'-'*10}")
    for key in ["plasticity", "stability", "energy_state", "cognitive_load", "memory_capacity", "prediction_accuracy", "self_model_stability"]:
        a = result["no_aging"][key]
        b = result["with_aging"][key]
        d = result["deltas"][key]
        print(f"  {key:<22} {a:>10.4f} {b:>12.4f} {d:>+10.4f}")

    print(f"\n  Interpretation:")
    print(f"    Aging reduces plasticity and memory capacity while increasing")
    print(f"    self-model stability (consolidation). The organism's accumulated")
    print(f"    computational history shapes its future cognition.")
    print(f"\n  Interpretation caveat: Aging is configurable. Do not impose")
    print(f"    biological aging assumptions without evidence.")

    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "aging_result.json").write_text(
            json.dumps(result, indent=2, default=str), encoding="utf-8"
        )
        print(f"\nArtifacts written to: {out_dir}")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="NurosOS Artificial Aging demo")
    parser.add_argument("--steps", type=int, default=80)
    parser.add_argument("--model", type=str, default="rapid", choices=list(AGING_MODELS.keys()))
    parser.add_argument("--env-seed", type=int, default=1)
    parser.add_argument("--width", type=int, default=6)
    parser.add_argument("--height", type=int, default=6)
    parser.add_argument("--genome-name", type=str, default="aging_demo")
    parser.add_argument("--out-dir", type=str, default=None)
    args = parser.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else (_REPO_ROOT / "experiment_outputs" / "aging_demo")
    run_aging_demo(
        steps=args.steps,
        model_name=args.model,
        env_seed=args.env_seed,
        width=args.width,
        height=args.height,
        genome_name=args.genome_name,
        out_dir=out_dir,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
