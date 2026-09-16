"""
Mind Observatory — observability layer for the NurosOS developmental substrate.

The Observatory is an **experimental instrument**, not a decorative dashboard.
It reads the artifacts produced by an experiment (trajectories, telemetry,
checkpoints, divergence, mind diff, manifest) and produces:

  - **Text renderers** for terminal/CLI inspection (timeline replay, mind diff,
    causal trace, checkpoints overview, environment events).
  - **PNG plots** for paper-ready figures (developmental trajectory, prediction
    error, reward curves, memory changes, state transitions, resource
    consumption, divergence comparison).

Usage
-----
    from nuros.observatory import Observatory
    obs = Observatory.from_experiment_dir(Path("experiment_outputs/same_genome_different_world"))
    print(obs.render_timeline_replay(organism_id="organism_a", start=0, end=20))
    obs.plot_developmental_trajectory(organism_id="organism_a", out_path=Path("dev_traj.png"))
    obs.render_all(out_dir=Path("observatory_outputs"))

Implementation Status: [IMPLEMENTED] — text renderers + PNG plots.
"""

from __future__ import annotations

import csv
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ============================================================================
# Artifact loaders
# ============================================================================


@dataclass
class TrajectoryPoint:
    """A single point in a developmental trajectory (parsed from JSONL)."""
    step: int
    action: str
    observation: dict[str, Any]
    reward: float
    prediction_error: float
    predicted_reward: float
    developmental_stage: str
    energy: float
    plasticity: float
    memory_size: int
    state_hash: str


@dataclass
class TelemetryRow:
    """A single telemetry row (parsed from CSV)."""
    step: int
    action: str
    reward: float
    prediction_error: float
    developmental_stage: str
    energy: float
    plasticity: float
    memory_size: int
    cum_reward: float
    cum_pe: float
    state_hash: str


@dataclass
class ExperimentArtifacts:
    """All artifacts produced by a Same Genome / Different World experiment."""
    experiment_dir: Path
    genome: dict[str, Any] = field(default_factory=dict)
    trajectories: dict[str, list[TrajectoryPoint]] = field(default_factory=dict)
    telemetry: dict[str, list[TelemetryRow]] = field(default_factory=dict)
    checkpoints: dict[str, dict[str, Any]] = field(default_factory=dict)
    divergence: dict[str, Any] = field(default_factory=dict)
    mind_diff: dict[str, Any] = field(default_factory=dict)
    manifests: dict[str, dict[str, Any]] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)

    @property
    def organism_ids(self) -> list[str]:
        return sorted(self.trajectories.keys())


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _parse_trajectory_point(d: dict[str, Any]) -> TrajectoryPoint:
    return TrajectoryPoint(
        step=int(d.get("step", 0)),
        action=str(d.get("action", "")),
        observation=d.get("observation", {}) if isinstance(d.get("observation"), dict) else {},
        reward=float(d.get("reward", 0.0)),
        prediction_error=float(d.get("prediction_error", 0.0)),
        predicted_reward=float(d.get("predicted_reward", 0.0)),
        developmental_stage=str(d.get("developmental_stage", "")),
        energy=float(d.get("energy", 0.0)),
        plasticity=float(d.get("plasticity", 0.0)),
        memory_size=int(d.get("memory_size", 0)),
        state_hash=str(d.get("state_hash", "")),
    )


def _parse_telemetry_row(d: dict[str, str]) -> TelemetryRow:
    return TelemetryRow(
        step=int(d.get("step", 0)),
        action=str(d.get("action", "")),
        reward=float(d.get("reward", 0.0)),
        prediction_error=float(d.get("prediction_error", 0.0)),
        developmental_stage=str(d.get("developmental_stage", "")),
        energy=float(d.get("energy", 0.0)),
        plasticity=float(d.get("plasticity", 0.0)),
        memory_size=int(d.get("memory_size", 0)),
        cum_reward=float(d.get("cum_reward", 0.0)),
        cum_pe=float(d.get("cum_pe", 0.0)),
        state_hash=str(d.get("state_hash", "")),
    )


