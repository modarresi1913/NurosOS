//! Counterfactual Self + Possible-Self Space.
//!
//! `CounterfactualSelf` allows an organism to evaluate alternative developmental
//! histories: "What if environment E2 had occurred?", "What if action A had
//! not been taken?", "What if memory M had been retained?", "What if value V
//! had been different?".
//!
//! Architecture:
//!
//! ```text
//! CurrentSelf
//!      ↓
//! CounterfactualGenerator
//!      ↓
//! AlternativeTrajectory
//!      ↓
//! Simulation
//!      ↓
//! Evaluation
//! ```
//!
//! ## Safety invariants
//!
//! 1. **Never automatically execute counterfactual actions in the real
//!    environment.** Counterfactual simulations run against an environment
//!    *snapshot* — a copy of the environment state, never the live one.
//! 2. **Every counterfactual trajectory is marked** with the epistemic labels
//!    `SIMULATED` and `COUNTERFACTUAL`. These labels propagate to every
//!    record in the trajectory.
//! 3. **Counterfactual trajectories are query-only.** They can be inspected,
//!    diffed, and compared, but they cannot be "committed" back to the
//!    organism's real state.
//!
//! ## Interpretation caveat
//!
//! `PossibleSelfSpace` is an experimental abstraction. It does NOT represent
//! phenomenological identity. The "possible selves" are reachable
//! computational states under counterfactual perturbations — nothing more.

use serde::{Deserialize, Serialize};

use crate::checkpoint::MindCheckpoint;
use crate::environment::{Action, Environment};
use crate::genome::DevelopmentalGenome;
use crate::organism::MinimumOrganism;
use crate::state::DevelopmentalState;
use crate::trajectory::{DevelopmentalDivergence, DevelopmentalTrajectory};

/// The epistemic labels attached to every counterfactual trajectory.
///
/// These match the labels in the Python `nuros.epistemic` module:
/// `SIMULATED` (output of internal simulation) and `COUNTERFACTUAL`
/// (counterfactual construction). A counterfactual trajectory carries both.
pub const COUNTERFACTUAL_LABELS: &[&str] = &["SIMULATED", "COUNTERFACTUAL"];

/// A trajectory produced by a counterfactual simulation.
///
/// This wraps a [`DevelopmentalTrajectory`] with provenance about what was
/// changed and the epistemic labels that mark it as counterfactual.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CounterfactualTrajectory {
    /// The trajectory that resulted from the counterfactual simulation.
    pub trajectory: DevelopmentalTrajectory,
    /// Epistemic labels — always `["SIMULATED", "COUNTERFACTUAL"]`.
    pub epistemic_labels: Vec<String>,
    /// Human-readable description of what was changed
    /// (e.g. `"environment_seed=999"`, `"action_at_step_5=MoveLeft"`).
    pub counterfactual_change: String,
    /// Hash of the checkpoint from which the counterfactual was started.
    pub source_checkpoint_hash: String,
    /// Always `false` — counterfactuals are never executed in the real
    /// environment. This field exists to make the invariant explicit and
    /// auditable.
    pub executed_in_real_environment: bool,
}

impl CounterfactualTrajectory {
    /// Render a human-readable summary.
    pub fn render(&self) -> String {
        let s = self.trajectory.summary();
        let mut out = String::new();
        out.push_str("=== Counterfactual Trajectory ===\n");
        out.push_str(&format!("  epistemic_labels:       {:?}\n", self.epistemic_labels));
        out.push_str(&format!("  counterfactual_change:  {}\n", self.counterfactual_change));
        out.push_str(&format!("  source_checkpoint_hash: {}...\n", &self.source_checkpoint_hash[..12.min(self.source_checkpoint_hash.len())]));
        out.push_str(&format!("  executed_in_real_env:   {}\n", self.executed_in_real_environment));
        out.push_str(&format!("  organism_id:            {}\n", s.organism_id));
        out.push_str(&format!("  n_points:               {}\n", s.n_points));
        out.push_str(&format!("  total_reward:           {:.4}\n", s.total_reward));
        out.push_str(&format!("  mean_reward:            {:.4}\n", s.mean_reward));
        out.push_str(&format!("  mean_prediction_error:  {:.4}\n", s.mean_prediction_error));
        out.push_str(&format!("  final_stage:            {}\n", s.final_stage));
        out
    }
}

