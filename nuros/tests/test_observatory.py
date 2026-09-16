"""
Tests for the Mind Observatory (nuros.observatory).

These tests verify that the Observatory can load artifacts from a Same Genome /
Different World experiment, produce text renderers, and produce PNG plots.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _dev_available() -> bool:
    try:
        from nuros import _dev  # noqa: F401
        return True
    except ImportError:
        return False


# We need the Rust extension to generate fresh artifacts for the tests.
pytestmark = pytest.mark.skipif(
    not _dev_available(),
    reason="nuros._dev Rust extension is not installed",
)

from nuros.observatory import Observatory, load_artifacts  # noqa: E402


@pytest.fixture(scope="module")
def experiment_dir(tmp_path_factory):
    """Run a small flagship experiment and return its output directory."""
    from nuros import _dev
    # Use the Rust-side flagship runner to generate artifacts.
    result_json = _dev.run_same_genome_different_world(
        steps=60,
        env_a_seed=1,
        env_b_seed=987654321,
        width=6,
        height=6,
        genome_name="observatory_test",
    )
    result = json.loads(result_json)

    out_dir = tmp_path_factory.mktemp("experiment")
    # Write the artifacts that the Observatory expects to read.
    # The Rust runner returns the data inline; we write it to disk so the
    # Observatory's file-based loaders can read it.
    (out_dir / "summary.json").write_text(json.dumps({
        "experiment": "same_genome_different_world",
        "genome_name": "observatory_test",
        "genome_hash": result["genome_hash"],
        "genome_short_hash": result["genome_short_hash"],
        "n_steps": 60,
        "env_a_seed": 1,
        "env_b_seed": 987654321,
        "env_a_hash": result["trajectory_a"]["environment_hash"],
        "env_b_hash": result["trajectory_b"]["environment_hash"],
        "final_stage_a": result["trajectory_a"]["points"][-1]["developmental_state"]["developmental_stage"],
        "final_stage_b": result["trajectory_b"]["points"][-1]["developmental_state"]["developmental_stage"],
        "total_reward_a": sum(p["reward"] for p in result["trajectory_a"]["points"]),
        "total_reward_b": sum(p["reward"] for p in result["trajectory_b"]["points"]),
        "total_prediction_error_a": sum(p["prediction_error"] for p in result["trajectory_a"]["points"]),
        "total_prediction_error_b": sum(p["prediction_error"] for p in result["trajectory_b"]["points"]),
        "divergence": {
            "mean_state_distance": result["divergence"]["mean_state_distance"],
            "final_state_distance": result["divergence"]["final_state_distance"],
            "reward_distance": result["divergence"]["reward_distance"],
            "prediction_error_distance": result["divergence"]["prediction_error_distance"],
            "action_distance": result["divergence"]["action_distance"],
            "stage_divergence": result["divergence"]["stage_divergence"],
        },
        "mind_diff_identical": False,
        "mind_diff_developmental_state_l1": result["mind_diff"]["developmental_changes"]["state_l1_distance"] if "mind_diff" in result else 0.0,
        "interpretation": "test",
    }, indent=2))

    # Write trajectory JSONL
    for org_id, traj_key, suffix in [("organism_a", "trajectory_a", "a"), ("organism_b", "trajectory_b", "b")]:
        points = result[traj_key]["points"]
        with (out_dir / f"trajectory_{suffix}.jsonl").open("w") as f:
            for p in points:
                f.write(json.dumps(p) + "\n")

    # Write telemetry CSV
    for org_id, traj_key, suffix in [("organism_a", "trajectory_a", "a"), ("organism_b", "trajectory_b", "b")]:
        points = result[traj_key]["points"]
        cum_r = 0.0
        cum_pe = 0.0
        with (out_dir / f"telemetry_{suffix}.csv").open("w") as f:
            f.write("step,action,reward,prediction_error,developmental_stage,energy,plasticity,memory_size,cum_reward,cum_pe,state_hash\n")
            for p in points:
                cum_r += p["reward"]
                cum_pe += p["prediction_error"]
                f.write(f"{p['step']},{p['action']},{p['reward']},{p['prediction_error']},"
                        f"{p['developmental_state']['developmental_stage']},"
                        f"{p['developmental_state']['energy_state']},"
                        f"{p['developmental_state']['plasticity']},"
                        f"{p['memory_size']},{cum_r},{cum_pe},{p['state_hash']}\n")

    # Write divergence + mind_diff + manifests
    (out_dir / "divergence.json").write_text(json.dumps(result["divergence"], indent=2))
    # The Rust flagship runner does not return a full mind_diff (which requires
    # the complete OrganismState including memory, self_model, action_preferences).
    # We synthesize a minimal mind_diff from the final developmental states so
    # the Observatory's loaders can exercise the mind_diff renderers.
    final_a = result["trajectory_a"]["points"][-1]["developmental_state"]
    final_b = result["trajectory_b"]["points"][-1]["developmental_state"]
    mind_diff = {
        "state_a_hash": result["trajectory_a"]["points"][-1]["state_hash"],
        "state_b_hash": result["trajectory_b"]["points"][-1]["state_hash"],
        "step_delta": 0,
        "identical": result["trajectory_a"]["points"][-1]["state_hash"] == result["trajectory_b"]["points"][-1]["state_hash"],
        "memory_changes": {"added": 0, "removed": 0, "importance_changed": 0, "size_a": 0, "size_b": 0},
        "self_model_changes": {
            "expected_reward_delta": 0.0,
            "expected_prediction_error_delta": 0.0,
            "update_count_delta": 0,
        },
        "value_changes": {"per_action": {}, "total_l1": 0.0},
        "capability_changes": {"per_capability": {}, "gained": [], "lost": []},
        "prediction_changes": {
            "accuracy_delta": final_b["prediction_accuracy"] - final_a["prediction_accuracy"],
            "total_error_delta": 0.0,
        },
        "behavioral_changes": {
            "last_action_a": result["trajectory_a"]["points"][-1]["action"],
            "last_action_b": result["trajectory_b"]["points"][-1]["action"],
            "last_action_changed": result["trajectory_a"]["points"][-1]["action"] != result["trajectory_b"]["points"][-1]["action"],
        },
        "developmental_changes": {
            "age_delta": int(final_b["age"]) - int(final_a["age"]),
            "maturity_delta": final_b["maturity"] - final_a["maturity"],
            "plasticity_delta": final_b["plasticity"] - final_a["plasticity"],
            "stability_delta": final_b["stability"] - final_a["stability"],
            "energy_delta": final_b["energy_state"] - final_a["energy_state"],
            "prediction_accuracy_delta": final_b["prediction_accuracy"] - final_a["prediction_accuracy"],
            "self_model_stability_delta": final_b["self_model_stability"] - final_a["self_model_stability"],
            "exploration_level_delta": final_b["exploration_level"] - final_a["exploration_level"],
            "state_l1_distance": result["divergence"]["final_state_distance"],
            "stage_changed": final_a["developmental_stage"] != final_b["developmental_stage"],
            "stage_a": final_a["developmental_stage"],
            "stage_b": final_b["developmental_stage"],
        },
    }
    (out_dir / "mind_diff.json").write_text(json.dumps(mind_diff, indent=2))
    (out_dir / "manifest_a.json").write_text(json.dumps(result["manifest_a"], indent=2))
    (out_dir / "manifest_b.json").write_text(json.dumps(result["manifest_b"], indent=2))

    # Write minimal checkpoints + genome
    (out_dir / "checkpoint_a.json").write_text(json.dumps({
        "checkpoint_id": "ck-a",
        "organism_id": "organism_a",
        "genome_hash": result["genome_hash"],
        "environment_hash": result["trajectory_a"]["environment_hash"],
        "state_hash": result["trajectory_a"]["points"][-1]["state_hash"],
        "step": 60,
        "runtime_version": "0.1.0-alpha",
        "label": "final_a",
    }, indent=2))
    (out_dir / "checkpoint_b.json").write_text(json.dumps({
        "checkpoint_id": "ck-b",
        "organism_id": "organism_b",
        "genome_hash": result["genome_hash"],
        "environment_hash": result["trajectory_b"]["environment_hash"],
        "state_hash": result["trajectory_b"]["points"][-1]["state_hash"],
        "step": 60,
        "runtime_version": "0.1.0-alpha",
        "label": "final_b",
    }, indent=2))
    (out_dir / "genome.json").write_text(json.dumps({
        "name": "observatory_test",
        "hash": result["genome_hash"],
        "short_hash": result["genome_short_hash"],
    }, indent=2))

    return out_dir


# ============================================================================
# Loader tests
# ============================================================================

class TestLoaders:
    def test_load_artifacts_returns_all_components(self, experiment_dir):
        art = load_artifacts(experiment_dir)
        assert "organism_a" in art.trajectories
        assert "organism_b" in art.trajectories
        assert "organism_a" in art.telemetry
        assert "organism_b" in art.telemetry
        assert "organism_a" in art.checkpoints
        assert "organism_b" in art.checkpoints
        assert art.divergence  # non-empty
        assert art.summary  # non-empty

    def test_trajectory_points_have_expected_fields(self, experiment_dir):
        art = load_artifacts(experiment_dir)
        p = art.trajectories["organism_a"][0]
        assert hasattr(p, "step")
        assert hasattr(p, "action")
        assert hasattr(p, "reward")
        assert hasattr(p, "prediction_error")
        assert hasattr(p, "developmental_stage")
        assert hasattr(p, "energy")
        assert hasattr(p, "plasticity")
        assert hasattr(p, "memory_size")
        assert hasattr(p, "state_hash")

    def test_telemetry_rows_have_expected_fields(self, experiment_dir):
        art = load_artifacts(experiment_dir)
        r = art.telemetry["organism_a"][0]
        assert hasattr(r, "step")
        assert hasattr(r, "reward")
        assert hasattr(r, "cum_reward")
        assert hasattr(r, "cum_pe")

    def test_organism_ids_property(self, experiment_dir):
        art = load_artifacts(experiment_dir)
        assert art.organism_ids == ["organism_a", "organism_b"]


# ============================================================================
# Text renderer tests
# ============================================================================

class TestTextRenderers:
    def test_timeline_replay_renders_steps(self, experiment_dir):
        obs = Observatory.from_experiment_dir(experiment_dir)
        text = obs.render_timeline_replay("organism_a", end=10)
        assert "Timeline Replay" in text
        assert "organism_a" in text
        # Should contain at least one step line.
        assert "consume" in text or "move" in text or "idle" in text

    def test_timeline_replay_handles_unknown_organism(self, experiment_dir):
        obs = Observatory.from_experiment_dir(experiment_dir)
        text = obs.render_timeline_replay("unknown_org")
        assert "error" in text.lower()

    def test_mind_diff_renders(self, experiment_dir):
        obs = Observatory.from_experiment_dir(experiment_dir)
        text = obs.render_mind_diff()
        assert "Mind Diff" in text
        assert "identical" in text.lower()

    def test_causal_trace_renders(self, experiment_dir):
        obs = Observatory.from_experiment_dir(experiment_dir)
        text = obs.render_causal_trace(max_events=5)
        assert "Causal Trace" in text

    def test_env_events_renders(self, experiment_dir):
        obs = Observatory.from_experiment_dir(experiment_dir)
        text = obs.render_environment_events("organism_a", max_events=5)
        assert "Environment Events" in text
        assert "organism_a" in text

    def test_checkpoints_renders(self, experiment_dir):
        obs = Observatory.from_experiment_dir(experiment_dir)
        text = obs.render_checkpoints()
        assert "Checkpoints" in text
        assert "organism_a" in text
        assert "organism_b" in text

    def test_manifests_renders(self, experiment_dir):
        obs = Observatory.from_experiment_dir(experiment_dir)
        text = obs.render_manifests()
        assert "Reproducibility Manifests" in text

    def test_divergence_renders(self, experiment_dir):
        obs = Observatory.from_experiment_dir(experiment_dir)
        text = obs.render_divergence()
        assert "Developmental Divergence" in text
        assert "reward_distance" in text


# ============================================================================
# PNG plot tests
# ============================================================================

class TestPlots:
    def test_plot_developmental_trajectory(self, experiment_dir, tmp_path):
        obs = Observatory.from_experiment_dir(experiment_dir)
        out = obs.plot_developmental_trajectory("organism_a", tmp_path / "dev_traj.png")
        assert out.exists()
        assert out.stat().st_size > 1000  # non-trivial PNG

    def test_plot_prediction_error(self, experiment_dir, tmp_path):
        obs = Observatory.from_experiment_dir(experiment_dir)
        out = obs.plot_prediction_error("organism_a", tmp_path / "pred_err.png")
        assert out.exists()
        assert out.stat().st_size > 1000

    def test_plot_memory_changes(self, experiment_dir, tmp_path):
        obs = Observatory.from_experiment_dir(experiment_dir)
        out = obs.plot_memory_changes("organism_a", tmp_path / "mem.png")
        assert out.exists()
        assert out.stat().st_size > 1000

    def test_plot_state_transitions(self, experiment_dir, tmp_path):
        obs = Observatory.from_experiment_dir(experiment_dir)
        out = obs.plot_state_transitions("organism_a", tmp_path / "state.png")
        assert out.exists()
        assert out.stat().st_size > 1000

    def test_plot_resource_consumption(self, experiment_dir, tmp_path):
        obs = Observatory.from_experiment_dir(experiment_dir)
        out = obs.plot_resource_consumption("organism_a", tmp_path / "resource.png")
        assert out.exists()
        assert out.stat().st_size > 1000

    def test_plot_mind_diff(self, experiment_dir, tmp_path):
        obs = Observatory.from_experiment_dir(experiment_dir)
        out = obs.plot_mind_diff(tmp_path / "mind_diff.png")
        assert out.exists()
        assert out.stat().st_size > 1000

    def test_plot_divergence(self, experiment_dir, tmp_path):
        obs = Observatory.from_experiment_dir(experiment_dir)
        out = obs.plot_divergence(tmp_path / "divergence.png")
        assert out.exists()
        assert out.stat().st_size > 1000

    def test_plot_divergence_comparison(self, experiment_dir, tmp_path):
        obs = Observatory.from_experiment_dir(experiment_dir)
        out = obs.plot_divergence_comparison(tmp_path / "div_cmp.png")
        assert out.exists()
        assert out.stat().st_size > 1000


# ============================================================================
# render_all integration test
# ============================================================================

class TestRenderAll:
    def test_render_all_produces_expected_artifacts(self, experiment_dir, tmp_path):
        obs = Observatory.from_experiment_dir(experiment_dir)
        results = obs.render_all(tmp_path / "observatory_out")
        # Should produce 9 text files + 13 PNG files = 22 total.
        assert len(results) >= 20
        # All paths should exist.
        for name, path in results.items():
            assert Path(path).exists(), f"{name} not written"
        # Should have at least the text reports.
        text_names = [n for n in results if n.endswith(".txt")]
        png_names = [n for n in results if n.endswith(".png")]
        assert len(text_names) >= 8
        assert len(png_names) >= 10
