"""
Experiment harness for the NurosOS scientific audit.

Per master prompt PHASE 10: structured output directory.

Runs 6 conditions (A=Q-learning, B=NurosOS, C=no maturation,
D=no plasticity decay, E=no self-model, F=no heuristic bias)
x 2 observation modes (privileged, raw) x 30 seeds = 360 runs.

Produces:
  experiment_outputs/<experiment_id>/
    config.json
    manifest.json
    raw/           per-seed results
    metrics/       aggregated metrics
    trajectories/  per-seed trajectories
    report.md      human-readable summary
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from nuros.baselines.q_learning.q_learning_agent import (
    QLearningAgent, QLearningConfig, run_q_learning_episode,
)
from nuros.baselines.simple_organism import SimpleOrganism, GenomeConfig
from nuros.baselines.simple_env import SimpleResourceWorld, SimpleChangingWorld
from environments.nonstationary import NonStationaryEnv


CONDITIONS = {
    "A": {"name": "q_learning", "disable_bias": None, "disable_maturation": None,
           "disable_plasticity_decay": None, "disable_self_model": None,
           "use_memory": None, "memory_engine": None},
    "B": {"name": "nurosos_baseline", "disable_bias": False, "disable_maturation": False,
           "disable_plasticity_decay": False, "disable_self_model": False,
           "use_memory": False, "memory_engine": "default"},
    "C": {"name": "no_maturation", "disable_bias": False, "disable_maturation": True,
           "disable_plasticity_decay": False, "disable_self_model": False,
           "use_memory": False, "memory_engine": "default"},
    "D": {"name": "no_plasticity_decay", "disable_bias": False, "disable_maturation": False,
           "disable_plasticity_decay": True, "disable_self_model": False,
           "use_memory": False, "memory_engine": "default"},
    "E": {"name": "no_self_model", "disable_bias": False, "disable_maturation": False,
           "disable_plasticity_decay": False, "disable_self_model": True,
           "use_memory": False, "memory_engine": "default"},
    "F": {"name": "no_heuristic_bias", "disable_bias": True, "disable_maturation": False,
           "disable_plasticity_decay": False, "disable_self_model": False,
           "use_memory": False, "memory_engine": "default"},
    "G": {"name": "nurosos_plus_memory", "disable_bias": False, "disable_maturation": False,
           "disable_plasticity_decay": False, "disable_self_model": False,
           "use_memory": True, "memory_engine": "default"},
    "H": {"name": "nurosos_plus_hippocore", "disable_bias": False, "disable_maturation": False,
           "disable_plasticity_decay": False, "disable_self_model": False,
           "use_memory": True, "memory_engine": "hippocore"},
}


def run_single_experiment(
    condition_id: str,
    privileged_obs: bool,
    seed: int,
    n_steps: int = 300,
) -> dict[str, Any]:
    """Run one experiment and return results."""
    cond = CONDITIONS[condition_id]
    env = NonStationaryEnv(env_seed=seed, privileged_obs=privileged_obs)

    if condition_id == "A":
        # Q-learning baseline.
        config = QLearningConfig(
            alpha=0.1, gamma=0.95, epsilon=0.1,
            q_table_capacity=200, privileged_obs=privileged_obs,
            seed=seed, n_steps=n_steps,
        )
        from nuros.baselines.q_learning.q_learning_agent import state_signature
        agent = QLearningAgent(config)
        per_step = []
        obs = env.reset()
        for step in range(n_steps):
            action = agent.select_action(obs)
            next_obs, reward, done = env.step(action)
            agent.update(obs, action, reward, next_obs, done)
            per_step.append({
                "step": step + 1, "action": action, "reward": reward,
                "regime": env.regime,
            })
            obs = next_obs
            if done:
                break
        return {
            "condition": condition_id, "condition_name": cond["name"],
            "privileged_obs": privileged_obs, "seed": seed,
            "total_reward": agent.total_reward, "n_steps": len(per_step),
            "q_table_size": agent.q_table_size,
            "per_step": per_step,
        }
    else:
        # NurosOS organism (Python port).
        genome = GenomeConfig(
            disable_heuristic_bias=cond["disable_bias"],
            disable_maturation=cond["disable_maturation"],
            disable_plasticity_decay=cond["disable_plasticity_decay"],
            disable_self_model=cond["disable_self_model"],
            use_memory=cond.get("use_memory", False),
            memory_engine=cond.get("memory_engine", "default"),
            replay_interval=50,
            consolidate_interval=100,
        )
        organism = SimpleOrganism(genome, organism_id=f"org-{condition_id}-{seed}")
        per_step = []
        env.reset()
        for step in range(n_steps):
            record = organism.tick(env)
            record["regime"] = env.regime
            per_step.append(record)
            if step + 1 >= n_steps:
                break
        return {
            "condition": condition_id, "condition_name": cond["name"],
            "privileged_obs": privileged_obs, "seed": seed,
            "total_reward": organism.total_reward, "n_steps": len(per_step),
            "memory_size": len(organism.memory),
            "dev_stage": organism.dev_stage,
            "dev_plasticity": organism.dev_plasticity,
            "per_step": per_step,
        }


def run_full_experiment(
    out_root: str = "./experiment_outputs",
    n_seeds: int = 30,
    base_seed: int = 42,
    n_steps: int = 300,
) -> dict[str, Any]:
    """Run the full 6 conditions × 2 modes × N seeds experiment."""
    experiment_id = f"audit_{n_seeds}seeds_{int(time.time())}"
    out_dir = Path(out_root) / experiment_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "raw").mkdir(exist_ok=True)
    (out_dir / "metrics").mkdir(exist_ok=True)
    (out_dir / "trajectories").mkdir(exist_ok=True)

    config = {
        "experiment_id": experiment_id,
        "n_seeds": n_seeds, "base_seed": base_seed,
        "n_steps": n_steps,
        "conditions": CONDITIONS,
        "observation_modes": ["privileged", "raw"],
    }
    (out_dir / "config.json").write_text(json.dumps(config, indent=2, default=str))

    all_results: list[dict[str, Any]] = []
    total_runs = len(CONDITIONS) * 2 * n_seeds
    run_count = 0

    for cond_id in CONDITIONS:
        for priv in [True, False]:
            mode_name = "privileged" if priv else "raw"
            for seed_offset in range(n_seeds):
                seed = base_seed + seed_offset
                run_count += 1
                result = run_single_experiment(cond_id, priv, seed, n_steps)
                all_results.append(result)
                # Save raw per-seed result.
                fname = f"{cond_id}_{mode_name}_seed{seed}.json"
                (out_dir / "raw" / fname).write_text(
                    json.dumps(result, indent=2, default=str)
                )
                if run_count % 30 == 0:
                    print(f"  [{run_count}/{total_runs}] {cond_id}/{mode_name}/seed{seed}: reward={result['total_reward']:.2f}", flush=True)

    # Aggregate.
    summary = aggregate_results(all_results)
    (out_dir / "metrics" / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str)
    )

    # Report.
    report = generate_report(summary, config)
    (out_dir / "report.md").write_text(report)

    print(f"\n✅ Experiment complete: {total_runs} runs")
    print(f"   Output: {out_dir}")
    return summary


def aggregate_results(results: list[dict]) -> dict[str, Any]:
    """Aggregate per-seed results into mean ± std per condition."""
    import statistics
    from collections import defaultdict

    by_cell: dict[str, list[float]] = defaultdict(list)
    for r in results:
        cell = f"{r['condition']}_{r['condition_name']}_{('priv' if r['privileged_obs'] else 'raw')}"
        by_cell[cell].append(r["total_reward"])

    summary = {}
    for cell, rewards in sorted(by_cell.items()):
        mean = statistics.mean(rewards)
        std = statistics.stdev(rewards) if len(rewards) > 1 else 0.0
        summary[cell] = {
            "mean": round(mean, 4),
            "std": round(std, 4),
            "n": len(rewards),
            "min": round(min(rewards), 4),
            "max": round(max(rewards), 4),
            "per_seed": [round(r, 4) for r in rewards],
        }

    # Effect sizes vs condition B (NurosOS baseline).
    for mode in ["priv", "raw"]:
        b_key = f"B_nurosos_baseline_{mode}"
        if b_key not in summary:
            continue
        b_mean = summary[b_key]["mean"]
        b_std = summary[b_key]["std"]
        for cond in ["A", "C", "D", "E", "F"]:
            for cond_name in CONDITIONS[cond]["name"]:
                key = f"{cond}_{cond_name}_{mode}"
                pass
        # Simpler: iterate by prefix.
        for key in summary:
            if not key.endswith(f"_{mode}") or key == b_key:
                continue
            cond_mean = summary[key]["mean"]
            cond_std = summary[key]["std"]
            # Cohen's d.
            pooled_std = ((b_std ** 2 + cond_std ** 2) / 2) ** 0.5
            d = (cond_mean - b_mean) / pooled_std if pooled_std > 0 else 0.0
            summary[key]["cohens_d_vs_B"] = round(d, 4)

    return summary


def generate_report(summary: dict, config: dict) -> str:
    """Generate a human-readable Markdown report."""
    lines = [
        f"# Experiment Report — {config['experiment_id']}",
        "",
        f"- **Seeds**: {config['n_seeds']}",
        f"- **Steps per run**: {config['n_steps']}",
        f"- **Total runs**: {len(config['conditions']) * 2 * config['n_seeds']}",
        "",
        "## Results: Cumulative Reward (mean ± std)",
        "",
        "| Condition | Mode | Mean | Std | n | Min | Max | Cohen's d vs B |",
        "|-----------|------|------|-----|---|-----|-----|-----------------|",
    ]
    for key in sorted(summary):
        s = summary[key]
        parts = key.rsplit("_", 1)
        cond = parts[0] if len(parts) > 1 else key
        mode = parts[1] if len(parts) > 1 else "?"
        d = s.get("cohens_d_vs_B", "—")
        d_str = f"{d:+.3f}" if isinstance(d, float) else str(d)
        lines.append(
            f"| {cond} | {mode} | {s['mean']:.4f} | {s['std']:.4f} | "
            f"{s['n']} | {s['min']:.4f} | {s['max']:.4f} | {d_str} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- **Positive Cohen's d** means the condition performed BETTER than B (NurosOS baseline).")
    lines.append("- **Negative Cohen's d** means the condition performed WORSE than B.")
    lines.append("- **|d| > 0.3** is a practically significant effect size.")
    lines.append("- **Condition F (no heuristic bias)** is the CRITICAL ablation: if F << B, the bias carries the performance.")
    lines.append("- **Condition A (Q-learning)** vs B: if A >= B, NurosOS provides no measurable value.")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    run_full_experiment(n_seeds=n_seeds)