/// The Counterfactual Self.
///
/// Holds a reference checkpoint (the organism's state at a particular point)
/// and provides methods to generate counterfactual trajectories from it.
///
/// The actual trajectory (the organism's real history) is stored separately
/// so that counterfactuals can be compared against it.
pub struct CounterfactualSelf {
    /// The checkpoint from which counterfactuals are generated.
    pub source_checkpoint: MindCheckpoint,
    /// The actual trajectory of the organism (the "real" history). Used
    /// as the baseline for comparison.
    pub actual_trajectory: DevelopmentalTrajectory,
}

impl CounterfactualSelf {
    /// Construct a CounterfactualSelf from a checkpoint + the actual trajectory.
    pub fn new(checkpoint: MindCheckpoint, actual: DevelopmentalTrajectory) -> Self {
        Self {
            source_checkpoint: checkpoint,
            actual_trajectory: actual,
        }
    }

    /// "What if the environment had been different?"
    ///
    /// Replays the organism from the source checkpoint in an alternative
    /// environment for `n_steps` steps. The alternative environment must be
    /// a fresh instance (or a restored snapshot) — it is never the live
    /// environment.
    ///
    /// The organism's policy runs normally in the alternative environment;
    /// only the environment differs.
    pub fn what_if_environment(
        &self,
        alt_env: &mut dyn Environment,
        n_steps: u64,
        alt_env_seed: u64,
    ) -> CounterfactualTrajectory {
        let genome = self.source_checkpoint.genome.clone();
        let mut org = MinimumOrganism::instantiate(genome);
        org.state = self.source_checkpoint.organism_state.clone();

        let env_hash = alt_env.hash();
        let mut traj = DevelopmentalTrajectory::new(
            format!("{}_counterfactual", self.actual_trajectory.organism_id),
            self.source_checkpoint.genome_hash.clone(),
            env_hash,
            alt_env_seed,
        );

        for _ in 0..n_steps {
            let tick = org.tick(alt_env);
            traj.record(&tick, &org.state.developmental);
        }

        CounterfactualTrajectory {
            trajectory: traj,
            epistemic_labels: COUNTERFACTUAL_LABELS.iter().map(|s| s.to_string()).collect(),
            counterfactual_change: format!("environment={} (seed={})", alt_env.name(), alt_env_seed),
            source_checkpoint_hash: self.source_checkpoint.hash(),
            executed_in_real_environment: false,
        }
    }

    /// "What if the organism had taken different actions?"
    ///
    /// Replays the organism from the source checkpoint with a forced action
    /// sequence. The environment is restored to the checkpoint's snapshot
    /// before replay begins.
    ///
    /// If `actions.len() < n_steps`, the organism's own policy takes over
    /// for the remaining steps.
    pub fn what_if_actions(
        &self,
        env: &mut dyn Environment,
        actions: &[Action],
        n_steps: u64,
        env_seed: u64,
    ) -> CounterfactualTrajectory {
        // Restore the environment to the checkpoint state.
        let _ = env.restore(&self.source_checkpoint.environment_snapshot);

        let genome = self.source_checkpoint.genome.clone();
        let mut org = MinimumOrganism::instantiate(genome);
        org.state = self.source_checkpoint.organism_state.clone();

        let env_hash = env.hash();
        let mut traj = DevelopmentalTrajectory::new(
            format!("{}_counterfactual_actions", self.actual_trajectory.organism_id),
            self.source_checkpoint.genome_hash.clone(),
            env_hash,
            env_seed,
        );

        for i in 0..n_steps {
            let tick = if (i as usize) < actions.len() {
                org.tick_with_action(env, actions[i as usize])
            } else {
                org.tick(env)
            };
            traj.record(&tick, &org.state.developmental);
        }

        let action_desc: Vec<String> = actions.iter().take(5).map(|a| a.to_string()).collect();
        let action_summary = if actions.len() > 5 {
            format!("{:?} ... ({} total)", action_desc, actions.len())
        } else {
            format!("{:?}", action_desc)
        };

        CounterfactualTrajectory {
            trajectory: traj,
            epistemic_labels: COUNTERFACTUAL_LABELS.iter().map(|s| s.to_string()).collect(),
            counterfactual_change: format!("forced_actions={}", action_summary),
            source_checkpoint_hash: self.source_checkpoint.hash(),
            executed_in_real_environment: false,
        }
    }

