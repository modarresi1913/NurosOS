"""
Integration tests for the nuros-dev developmental substrate.

These tests exercise the Python bindings of the Rust crate `nuros._dev`.
They verify that:
  - The Same Genome / Different World experiment runs end-to-end.
  - Identical (genome, env_seed, steps) produces identical trajectories.
  - Different env_seeds produce divergent trajectories.
  - MindDiff correctly identifies changes between two organism states.
  - The flagship experiment produces all expected output artifacts.

Run with:
    pytest nuros/tests/test_developmental_substrate.py -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Make the nuros package importable when running from the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _dev_available() -> bool:
    try:
        from nuros import _dev  # noqa: F401
        return True
    except ImportError:
        return False


# Skip the entire module if the Rust extension is not available.
pytestmark = pytest.mark.skipif(
    not _dev_available(),
    reason="nuros._dev Rust extension is not installed. Run `maturin develop` in nuros-dev/.",
)

from nuros import _dev  # type: ignore[attr-defined]  # noqa: E402


# ============================================================================
# Genome tests
# ============================================================================

class TestGenome:
    def test_genome_hash_is_deterministic(self):
        g1 = _dev.DevelopmentalGenome("alpha")
        g2 = _dev.DevelopmentalGenome("alpha")
        assert g1.hash == g2.hash

    def test_genome_hash_changes_with_name(self):
        g1 = _dev.DevelopmentalGenome("alpha")
        g2 = _dev.DevelopmentalGenome("beta")
        assert g1.hash != g2.hash

    def test_genome_hash_is_64_hex_chars(self):
        g = _dev.DevelopmentalGenome("test")
        assert len(g.hash) == 64
        assert all(c in "0123456789abcdef" for c in g.hash)

    def test_genome_short_hash_is_12_chars(self):
        g = _dev.DevelopmentalGenome("test")
        assert len(g.short_hash) == 12
        assert g.hash.startswith(g.short_hash)

    def test_genome_json_roundtrip_preserves_hash(self):
        g1 = _dev.DevelopmentalGenome("roundtrip")
        g1_json = g1.to_json()
        g2 = _dev.DevelopmentalGenome.from_json(g1_json)
        assert g1.hash == g2.hash


# ============================================================================
# Environment tests
# ============================================================================

class TestEnvironments:
    def test_resource_world_determinism(self):
        env_a = _dev.ResourceWorld(6, 6, 42)
        env_b = _dev.ResourceWorld(6, 6, 42)
        env_a.reset()
        env_b.reset()
        assert env_a.hash == env_b.hash
        # Apply the same action sequence and verify equality.
        for action in ["move_right", "consume", "move_up", "idle"]:
            obs_a = env_a.step(action)
            obs_b = env_b.step(action)
            assert obs_a[0] == obs_b[0]  # observation payload
            assert abs(obs_a[1] - obs_b[1]) < 1e-9  # reward

    def test_resource_world_different_seeds_produce_different_hashes(self):
        env_a = _dev.ResourceWorld(6, 6, 1)
        env_b = _dev.ResourceWorld(6, 6, 999)
        env_a.reset()
        env_b.reset()
        assert env_a.hash != env_b.hash

    def test_resource_world_render_shows_agent(self):
        env = _dev.ResourceWorld(4, 4, 1)
        env.reset()
        rendered = env.render()
        assert "A" in rendered

    def test_changing_world_resource_shifts(self):
        env = _dev.ChangingWorld(10, 5, 99)
        env.reset()
        initial_resource_pos = None
        obs = env.observe()
        if isinstance(obs, dict):
            initial_resource_pos = obs.get("resource_pos")
        for _ in range(5):
            env.step("idle")
        # After 5 steps, a shift should have occurred.
        obs_final = env.observe()
        # Either resource_pos changed or shifts counter incremented.
        if isinstance(obs_final, dict):
            shifts = obs_final.get("shifts", 0)
            assert shifts >= 1


# ============================================================================
# Organism tests
# ============================================================================

class TestOrganism:
    def test_organism_initialization(self):
        g = _dev.DevelopmentalGenome("test")
        org = _dev.MinimumOrganism(g)
        assert org.step == 0
        org.initialize()
        org.begin_development()
        assert org.developmental_stage == "NASCENT"

    def test_organism_tick_updates_state(self):
        g = _dev.DevelopmentalGenome("test")
        org = _dev.MinimumOrganism(g)
        org.initialize()
        org.begin_development()
        env = _dev.ResourceWorld(6, 6, 1)
        env.reset()
        tick = org.tick_resource(env)
        assert tick["step"] == 1
        assert "action" in tick
        assert "reward" in tick
        assert "developmental_stage" in tick
        assert "state_hash" in tick
        assert org.step == 1

    def test_same_genome_same_env_produces_identical_trajectory(self):
        g = _dev.DevelopmentalGenome("repro")
        org_a = _dev.MinimumOrganism(g)
        org_b = _dev.MinimumOrganism(g)
        org_a.initialize(); org_a.begin_development()
        org_b.initialize(); org_b.begin_development()
        env_a = _dev.ResourceWorld(6, 6, 7)
        env_b = _dev.ResourceWorld(6, 6, 7)
        env_a.reset(); env_b.reset()
        for _ in range(20):
            ta = org_a.tick_resource(env_a)
            tb = org_b.tick_resource(env_b)
            assert ta["action"] == tb["action"]
            assert abs(ta["reward"] - tb["reward"]) < 1e-9
            assert ta["state_hash"] == tb["state_hash"]

    def test_different_envs_produce_different_trajectories(self):
        g = _dev.DevelopmentalGenome("diverge")
        org_a = _dev.MinimumOrganism(g)
        org_b = _dev.MinimumOrganism(g)
        org_a.initialize(); org_a.begin_development()
        org_b.initialize(); org_b.begin_development()
        env_a = _dev.ResourceWorld(6, 6, 1)
        env_b = _dev.ResourceWorld(6, 6, 987654321)
        env_a.reset(); env_b.reset()
        actions_a = []
        actions_b = []
        for _ in range(60):
            actions_a.append(org_a.tick_resource(env_a)["action"])
            actions_b.append(org_b.tick_resource(env_b)["action"])
        # The two trajectories should NOT be identical.
        assert actions_a != actions_b or org_a.state_hash != org_b.state_hash

    def test_organism_snapshot_restore_roundtrip(self):
        g = _dev.DevelopmentalGenome("snap")
        org = _dev.MinimumOrganism(g)
        org.initialize(); org.begin_development()
        env = _dev.ResourceWorld(6, 6, 1)
        env.reset()
        for _ in range(5):
            org.tick_resource(env)
        snap = org.snapshot()
        hash_before = org.state_hash
        for _ in range(5):
            org.tick_resource(env)
        assert org.state_hash != hash_before
        org.restore(snap)
        assert org.state_hash == hash_before


# ============================================================================
# MindDiff tests
# ============================================================================

class TestMindDiff:
    def test_mind_diff_of_identical_states_is_identical(self):
        g = _dev.DevelopmentalGenome("diff")
        org = _dev.MinimumOrganism(g)
        org.initialize(); org.begin_development()
        snap = org.snapshot()
        diff_json = _dev.mind_diff(snap, snap)
        diff = json.loads(diff_json)
        assert diff["identical"] is True

    def test_mind_diff_of_different_states_is_not_identical(self):
        g = _dev.DevelopmentalGenome("diff")
        org = _dev.MinimumOrganism(g)
        org.initialize(); org.begin_development()
        snap_a = org.snapshot()
        env = _dev.ResourceWorld(6, 6, 1)
        env.reset()
        for _ in range(5):
            org.tick_resource(env)
        snap_b = org.snapshot()
        diff_json = _dev.mind_diff(snap_a, snap_b)
        diff = json.loads(diff_json)
        assert diff["identical"] is False
        assert diff["step_delta"] == 5


# ============================================================================
# Flagship experiment integration test
# ============================================================================

class TestFlagshipExperiment:
    def test_flagship_runner_returns_divergence(self):
        result_json = _dev.run_same_genome_different_world(
            steps=60,
            env_a_seed=1,
            env_b_seed=987654321,
            width=6,
            height=6,
            genome_name="integration_test",
        )
        result = json.loads(result_json)
        assert "genome_hash" in result
        assert "trajectory_a" in result
        assert "trajectory_b" in result
        assert "divergence" in result
        assert "manifest_a" in result
        assert "manifest_b" in result
        assert "summary" in result
        # Genome hashes must match (it's the same genome).
        assert result["trajectory_a"]["genome_hash"] == result["trajectory_b"]["genome_hash"]
        # Environment hashes must differ (different seeds).
        assert result["trajectory_a"]["environment_hash"] != result["trajectory_b"]["environment_hash"]
        # Divergence must report some non-zero distance in at least one dimension.
        d = result["divergence"]
        assert (
            d["mean_state_distance"] > 0
            or d["action_distance"] > 0
            or d["reward_distance"] > 0
            or d["prediction_error_distance"] > 0
        )

    def test_flagship_experiment_writes_artifacts(self, tmp_path):
        # Import the experiment runner.
        sys.path.insert(0, str(_REPO_ROOT / "experiments"))
        try:
            from same_genome_different_world import run_experiment
        finally:
            sys.path.pop(0)

        result = run_experiment(
            steps=60,
            env_a_seed=1,
            env_b_seed=987654321,
            width=6,
            height=6,
            genome_name="integration_test",
            out_dir=tmp_path,
        )

        # Verify all expected artifacts exist.
        expected_files = [
            "genome.json",
            "trajectory_a.jsonl",
            "trajectory_b.jsonl",
            "telemetry_a.csv",
            "telemetry_b.csv",
            "checkpoint_a.json",
            "checkpoint_b.json",
            "divergence.json",
            "mind_diff.json",
            "manifest_a.json",
            "manifest_b.json",
            "report.txt",
            "summary.json",
        ]
        for fname in expected_files:
            assert (tmp_path / fname).exists(), f"missing artifact: {fname}"

        # Verify summary is valid JSON with expected fields.
        summary = json.loads((tmp_path / "summary.json").read_text())
        assert summary["experiment"] == "same_genome_different_world"
        assert summary["n_steps"] == 60
        assert "divergence" in summary
        assert "interpretation" in summary

        # Verify report contains the expected conclusion header.
        report = (tmp_path / "report.txt").read_text()
        assert "Same Genome / Different World" in report
        # The phrase "Computational Developmental Divergence" may be wrapped
        # across lines in the report; check for it with whitespace normalized.
        normalized = " ".join(report.split())
        assert "Computational Developmental Divergence" in normalized