def load_artifacts(experiment_dir: Path) -> ExperimentArtifacts:
    """Load all artifacts from a Same Genome / Different World experiment dir."""
    art = ExperimentArtifacts(experiment_dir=experiment_dir)

    # Genome
    art.genome = _load_json(experiment_dir / "genome.json")

    # Trajectories + telemetry (organism_a, organism_b)
    for org_id, traj_file, tel_file in [
        ("organism_a", "trajectory_a.jsonl", "telemetry_a.csv"),
        ("organism_b", "trajectory_b.jsonl", "telemetry_b.csv"),
    ]:
        raw_traj = _load_jsonl(experiment_dir / traj_file)
        art.trajectories[org_id] = [_parse_trajectory_point(d) for d in raw_traj]
        raw_tel = _load_csv(experiment_dir / tel_file)
        art.telemetry[org_id] = [_parse_telemetry_row(d) for d in raw_tel]

    # Checkpoints
    for org_id, ckpt_file in [("organism_a", "checkpoint_a.json"), ("organism_b", "checkpoint_b.json")]:
        art.checkpoints[org_id] = _load_json(experiment_dir / ckpt_file)

    # Divergence + mind diff + manifests + summary
    art.divergence = _load_json(experiment_dir / "divergence.json")
    art.mind_diff = _load_json(experiment_dir / "mind_diff.json")
    for org_id, man_file in [("organism_a", "manifest_a.json"), ("organism_b", "manifest_b.json")]:
        art.manifests[org_id] = _load_json(experiment_dir / man_file)
    art.summary = _load_json(experiment_dir / "summary.json")

    return art


# ============================================================================
# Observatory
# ============================================================================