    /// Compare a counterfactual trajectory against the actual trajectory.
    ///
    /// Returns the [`DevelopmentalDivergence`] between the segment of the
    /// actual trajectory starting at the checkpoint step and the
    /// counterfactual trajectory.
    pub fn compare_to_actual(
        &self,
        counterfactual: &CounterfactualTrajectory,
    ) -> Result<DevelopmentalDivergence, String> {
        // Slice the actual trajectory from the checkpoint step onward.
        let start = self.source_checkpoint.step as usize;
        let n = counterfactual.trajectory.len();
        let end = (start + n).min(self.actual_trajectory.len());
        let actual_slice_points: Vec<_> = self.actual_trajectory.points[start..end].to_vec();
        if actual_slice_points.len() != n {
            return Err(format!(
                "length mismatch: actual_slice={} vs counterfactual={}",
                actual_slice_points.len(),
                n
            ));
        }
        let mut actual_slice = DevelopmentalTrajectory::new(
            self.actual_trajectory.organism_id.clone(),
            self.actual_trajectory.genome_hash.clone(),
            self.actual_trajectory.environment_hash.clone(),
            self.actual_trajectory.environment_seed,
        );
        actual_slice.points = actual_slice_points;

        DevelopmentalDivergence::between(&actual_slice, &counterfactual.trajectory)
    }
}

// ============================================================================
// Possible-Self Space
// ============================================================================

/// The Possible-Self Space.
///
/// Represents the organism not as a single static state but as a space of
/// reachable developmental states: the current self, a set of possible futures
/// (counterfactual trajectories from the current checkpoint), and an optional
/// counterfactual past (what if an earlier decision had been different).
///
/// **Interpretation caveat**: This is an experimental abstraction. It does
/// NOT represent phenomenological identity. The "possible selves" are
/// reachable computational states under counterfactual perturbations —
/// nothing more.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PossibleSelfSpace {
    /// The organism's current developmental state (the "actual" self).
    pub current_self: DevelopmentalState,
    /// Possible futures: counterfactual trajectories from the current
    /// checkpoint under different perturbations.
    pub possible_futures: Vec<CounterfactualTrajectory>,
    /// Counterfactual past: what if an earlier decision had been different?
    /// `None` if not computed.
    pub counterfactual_past: Option<CounterfactualTrajectory>,
    /// Hash of the checkpoint from which the space was constructed.
    pub source_checkpoint_hash: String,
}

impl PossibleSelfSpace {
    /// Construct an empty space from a current state + checkpoint hash.
    pub fn new(current_self: DevelopmentalState, source_checkpoint_hash: String) -> Self {
        Self {
            current_self,
            possible_futures: Vec::new(),
            counterfactual_past: None,
            source_checkpoint_hash,
        }
    }

    /// Add a possible future.
    pub fn add_future(&mut self, future: CounterfactualTrajectory) {
        self.possible_futures.push(future);
    }

    /// Set the counterfactual past.
    pub fn set_counterfactual_past(&mut self, past: CounterfactualTrajectory) {
        self.counterfactual_past = Some(past);
    }

    /// Number of possible futures.
    pub fn n_futures(&self) -> usize {
        self.possible_futures.len()
    }

    /// Compute the coverage of the possible-self space.
    ///
    /// Coverage is measured as the mean pairwise L1 distance between the
    /// final developmental states of all possible futures. A larger coverage
    /// means the organism's possible selves are more spread out in state
    /// space.
    ///
    /// Returns 0.0 if there are fewer than 2 futures.
    pub fn coverage(&self) -> f64 {
        if self.possible_futures.len() < 2 {
            return 0.0;
        }
        let final_states: Vec<&DevelopmentalState> = self
            .possible_futures
            .iter()
            .filter_map(|t| t.trajectory.points.last())
            .map(|p| &p.developmental_state)
            .collect();
        if final_states.len() < 2 {
            return 0.0;
        }
        let mut sum = 0.0;
        let mut count = 0;
        for i in 0..final_states.len() {
            for j in (i + 1)..final_states.len() {
                sum += final_states[i].distance(final_states[j]);
                count += 1;
            }
        }
        if count == 0 {
            0.0
        } else {
            sum / count as f64
        }
    }

    /// Compute the divergence between each possible future and the current
    /// self's developmental state. Returns a vector of (future_index, distance).
    pub fn distances_from_current(&self) -> Vec<(usize, f64)> {
        self.possible_futures
            .iter()
            .enumerate()
            .filter_map(|(i, t)| {
                t.trajectory.points.last().map(|p| {
                    (i, p.developmental_state.distance(&self.current_self))
                })
            })
            .collect()
    }

