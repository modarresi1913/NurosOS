//! Mind Checkpointing + Replay.
//!
//! A checkpoint captures enough state to resume or analyze an organism at
//! a particular step. Combined with the genome + environment seed, the
//! checkpoint should let an external researcher re-run the experiment and
//! compare trajectories.
//!
//! Replay determinism is best-effort. We classify replay fidelity into
//! three categories:
//!
//! - [`ReplayFidelity::Exact`] — the replayed trajectory is byte-for-byte
//!   identical to the original.
//! - [`ReplayFidelity::Approximate`] — the replayed trajectory matches the
//!   original within a documented tolerance.
//! - [`ReplayFidelity::NonReproducible`] — the replayed trajectory diverged
//!   beyond the tolerance, or the runtime cannot guarantee determinism.

use serde::{Deserialize, Serialize};

use crate::environment::Environment;
use crate::genome::DevelopmentalGenome;
use crate::lifecycle::LifecycleMachine;
use crate::organism::{MinimumOrganism, OrganismState, TickRecord};
use crate::state::DevelopmentalState;
use crate::trajectory::DevelopmentalTrajectory;

/// A complete checkpoint of an organism + its environment + provenance.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MindCheckpoint {
    /// ID of the checkpoint (a UUID-like string).
    pub checkpoint_id: String,
    /// ID of the organism this checkpoint belongs to.
    pub organism_id: String,
    /// Hash of the genome the organism was instantiated from.
    pub genome_hash: String,
    /// The full genome (so the checkpoint is self-contained).
    pub genome: DevelopmentalGenome,
    /// Hash of the environment at checkpoint time.
    pub environment_hash: String,
    /// Snapshot of the environment at checkpoint time (self-contained).
    pub environment_snapshot: serde_json::Value,
    /// RNG seed used by the environment.
    pub environment_seed: u64,
    /// Random seed used to instantiate the organism (if any).
    pub random_seed: u64,
    /// Full organism state at checkpoint time.
    pub organism_state: OrganismState,
    /// Step at which the checkpoint was taken.
    pub step: u64,
    /// Hash of the organism state at checkpoint time.
    pub state_hash: String,
    /// Runtime version that produced this checkpoint.
    pub runtime_version: String,
    /// Optional label for human identification.
    pub label: String,
}

impl MindCheckpoint {
    /// Take a checkpoint from an organism + environment.
    pub fn take(
        organism: &MinimumOrganism,
        env: &dyn Environment,
        environment_seed: u64,
        random_seed: u64,
        label: impl Into<String>,
    ) -> Self {
        let state_hash = organism.state.short_hash();
        let checkpoint_id = format!(
            "ck-{}-{}",
            organism.state.step,
            &state_hash[..8]
        );
        Self {
            checkpoint_id,
            organism_id: format!("org-{}", &organism.genome.short_hash()),
            genome_hash: organism.genome.hash(),
            genome: organism.genome.clone(),
            environment_hash: env.hash(),
            environment_snapshot: env.snapshot(),
            environment_seed,
            random_seed,
            organism_state: organism.state.clone(),
            step: organism.state.step,
            state_hash,
            runtime_version: env!("CARGO_PKG_VERSION").to_string(),
            label: label.into(),
        }
    }

    /// Compute the canonical hash of the entire checkpoint (for integrity
    /// verification after serialization round-trip).
    pub fn hash(&self) -> String {
        crate::hash::hash(self)
    }

    /// Serialize to canonical JSON.
    pub fn to_json(&self) -> serde_json::Result<String> {
        crate::hash::canonical_json(self)
    }

    /// Deserialize from JSON.
    pub fn from_json(s: &str) -> serde_json::Result<Self> {
        serde_json::from_str(s)
    }
}

/// Fidelity classification for a replay attempt.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ReplayFidelity {
    /// Replayed trajectory matches the original byte-for-byte.
    Exact,
    /// Replayed trajectory matches the original within tolerance.
    Approximate,
    /// Replayed trajectory diverged beyond tolerance.
    NonReproducible,
}

impl std::fmt::Display for ReplayFidelity {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ReplayFidelity::Exact => write!(f, "EXACT"),
            ReplayFidelity::Approximate => write!(f, "APPROXIMATE"),
            ReplayFidelity::NonReproducible => write!(f, "NON_REPRODUCIBLE"),
        }
    }
}

/// The result of a replay attempt.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReplayResult {
    /// The fidelity classification.
    pub fidelity: ReplayFidelity,
    /// The number of steps replayed.
    pub steps_replayed: u64,
    /// Number of steps that matched exactly (same action + same reward).
    pub exact_matches: u64,
    /// Number of steps that matched within tolerance (same action, reward
    /// within tolerance).
    pub approximate_matches: u64,
    /// Number of steps that diverged.
    pub divergences: u64,
    /// Mean absolute reward difference across all replayed steps.
    pub mean_reward_diff: f64,
    /// Final state hash of the replayed organism.
    pub replayed_state_hash: String,
    /// Final state hash of the original organism.
    pub original_state_hash: String,
}

impl ReplayResult {
    /// Render a human-readable summary.
    pub fn render(&self) -> String {
        let mut s = String::new();
        s.push_str("=== Replay Result ===\n");
        s.push_str(&format!("  Fidelity:          {}\n", self.fidelity));
        s.push_str(&format!("  Steps replayed:    {}\n", self.steps_replayed));
        s.push_str(&format!("  Exact matches:     {}\n", self.exact_matches));
        s.push_str(&format!("  Approx matches:    {}\n", self.approximate_matches));
        s.push_str(&format!("  Divergences:       {}\n", self.divergences));
        s.push_str(&format!("  Mean reward diff:  {:.6}\n", self.mean_reward_diff));
        s.push_str(&format!("  Original hash:     {}...\n", &self.original_state_hash[..12]));
        s.push_str(&format!("  Replayed hash:     {}...\n", &self.replayed_state_hash[..12]));
        s
    }
}