class Observatory:
    """An experimental instrument for inspecting developmental trajectories.

    The Observatory reads the artifacts produced by a Same Genome / Different
    World experiment and produces text renderers (for terminal inspection) and
    PNG plots (for paper-ready figures).
    """

    def __init__(self, artifacts: ExperimentArtifacts) -> None:
        self.art = artifacts

    @classmethod
    def from_experiment_dir(cls, experiment_dir: Path | str) -> "Observatory":
        """Load artifacts from an experiment output directory."""
        return cls(load_artifacts(Path(experiment_dir)))

    # ------------------------------------------------------------------
    # Text renderers
    # ------------------------------------------------------------------

    def render_timeline_replay(
        self,
        organism_id: str,
        start: int = 0,
        end: Optional[int] = None,
        show_observation: bool = False,
    ) -> str:
        """Render a step-by-step timeline replay for an organism.

        Each step shows: step | action | reward | prediction_error | stage |
        energy | plasticity | memory_size | state_hash.
        """
        traj = self.art.trajectories.get(organism_id, [])
        if not traj:
            return f"[error] no trajectory found for organism_id={organism_id}"
        end = end or len(traj)
        slice_ = traj[start:end]
        lines: list[str] = []
        lines.append(f"=== Timeline Replay: {organism_id} (steps {start}..{end - 1}) ===")
        lines.append(
            f"{'step':>5}  {'action':<12} {'reward':>8} {'pe':>8} {'stage':<14} "
            f"{'energy':>6} {'plast':>6} {'mem':>4}  {'state_hash':<12}"
        )
        lines.append("-" * 90)
        for p in slice_:
            lines.append(
                f"{p.step:>5}  {p.action:<12} {p.reward:>8.4f} {p.prediction_error:>8.4f} "
                f"{p.developmental_stage:<14} {p.energy:>6.3f} {p.plasticity:>6.3f} "
                f"{p.memory_size:>4}  {p.state_hash[:12]:<12}"
            )
            if show_observation and p.observation:
                obs_str = json.dumps(p.observation, sort_keys=True)
                if len(obs_str) > 100:
                    obs_str = obs_str[:97] + "..."
                lines.append(f"       obs: {obs_str}")
        return "\n".join(lines)

    def render_mind_diff(self) -> str:
        """Render the mind diff between the two organisms' final states."""
        d = self.art.mind_diff
        if not d:
            return "[error] no mind_diff found"
        lines: list[str] = []
        lines.append("=== Mind Diff (final state A vs final state B) ===")
        lines.append(f"  state_a_hash:        {d.get('state_a_hash', '')[:12]}...")
        lines.append(f"  state_b_hash:        {d.get('state_b_hash', '')[:12]}...")
        lines.append(f"  step_delta:          {d.get('step_delta', 0)}")
        lines.append(f"  identical:           {d.get('identical', False)}")
        mc = d.get("memory_changes", {})
        lines.append(f"  memory added/removed: {mc.get('added', 0)}/{mc.get('removed', 0)}")
        vc = d.get("value_changes", {})
        lines.append(f"  value_changes L1:    {vc.get('total_l1', 0.0):.4f}")
        dc = d.get("developmental_changes", {})
        lines.append(f"  dev state L1:        {dc.get('state_l1_distance', 0.0):.4f}")
        lines.append(f"  stage A -> B:        {dc.get('stage_a', '?')} -> {dc.get('stage_b', '?')}")
        return "\n".join(lines)

    def render_causal_trace(self, event_id: Optional[int] = None, max_events: int = 20) -> str:
        """Render a causal trace from a checkpoint's causality graph.

        Note: the current flagship experiment does not serialize a full
        causality graph. This renderer shows the closest available provenance:
        the sequence of (action, reward, prediction_error) events from the
        trajectory, which is the causal backbone of the developmental loop.
        """
        # The current flagship doesn't serialize a DevelopmentalCausalityGraph.
        # We render the trajectory as a causal backbone instead.
        lines: list[str] = []
        lines.append("=== Causal Trace (trajectory backbone) ===")
        lines.append("Note: Full DevelopmentalCausalityGraph serialization is [PROPOSED].")
        lines.append("Rendering the trajectory's (observation -> action -> outcome) chain.")
        lines.append("")
        for org_id in self.art.organism_ids:
            traj = self.art.trajectories[org_id]
            lines.append(f"--- {org_id} (first {max_events} steps) ---")
            for p in traj[:max_events]:
                obs_keys = sorted(p.observation.keys()) if p.observation else []
                obs_summary = ", ".join(f"{k}={_short(p.observation[k])}" for k in obs_keys[:3])
                lines.append(
                    f"  step={p.step:>3}  obs[{obs_summary}]  "
                    f"-> action={p.action}  -> reward={p.reward:+.3f}  "
                    f"(pe={p.prediction_error:.3f}, pred={p.predicted_reward:+.3f})"
                )
            lines.append("")
        return "\n".join(lines)

    def render_environment_events(self, organism_id: str, max_events: int = 30) -> str:
        """Render environment-side events (observations) for an organism."""
        traj = self.art.trajectories.get(organism_id, [])
        if not traj:
            return f"[error] no trajectory for {organism_id}"
        lines: list[str] = []
        lines.append(f"=== Environment Events: {organism_id} (first {max_events}) ===")
        lines.append(f"{'step':>5}  {'on_res':>6} {'on_haz':>6} {'dist':>6} {'total_left':>10}  {'agent_pos'}")
        lines.append("-" * 60)
        for p in traj[:max_events]:
            obs = p.observation
            on_res = obs.get("on_resource", False)
            on_haz = obs.get("on_hazard", False)
            dist = obs.get("nearest_resource_distance", -1)
            total = obs.get("total_resource_left", 0.0)
            pos = obs.get("agent_pos", "?")
            lines.append(
                f"{p.step:>5}  {str(on_res):>6} {str(on_haz):>6} {dist:>6.1f} {total:>10.3f}  {pos}"
            )
        return "\n".join(lines)

    def render_checkpoints(self) -> str:
        """Render an overview of all checkpoints."""
        lines: list[str] = []
        lines.append("=== Checkpoints Overview ===")
        for org_id, ckpt in self.art.checkpoints.items():
            if not ckpt:
                continue
            lines.append(f"--- {org_id} ---")
            lines.append(f"  checkpoint_id:    {ckpt.get('checkpoint_id', '')}")
            lines.append(f"  organism_id:      {ckpt.get('organism_id', '')}")
            lines.append(f"  genome_hash:      {ckpt.get('genome_hash', '')[:24]}...")
            lines.append(f"  environment_hash: {ckpt.get('environment_hash', '')[:24]}...")
            lines.append(f"  state_hash:       {ckpt.get('state_hash', '')[:24]}...")
            lines.append(f"  step:             {ckpt.get('step', 0)}")
            lines.append(f"  runtime_version:  {ckpt.get('runtime_version', '')}")
            lines.append(f"  label:            {ckpt.get('label', '')}")
            lines.append("")
        return "\n".join(lines)

    def render_manifests(self) -> str:
        """Render the reproducibility manifests."""
        lines: list[str] = []
        lines.append("=== Reproducibility Manifests ===")
        for org_id, man in self.art.manifests.items():
            if not man:
                continue
            lines.append(f"--- {org_id} ---")
            lines.append(f"  mind_id:            {man.get('mind_id', '')}")
            lines.append(f"  genome_hash:        {man.get('genome_hash', '')[:24]}...")
            lines.append(f"  runtime_hash:       {man.get('runtime_hash', '')[:24]}...")
            lines.append(f"  environment_hash:   {man.get('environment_hash', '')[:24]}...")
            lines.append(f"  experiment_hash:    {man.get('experiment_hash', '')[:24]}...")
            lines.append(f"  configuration_hash: {man.get('configuration_hash', '')[:24]}...")
            lines.append(f"  checkpoint_hash:    {man.get('checkpoint_hash', '')[:24]}...")
            lines.append(f"  random_seed:        {man.get('random_seed', 0)}")
            lines.append(f"  environment_seed:   {man.get('environment_seed', 0)}")
            lines.append(f"  n_steps:            {man.get('n_steps', 0)}")
            lines.append(f"  timestamp:          {man.get('timestamp', 0)}")
            deps = man.get("dependency_versions", {})
            if deps:
                lines.append("  dependencies:")
                for k, v in deps.items():
                    lines.append(f"    {k} = {v}")
            limitations = man.get("limitations", [])
            if limitations:
                lines.append("  limitations:")
                for l in limitations:
                    lines.append(f"    - {l}")
            lines.append("")
        return "\n".join(lines)

    def render_divergence(self) -> str:
        """Render the developmental divergence between the two organisms."""
        d = self.art.divergence
        if not d:
            return "[error] no divergence found"
        lines: list[str] = []
        lines.append("=== Developmental Divergence ===")
        lines.append(f"  organism_a:          {d.get('organism_a', '')}")
        lines.append(f"  organism_b:          {d.get('organism_b', '')}")
        lines.append(f"  genome_hash:         {d.get('genome_hash', '')[:24]}...")
        lines.append(f"  env_a_hash:          {d.get('environment_a_hash', '')[:24]}...")
        lines.append(f"  env_b_hash:          {d.get('environment_b_hash', '')[:24]}...")
        lines.append(f"  n_steps:             {d.get('n_steps', 0)}")
        lines.append(f"  reward_distance:     {d.get('reward_distance', 0.0):.4f}")
        lines.append(f"  pe_distance:         {d.get('prediction_error_distance', 0.0):.4f}")
        lines.append(f"  action_distance:     {d.get('action_distance', 0.0):.0f} / {d.get('n_steps', 0)}")
        lines.append(f"  mean_state_distance: {d.get('mean_state_distance', 0.0):.4f}")
        lines.append(f"  final_state_distance:{d.get('final_state_distance', 0.0):.4f}")
        lines.append(f"  stage_divergence:    {d.get('stage_divergence', False)}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # PNG plots (matplotlib)
    # ------------------------------------------------------------------

    def _setup_matplotlib(self):
        """Configure matplotlib for CJK + Latin + symbols."""
        import matplotlib
        matplotlib.use("Agg")  # non-interactive
        import matplotlib.font_manager as fm
        # Register Noto Sans SC for any non-Latin glyphs + DejaVu Sans for symbols.
        for path in [
            "/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]:
            if Path(path).exists():
                fm.fontManager.addfont(path)
        import matplotlib.pyplot as plt
        plt.rcParams["font.sans-serif"] = ["Noto Sans SC", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False
        return plt

    def plot_developmental_trajectory(
        self, organism_id: str, out_path: Path, figsize: tuple[float, float] = (10, 6)
    ) -> Path:
        """Plot the developmental trajectory: plasticity, stability, prediction accuracy."""
        plt = self._setup_matplotlib()
        tel = self.art.telemetry.get(organism_id, [])
        if not tel:
            raise ValueError(f"no telemetry for {organism_id}")
        steps = [r.step for r in tel]
        plasticity = [r.plasticity for r in tel]
        energy = [r.energy for r in tel]
        # prediction_accuracy is not in the CSV; reconstruct from pe
        pred_acc = [1.0 / (1.0 + r.prediction_error) for r in tel]

        fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
        ax.plot(steps, plasticity, label="plasticity", color="#1f77b4", linewidth=1.5)
        ax.plot(steps, energy, label="energy_state", color="#2ca02c", linewidth=1.5)
        ax.plot(steps, pred_acc, label="prediction_accuracy (reconstructed)", color="#d62728", linewidth=1.5)
        ax.set_xlabel("step")
        ax.set_ylabel("value (0..1)")
        ax.set_title(f"Developmental Trajectory — {organism_id}")
        ax.set_ylim(-0.05, 1.1)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize=9)
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        return out_path

    def plot_prediction_error(
        self, organism_id: str, out_path: Path, figsize: tuple[float, float] = (10, 5)
    ) -> Path:
        """Plot per-step prediction error + reward for an organism."""
        plt = self._setup_matplotlib()
        tel = self.art.telemetry.get(organism_id, [])
        if not tel:
            raise ValueError(f"no telemetry for {organism_id}")
        steps = [r.step for r in tel]
        pe = [r.prediction_error for r in tel]
        reward = [r.reward for r in tel]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True, constrained_layout=True)
        ax1.plot(steps, pe, color="#d62728", linewidth=1.0, label="prediction_error")
        ax1.set_ylabel("prediction error")
        ax1.set_title(f"Prediction Error + Reward — {organism_id}")
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc="best", fontsize=9)

        ax2.plot(steps, reward, color="#1f77b4", linewidth=1.0, label="reward")
        ax2.axhline(0.0, color="black", linewidth=0.5, alpha=0.5)
        ax2.set_xlabel("step")
        ax2.set_ylabel("reward")
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc="best", fontsize=9)

        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        return out_path

    def plot_memory_changes(
        self, organism_id: str, out_path: Path, figsize: tuple[float, float] = (10, 5)
    ) -> Path:
        """Plot memory size over time + cumulative reward."""
        plt = self._setup_matplotlib()
        tel = self.art.telemetry.get(organism_id, [])
        if not tel:
            raise ValueError(f"no telemetry for {organism_id}")
        steps = [r.step for r in tel]
        mem = [r.memory_size for r in tel]
        cum = [r.cum_reward for r in tel]

        fig, ax1 = plt.subplots(figsize=figsize, constrained_layout=True)
        ax1.plot(steps, mem, color="#9467bd", linewidth=1.5, label="memory_size")
        ax1.set_xlabel("step")
        ax1.set_ylabel("memory size", color="#9467bd")
        ax1.tick_params(axis="y", labelcolor="#9467bd")
        ax1.grid(True, alpha=0.3)

        ax2 = ax1.twinx()
        ax2.plot(steps, cum, color="#ff7f0e", linewidth=1.5, label="cumulative_reward")
        ax2.set_ylabel("cumulative reward", color="#ff7f0e")
        ax2.tick_params(axis="y", labelcolor="#ff7f0e")

        ax1.set_title(f"Memory Changes + Cumulative Reward — {organism_id}")
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        return out_path

    def plot_state_transitions(
        self, organism_id: str, out_path: Path, figsize: tuple[float, float] = (10, 4)
    ) -> Path:
        """Plot developmental stage transitions as a step function."""
        plt = self._setup_matplotlib()
        tel = self.art.telemetry.get(organism_id, [])
        if not tel:
            raise ValueError(f"no telemetry for {organism_id}")
        stages = ["EMBRYONIC", "NASCENT", "DEVELOPING", "MATURING", "MATURE", "SPECIALIZED", "AGING", "TERMINATED"]
        stage_to_y = {s: i for i, s in enumerate(stages)}
        steps = [r.step for r in tel]
        y = [stage_to_y.get(r.developmental_stage, 0) for r in tel]

        fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
        ax.step(steps, y, where="post", color="#2ca02c", linewidth=1.5)
        ax.set_yticks(range(len(stages)))
        ax.set_yticklabels(stages, fontsize=8)
        ax.set_xlabel("step")
        ax.set_title(f"Developmental Stage Transitions — {organism_id}")
        ax.grid(True, alpha=0.3, axis="x")
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        return out_path

    def plot_resource_consumption(
        self, organism_id: str, out_path: Path, figsize: tuple[float, float] = (10, 5)
    ) -> Path:
        """Plot energy + cognitive load over time."""
        plt = self._setup_matplotlib()
        traj = self.art.trajectories.get(organism_id, [])
        if not traj:
            raise ValueError(f"no trajectory for {organism_id}")
        steps = [p.step for p in traj]
        energy = [p.energy for p in traj]
        plasticity = [p.plasticity for p in traj]

        fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
        ax.plot(steps, energy, color="#2ca02c", linewidth=1.5, label="energy_state")
        ax.plot(steps, plasticity, color="#1f77b4", linewidth=1.5, label="plasticity")
        ax.set_xlabel("step")
        ax.set_ylabel("value (0..1)")
        ax.set_ylim(-0.05, 1.1)
        ax.set_title(f"Resource Consumption — {organism_id}")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize=9)
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        return out_path

    def plot_mind_diff(
        self, out_path: Path, figsize: tuple[float, float] = (8, 5)
    ) -> Path:
        """Plot the per-action preference changes from the mind diff."""
        plt = self._setup_matplotlib()
        d = self.art.mind_diff
        if not d:
            raise ValueError("no mind_diff found")
        vc = d.get("value_changes", {})
        per_action = vc.get("per_action", {})
        if not per_action:
            # Fall back to developmental state diff
            dc = d.get("developmental_changes", {})
            labels = ["maturity", "plasticity", "stability", "energy", "pred_acc", "self_model", "exploration"]
            values = [
                dc.get("maturity_delta", 0.0),
                dc.get("plasticity_delta", 0.0),
                dc.get("stability_delta", 0.0),
                dc.get("energy_delta", 0.0),
                dc.get("prediction_accuracy_delta", 0.0),
                dc.get("self_model_stability_delta", 0.0),
                dc.get("exploration_level_delta", 0.0),
            ]
            fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
            ax.barh(labels, values, color=["#1f77b4" if v >= 0 else "#d62728" for v in values])
            ax.set_xlabel("delta (B - A)")
            ax.set_title("Mind Diff — Developmental State Deltas")
            ax.axvline(0.0, color="black", linewidth=0.5)
            ax.grid(True, alpha=0.3, axis="x")
        else:
            actions = sorted(per_action.keys())
            values = [per_action[a] for a in actions]
            fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
            colors = ["#1f77b4" if v >= 0 else "#d62728" for v in values]
            ax.barh(actions, values, color=colors)
            ax.set_xlabel("preference delta (B - A)")
            ax.set_title("Mind Diff — Action Preference Deltas")
            ax.axvline(0.0, color="black", linewidth=0.5)
            ax.grid(True, alpha=0.3, axis="x")
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        return out_path

    def plot_divergence(
        self, out_path: Path, figsize: tuple[float, float] = (10, 5)
    ) -> Path:
        """Plot per-step state distance from the divergence data."""
        plt = self._setup_matplotlib()
        d = self.art.divergence
        if not d:
            raise ValueError("no divergence found")
        per_step = d.get("per_step_state_distance", [])
        if not per_step:
            raise ValueError("no per_step_state_distance in divergence data")
        steps = list(range(1, len(per_step) + 1))

        fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
        ax.plot(steps, per_step, color="#d62728", linewidth=1.5, label="state distance")
        ax.set_xlabel("step")
        ax.set_ylabel("L1 state distance (A vs B)")
        ax.set_title("Computational Developmental Divergence — per-step state distance")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize=9)
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        return out_path

    def plot_divergence_comparison(
        self, out_path: Path, figsize: tuple[float, float] = (10, 6)
    ) -> Path:
        """Plot cumulative reward comparison between organism A and B."""
        plt = self._setup_matplotlib()
        fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
        for org_id, color in [("organism_a", "#1f77b4"), ("organism_b", "#d62728")]:
            tel = self.art.telemetry.get(org_id, [])
            if not tel:
                continue
            steps = [r.step for r in tel]
            cum = [r.cum_reward for r in tel]
            ax.plot(steps, cum, color=color, linewidth=1.5, label=org_id)
        ax.set_xlabel("step")
        ax.set_ylabel("cumulative reward")
        ax.set_title("Cumulative Reward: Organism A vs Organism B (Same Genome, Different World)")
        ax.axhline(0.0, color="black", linewidth=0.5, alpha=0.5)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize=9)
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        return out_path

    # ------------------------------------------------------------------
    # Render all
    # ------------------------------------------------------------------

    def render_all(self, out_dir: Path) -> dict[str, Path]:
        """Generate all text reports + PNG plots into out_dir.

        Returns a dict mapping artifact name -> file path.
        """
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        results: dict[str, Path] = {}

        # Text reports
        text_reports = {
            "timeline_a.txt": self.render_timeline_replay("organism_a", end=50),
            "timeline_b.txt": self.render_timeline_replay("organism_b", end=50),
            "mind_diff.txt": self.render_mind_diff(),
            "causal_trace.txt": self.render_causal_trace(max_events=30),
            "env_events_a.txt": self.render_environment_events("organism_a"),
            "env_events_b.txt": self.render_environment_events("organism_b"),
            "checkpoints.txt": self.render_checkpoints(),
            "manifests.txt": self.render_manifests(),
            "divergence.txt": self.render_divergence(),
        }
        for name, content in text_reports.items():
            p = out_dir / name
            p.write_text(content, encoding="utf-8")
            results[name] = p

        # PNG plots
        for org_id in self.art.organism_ids:
            suffix = org_id[-1]  # "a" or "b"
            results[f"dev_trajectory_{suffix}.png"] = self.plot_developmental_trajectory(
                org_id, out_dir / f"dev_trajectory_{suffix}.png"
            )
            results[f"prediction_error_{suffix}.png"] = self.plot_prediction_error(
                org_id, out_dir / f"prediction_error_{suffix}.png"
            )
            results[f"memory_changes_{suffix}.png"] = self.plot_memory_changes(
                org_id, out_dir / f"memory_changes_{suffix}.png"
            )
            results[f"state_transitions_{suffix}.png"] = self.plot_state_transitions(
                org_id, out_dir / f"state_transitions_{suffix}.png"
            )
            results[f"resource_consumption_{suffix}.png"] = self.plot_resource_consumption(
                org_id, out_dir / f"resource_consumption_{suffix}.png"
            )

        results["mind_diff.png"] = self.plot_mind_diff(out_dir / "mind_diff.png")
        results["divergence.png"] = self.plot_divergence(out_dir / "divergence.png")
        results["divergence_comparison.png"] = self.plot_divergence_comparison(
            out_dir / "divergence_comparison.png"
        )

        return results


def _short(v: Any, n: int = 20) -> str:
    s = str(v)
    return s if len(s) <= n else s[: n - 1] + "…"