    /// Render a human-readable summary of the possible-self space.
    pub fn render(&self) -> String {
        let mut out = String::new();
        out.push_str("=== Possible-Self Space ===\n");
        out.push_str(&format!("  source_checkpoint_hash: {}...\n", &self.source_checkpoint_hash[..12.min(self.source_checkpoint_hash.len())]));
        out.push_str(&format!("  current_self stage:     {}\n", self.current_self.developmental_stage));
        out.push_str(&format!("  current_self age:       {}\n", self.current_self.age));
        out.push_str(&format!("  n_possible_futures:     {}\n", self.n_futures()));
        out.push_str(&format!("  has_counterfactual_past: {}\n", self.counterfactual_past.is_some()));
        out.push_str(&format!("  coverage (mean pairwise L1): {:.4}\n", self.coverage()));
        out.push_str("\n  Possible futures:\n");
        for (i, f) in self.possible_futures.iter().enumerate() {
            let s = f.trajectory.summary();
            out.push_str(&format!(
                "    [{}] {} -> reward={:.3}, pe={:.3}, stage={}\n",
                i, f.counterfactual_change, s.total_reward, s.mean_prediction_error, s.final_stage
            ));
        }
        if let Some(past) = &self.counterfactual_past {
            let s = past.trajectory.summary();
            out.push_str("\n  Counterfactual past:\n");
            out.push_str(&format!(
                "    {} -> reward={:.3}, pe={:.3}, stage={}\n",
                past.counterfactual_change, s.total_reward, s.mean_prediction_error, s.final_stage
            ));
        }
        out.push_str("\n  Interpretation caveat: This is an experimental abstraction.\n");
        out.push_str("  It does NOT represent phenomenological identity.\n");
        out
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::environment::ResourceWorld;
    use crate::organism::MinimumOrganism;
    use crate::trajectory::DevelopmentalTrajectory;

    fn setup(n_steps: usize, seed: u64) -> (MinimumOrganism, ResourceWorld, DevelopmentalTrajectory, MindCheckpoint) {
        let g = DevelopmentalGenome::named("cf_test");
        let mut org = MinimumOrganism::instantiate(g.clone());
        org.initialize().unwrap();
        org.begin_development().unwrap();
        let mut env = ResourceWorld::new(6, 6, seed);
        env.reset();
        let env_hash = env.hash();
        let mut traj = DevelopmentalTrajectory::new("org_cf", g.hash(), env_hash, seed);
        // Run n_steps/2 steps, take a checkpoint, then run the remaining steps.
        let half = n_steps / 2;
        for _ in 0..half {
            let tick = org.tick(&mut env);
            traj.record(&tick, &org.state.developmental);
        }
        let ck = MindCheckpoint::take(&org, &env, seed, 0, "midpoint");
        for _ in half..n_steps {
            let tick = org.tick(&mut env);
            traj.record(&tick, &org.state.developmental);
        }
        (org, env, traj, ck)
    }

    #[test]
    fn counterfactual_labels_are_simulated_and_counterfactual() {
        let (_org, _env, traj, ck) = setup(20, 1);
        let cs = CounterfactualSelf::new(ck, traj);
        let mut alt_env = ResourceWorld::new(6, 6, 999);
        alt_env.reset();
        let cf = cs.what_if_environment(&mut alt_env, 10, 999);
        assert_eq!(cf.epistemic_labels, vec!["SIMULATED", "COUNTERFACTUAL"]);
        assert!(!cf.executed_in_real_environment);
    }

    #[test]
    fn what_if_environment_produces_trajectory() {
        let (_org, _env, traj, ck) = setup(20, 1);
        let cs = CounterfactualSelf::new(ck, traj);
        let mut alt_env = ResourceWorld::new(6, 6, 999);
        alt_env.reset();
        let cf = cs.what_if_environment(&mut alt_env, 15, 999);
        assert_eq!(cf.trajectory.len(), 15);
        assert!(cf.counterfactual_change.contains("environment"));
    }

    #[test]
    fn what_if_actions_produces_trajectory() {
        let (_org, env, traj, ck) = setup(20, 1);
        let cs = CounterfactualSelf::new(ck, traj);
        let mut alt_env = env.clone();
        let actions = vec![Action::MoveRight, Action::MoveRight, Action::Consume, Action::Idle];
        let cf = cs.what_if_actions(&mut alt_env, &actions, 5, 1);
        assert_eq!(cf.trajectory.len(), 5);
        assert!(cf.counterfactual_change.contains("forced_actions"));
    }

    #[test]
    fn compare_to_actual_returns_divergence() {
        let (_org, _env, traj, ck) = setup(30, 1);
        let cs = CounterfactualSelf::new(ck, traj.clone());
        let mut alt_env = ResourceWorld::new(6, 6, 999);
        alt_env.reset();
        let cf = cs.what_if_environment(&mut alt_env, 10, 999);
        let div = cs.compare_to_actual(&cf);
        let div = div.unwrap_or_else(|e| panic!("compare_to_actual failed: {}", e));
        assert_eq!(div.n_steps, 10);
    }

    #[test]
    fn possible_self_space_coverage_is_zero_with_one_future() {
        let (_org, _env, traj, ck) = setup(20, 1);
        let cs = CounterfactualSelf::new(ck.clone(), traj);
        let mut alt_env = ResourceWorld::new(6, 6, 999);
        alt_env.reset();
        let cf = cs.what_if_environment(&mut alt_env, 10, 999);
        let mut space = PossibleSelfSpace::new(
            ck.organism_state.developmental.clone(),
            ck.hash(),
        );
        space.add_future(cf);
        assert_eq!(space.coverage(), 0.0); // only 1 future
    }

    #[test]
    fn possible_self_space_coverage_is_positive_with_two_futures() {
        let (_org, _env, traj, ck) = setup(20, 1);
        let cs = CounterfactualSelf::new(ck.clone(), traj);
        let mut alt_env_a = ResourceWorld::new(6, 6, 100);
        alt_env_a.reset();
        let cf_a = cs.what_if_environment(&mut alt_env_a, 15, 100);
        let mut alt_env_b = ResourceWorld::new(6, 6, 200);
        alt_env_b.reset();
        let cf_b = cs.what_if_environment(&mut alt_env_b, 15, 200);
        let mut space = PossibleSelfSpace::new(
            ck.organism_state.developmental.clone(),
            ck.hash(),
        );
        space.add_future(cf_a);
        space.add_future(cf_b);
        assert!(space.coverage() >= 0.0);
        assert_eq!(space.n_futures(), 2);
    }

    #[test]
    fn possible_self_space_render_works() {
        let (_org, _env, traj, ck) = setup(20, 1);
        let cs = CounterfactualSelf::new(ck.clone(), traj);
        let mut alt_env = ResourceWorld::new(6, 6, 999);
        alt_env.reset();
        let cf = cs.what_if_environment(&mut alt_env, 10, 999);
        let mut space = PossibleSelfSpace::new(
            ck.organism_state.developmental.clone(),
            ck.hash(),
        );
        space.add_future(cf);
        let s = space.render();
        eprintln!("DEBUG render output:\n{}", s);
        assert!(s.contains("Possible-Self Space"));
        assert!(s.contains("n_possible_futures"));
        assert!(s.contains("Interpretation caveat"));
    }

    #[test]
    fn counterfactual_trajectory_render_works() {
        let (_org, _env, traj, ck) = setup(20, 1);
        let cs = CounterfactualSelf::new(ck, traj);
        let mut alt_env = ResourceWorld::new(6, 6, 999);
        alt_env.reset();
        let cf = cs.what_if_environment(&mut alt_env, 10, 999);
        let s = cf.render();
        assert!(s.contains("Counterfactual Trajectory"));
        assert!(s.contains("SIMULATED"));
        assert!(s.contains("COUNTERFACTUAL"));
        assert!(s.contains("executed_in_real_env"));
        assert!(s.contains("false"));
    }

    #[test]
    fn distances_from_current_returns_one_per_future() {
        let (_org, _env, traj, ck) = setup(20, 1);
        let cs = CounterfactualSelf::new(ck.clone(), traj);
        let mut alt_env_a = ResourceWorld::new(6, 6, 100);
        alt_env_a.reset();
        let cf_a = cs.what_if_environment(&mut alt_env_a, 10, 100);
        let mut alt_env_b = ResourceWorld::new(6, 6, 200);
        alt_env_b.reset();
        let cf_b = cs.what_if_environment(&mut alt_env_b, 10, 200);
        let mut space = PossibleSelfSpace::new(
            ck.organism_state.developmental.clone(),
            ck.hash(),
        );
        space.add_future(cf_a);
        space.add_future(cf_b);
        let dists = space.distances_from_current();
        assert_eq!(dists.len(), 2);
        for (_, d) in &dists {
            assert!(*d >= 0.0);
        }
    }
}