/// Replay an organism from a checkpoint for `n_steps` steps, comparing each
/// step against the original trajectory.
///
/// The `tolerance` parameter controls the boundary between `Approximate`
/// and `NonReproducible`: if any single reward difference exceeds the
/// tolerance, the fidelity is downgraded.
pub fn replay_from_checkpoint(
    checkpoint: &MindCheckpoint,
    env: &mut dyn Environment,
    n_steps: u64,
    original_trajectory: &DevelopmentalTrajectory,
    tolerance: f64,
) -> ReplayResult {
    // Restore environment to checkpoint state.
    let _ = env.restore(&checkpoint.environment_snapshot);

    // Reconstruct organism from checkpoint.
    let mut org = MinimumOrganism::instantiate(checkpoint.genome.clone());
    org.state = checkpoint.organism_state.clone();

    let mut exact_matches = 0u64;
    let mut approximate_matches = 0u64;
    let mut divergences = 0u64;
    let mut total_reward_diff = 0.0f64;
    let mut n_compared = 0u64;

    for i in 0..n_steps {
        let tick = org.tick(env);
        let orig = original_trajectory.points.get(checkpoint.step as usize + i as usize);
        match orig {
            Some(p) => {
                let reward_diff = (tick.reward - p.reward).abs();
                total_reward_diff += reward_diff;
                n_compared += 1;
                if tick.action == p.action && reward_diff < 1e-12 {
                    exact_matches += 1;
                } else if tick.action == p.action && reward_diff <= tolerance {
                    approximate_matches += 1;
                } else {
                    divergences += 1;
                }
            }
            None => break,
        }
    }

    let mean_reward_diff = if n_compared > 0 { total_reward_diff / n_compared as f64 } else { 0.0 };
    let fidelity = if divergences == 0 && mean_reward_diff < 1e-12 {
        ReplayFidelity::Exact
    } else if divergences == 0 && mean_reward_diff <= tolerance {
        ReplayFidelity::Approximate
    } else {
        ReplayFidelity::NonReproducible
    };

    ReplayResult {
        fidelity,
        steps_replayed: n_compared,
        exact_matches,
        approximate_matches,
        divergences,
        mean_reward_diff,
        replayed_state_hash: org.state.short_hash(),
        original_state_hash: original_trajectory
            .points
            .last()
            .map(|p| p.state_hash.clone())
            .unwrap_or_default(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::environment::ResourceWorld;
    use crate::genome::DevelopmentalGenome;
    use crate::organism::MinimumOrganism;
    use crate::trajectory::DevelopmentalTrajectory;

    fn setup(seed: u64, n: usize) -> (MinimumOrganism, ResourceWorld, DevelopmentalTrajectory) {
        let g = DevelopmentalGenome::named("replay_test");
        let mut org = MinimumOrganism::instantiate(g.clone());
        org.initialize().unwrap();
        org.begin_development().unwrap();
        let mut env = ResourceWorld::new(6, 6, seed);
        env.reset();
        let env_hash = env.hash();
        let mut traj = DevelopmentalTrajectory::new("org", g.hash(), env_hash, seed);
        for _ in 0..n {
            let tick = org.tick(&mut env);
            traj.record(&tick, &org.state.developmental);
        }
        (org, env, traj)
    }

    #[test]
    fn checkpoint_round_trips_through_json() {
        let g = DevelopmentalGenome::named("snap");
        let mut org = MinimumOrganism::instantiate(g.clone());
        org.initialize().unwrap();
        org.begin_development().unwrap();
        let mut env = ResourceWorld::new(6, 6, 1);
        env.reset();
        for _ in 0..5 {
            org.tick(&mut env);
        }
        let ck = MindCheckpoint::take(&org, &env, 1, 42, "test");
        let json = ck.to_json().unwrap();
        let ck2 = MindCheckpoint::from_json(&json).unwrap();
        assert_eq!(ck.hash(), ck2.hash());
        assert_eq!(ck.checkpoint_id, ck2.checkpoint_id);
    }

    #[test]
    fn replay_from_checkpoint_is_exact_for_deterministic_engine() {
        let (_org, _env, traj) = setup(7, 20);

        // Take a fresh checkpoint at step 5 of a fresh run.
        let g = DevelopmentalGenome::named("replay_test");
        let mut org = MinimumOrganism::instantiate(g.clone());
        org.initialize().unwrap();
        org.begin_development().unwrap();
        let mut env = ResourceWorld::new(6, 6, 7);
        env.reset();
        for _ in 0..5 {
            org.tick(&mut env);
        }
        let ck = MindCheckpoint::take(&org, &env, 7, 0, "midpoint");

        // Replay 15 more steps from the checkpoint.
        let result = replay_from_checkpoint(&ck, &mut env, 15, &traj, 1e-6);
        assert_eq!(result.fidelity, ReplayFidelity::Exact);
        assert_eq!(result.divergences, 0);
    }

    #[test]
    fn replay_result_renders() {
        let (_org, _env, traj) = setup(7, 10);
        let g = DevelopmentalGenome::named("replay_test");
        let mut org = MinimumOrganism::instantiate(g.clone());
        org.initialize().unwrap();
        org.begin_development().unwrap();
        let mut env = ResourceWorld::new(6, 6, 7);
        env.reset();
        let ck = MindCheckpoint::take(&org, &env, 7, 0, "start");
        let result = replay_from_checkpoint(&ck, &mut env, 5, &traj, 1e-6);
        let s = result.render();
        assert!(s.contains("Replay Result"));
        assert!(s.contains("Fidelity"));
    }
}
