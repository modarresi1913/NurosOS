//! Artificial Ontogenesis + Developmental Trajectory.
//!
//! The developmental trajectory is the central research object of NurosOS.
//! It is the ordered sequence of states, actions, and events that an
//! organism produces over its lifetime. Comparing trajectories of two
//! organisms instantiated from the same genome but placed in different
//! environments is the flagship experimental method.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

use crate::environment::Action;
use crate::organism::TickRecord;
use crate::state::{DevelopmentalStage, DevelopmentalState};

/// A single point in a developmental trajectory: the full state of the
/// organism at one step, plus the action it took and the resulting outcome.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrajectoryPoint {
    /// Step index.
    pub step: u64,
    /// Developmental state at this step.
    pub developmental_state: DevelopmentalState,
    /// Action taken at this step.
    pub action: Action,
    /// Reward received.
    pub reward: f64,
    /// Prediction error at this step.
    pub prediction_error: f64,
    /// Predicted reward (for provenance).
    pub predicted_reward: f64,
    /// Memory size at this step.
    pub memory_size: u64,
    /// State hash at this step (for fast equality checks).
    pub state_hash: String,
    /// Free-form environment observation payload.
    pub observation: serde_json::Value,
}

impl TrajectoryPoint {
    /// Construct a trajectory point from a tick record + the developmental state.
    pub fn from_tick(tick: &TickRecord, dev: &DevelopmentalState) -> Self {
        Self {
            step: tick.step,
            developmental_state: dev.clone(),
            action: tick.action,
            reward: tick.reward,
            prediction_error: tick.prediction_error,
            predicted_reward: tick.predicted_reward,
            memory_size: tick.memory_size,
            state_hash: tick.state_hash.clone(),
            observation: tick.observation.clone(),
        }
    }
}

/// A complete developmental trajectory.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DevelopmentalTrajectory {
    /// ID of the organism this trajectory belongs to.
    pub organism_id: String,
    /// Hash of the genome this trajectory started from.
    pub genome_hash: String,
    /// Hash of the environment this trajectory unfolded in.
    pub environment_hash: String,
    /// RNG seed used by the environment (for reproducibility).
    pub environment_seed: u64,
    /// Ordered list of trajectory points.
    pub points: Vec<TrajectoryPoint>,
    /// Developmental events recorded during the trajectory (e.g. stage transitions).
    pub events: Vec<DevelopmentalEvent>,
}

impl DevelopmentalTrajectory {
    /// Construct a new empty trajectory with provenance metadata.
    pub fn new(
        organism_id: impl Into<String>,
        genome_hash: impl Into<String>,
        environment_hash: impl Into<String>,
        environment_seed: u64,
    ) -> Self {
        Self {
            organism_id: organism_id.into(),
            genome_hash: genome_hash.into(),
            environment_hash: environment_hash.into(),
            environment_seed,
            points: Vec::new(),
            events: Vec::new(),
        }
    }

    /// Append a tick record + developmental state as a new trajectory point.
    pub fn record(&mut self, tick: &TickRecord, dev: &DevelopmentalState) {
        self.points.push(TrajectoryPoint::from_tick(tick, dev));
    }

    /// Record a developmental event (e.g. stage transition).
    pub fn record_event(&mut self, event: DevelopmentalEvent) {
        self.events.push(event);
    }

    /// Number of recorded points.
    pub fn len(&self) -> usize {
        self.points.len()
    }

    /// True if no points have been recorded.
    pub fn is_empty(&self) -> bool {
        self.points.is_empty()
    }

    /// Compute a set of summary statistics over the trajectory.
    pub fn summary(&self) -> TrajectorySummary {
        let n = self.points.len() as f64;
        let total_reward: f64 = self.points.iter().map(|p| p.reward).sum();
        let mean_reward = if n > 0.0 { total_reward / n } else { 0.0 };
        let mean_pe: f64 = if n > 0.0 {
            self.points.iter().map(|p| p.prediction_error).sum::<f64>() / n
        } else { 0.0 };
        let final_state = self.points.last().map(|p| p.developmental_state.clone());
        let final_stage = final_state
            .as_ref()
            .map(|s| s.developmental_stage)
            .unwrap_or(DevelopmentalStage::Embryonic);
        TrajectorySummary {
            organism_id: self.organism_id.clone(),
            genome_hash: self.genome_hash.clone(),
            environment_hash: self.environment_hash.clone(),
            n_points: self.points.len() as u64,
            n_events: self.events.len() as u64,
            total_reward,
            mean_reward,
            mean_prediction_error: mean_pe,
            final_stage,
            final_state,
        }
    }
}

/// Summary statistics for a trajectory. Used in experiment reports.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrajectorySummary {
    pub organism_id: String,
    pub genome_hash: String,
    pub environment_hash: String,
    pub n_points: u64,
    pub n_events: u64,
    pub total_reward: f64,
    pub mean_reward: f64,
    pub mean_prediction_error: f64,
    pub final_stage: DevelopmentalStage,
    pub final_state: Option<DevelopmentalState>,
}

/// A developmental event: stage transition, capability emergence, etc.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DevelopmentalEvent {
    /// Step at which the event occurred.
    pub step: u64,
    /// Event type (free-form; e.g. "stage_transition", "capability_emergence").
    pub kind: String,
    /// Free-form description.
    pub description: String,
    /// Optional before/after values.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub before: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub after: Option<serde_json::Value>,
}

// ============================================================================
// Developmental Divergence Metrics
// ============================================================================

/// Quantitative comparison of two developmental trajectories.
///
/// This computes several distance metrics between two trajectories of equal
/// length. The interpretation is deliberately limited: a small distance
/// does NOT mean the two organisms are cognitively equivalent — only that
/// their observable trajectories are close along the measured dimensions.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DevelopmentalDivergence {
    /// ID of the first organism.
    pub organism_a: String,
    /// ID of the second organism.
    pub organism_b: String,
    /// Genome hash shared by both organisms (must match for the
    /// "Same Genome / Different World" experiment).
    pub genome_hash: String,
    /// Hash of environment A.
    pub environment_a_hash: String,
    /// Hash of environment B.
    pub environment_b_hash: String,
    /// Number of steps compared.
    pub n_steps: u64,
    /// L1 distance between the cumulative reward curves.
    pub reward_distance: f64,
    /// L1 distance between the prediction-error curves.
    pub prediction_error_distance: f64,
    /// L1 distance between the action sequences (Hamming-style).
    pub action_distance: f64,
    /// Mean L1 distance between developmental state vectors per step.
    pub mean_state_distance: f64,
    /// Final L1 distance between the developmental states.
    pub final_state_distance: f64,
    /// True if the two trajectories ended in different developmental stages.
    pub stage_divergence: bool,
    /// Per-step state distances (for plotting).
    pub per_step_state_distance: Vec<f64>,
}

impl DevelopmentalDivergence {
    /// Compute divergence between two trajectories.
    ///
    /// Returns `Err` if the trajectories have different genome hashes or
    /// different lengths.
    pub fn between(a: &DevelopmentalTrajectory, b: &DevelopmentalTrajectory) -> Result<Self, String> {
        if a.genome_hash != b.genome_hash {
            return Err(format!(
                "genome hashes do not match: {} vs {}",
                a.genome_hash, b.genome_hash
            ));
        }
        if a.points.len() != b.points.len() {
            return Err(format!(
                "trajectory lengths differ: {} vs {}",
                a.points.len(),
                b.points.len()
            ));
        }

        let n = a.points.len();
        let mut reward_distance = 0.0;
        let mut prediction_error_distance = 0.0;
        let mut action_distance = 0.0;
        let mut sum_state_distance = 0.0;
        let mut per_step_state_distance = Vec::with_capacity(n);

        for (pa, pb) in a.points.iter().zip(b.points.iter()) {
            reward_distance += (pa.reward - pb.reward).abs();
            prediction_error_distance += (pa.prediction_error - pb.prediction_error).abs();
            if pa.action != pb.action {
                action_distance += 1.0;
            }
            let d = pa.developmental_state.distance(&pb.developmental_state);
            sum_state_distance += d;
            per_step_state_distance.push(d);
        }

        let mean_state_distance = if n > 0 { sum_state_distance / n as f64 } else { 0.0 };
        let final_state_distance = if n > 0 {
            a.points[n - 1].developmental_state.distance(&b.points[n - 1].developmental_state)
        } else {
            0.0
        };
        let stage_divergence = if n > 0 {
            a.points[n - 1].developmental_state.developmental_stage
                != b.points[n - 1].developmental_state.developmental_stage
        } else {
            false
        };

        Ok(Self {
            organism_a: a.organism_id.clone(),
            organism_b: b.organism_id.clone(),
            genome_hash: a.genome_hash.clone(),
            environment_a_hash: a.environment_hash.clone(),
            environment_b_hash: b.environment_hash.clone(),
            n_steps: n as u64,
            reward_distance,
            prediction_error_distance,
            action_distance,
            mean_state_distance,
            final_state_distance,
            stage_divergence,
            per_step_state_distance,
        })
    }

    /// Render a human-readable summary of the divergence.
    pub fn render(&self) -> String {
        let mut s = String::new();
        s.push_str("=== Developmental Divergence ===\n");
        s.push_str(&format!("  Organism A:       {}\n", self.organism_a));
        s.push_str(&format!("  Organism B:       {}\n", self.organism_b));
        s.push_str(&format!("  Genome hash:      {}...\n", &self.genome_hash[..12]));
        s.push_str(&format!("  Environment A:    {}...\n", &self.environment_a_hash[..12]));
        s.push_str(&format!("  Environment B:    {}...\n", &self.environment_b_hash[..12]));
        s.push_str(&format!("  Steps compared:   {}\n", self.n_steps));
        s.push_str(&format!("  Reward distance:  {:.4}\n", self.reward_distance));
        s.push_str(&format!("  Pred-error dist:  {:.4}\n", self.prediction_error_distance));
        s.push_str(&format!("  Action distance:  {:.0} / {} ({:.1}%)\n",
            self.action_distance, self.n_steps,
            100.0 * self.action_distance / self.n_steps.max(1) as f64));
        s.push_str(&format!("  Mean state dist:  {:.4}\n", self.mean_state_distance));
        s.push_str(&format!("  Final state dist: {:.4}\n", self.final_state_distance));
        s.push_str(&format!("  Stage divergence: {}\n",
            if self.stage_divergence { "YES" } else { "no" }));
        s
    }

    /// Export the per-step state distance series as a CSV string.
    pub fn per_step_csv(&self) -> String {
        let mut s = String::from("step,state_distance\n");
        for (i, d) in self.per_step_state_distance.iter().enumerate() {
            s.push_str(&format!("{},{}\n", i + 1, d));
        }
        s
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::environment::{ResourceWorld, Environment};
    use crate::genome::DevelopmentalGenome;
    use crate::organism::MinimumOrganism;

    fn run_trajectory(genome: &DevelopmentalGenome, env_seed: u64, n: usize) -> DevelopmentalTrajectory {
        let mut org = MinimumOrganism::instantiate(genome.clone());
        org.initialize().unwrap();
        org.begin_development().unwrap();
        let mut env = ResourceWorld::new(6, 6, env_seed);
        env.reset();
        let env_hash = env.hash();
        let mut traj = DevelopmentalTrajectory::new(
            format!("org_{}", env_seed),
            genome.hash(),
            env_hash,
            env_seed,
        );
        for _ in 0..n {
            let tick = org.tick(&mut env);
            traj.record(&tick, &org.state.developmental);
        }
        traj
    }

    #[test]
    fn trajectories_have_correct_length() {
        let g = DevelopmentalGenome::named("len");
        let t = run_trajectory(&g, 1, 25);
        assert_eq!(t.len(), 25);
    }

    #[test]
    fn same_genome_same_env_produces_equal_trajectories() {
        let g = DevelopmentalGenome::named("repro");
        let t1 = run_trajectory(&g, 42, 20);
        let t2 = run_trajectory(&g, 42, 20);
        for (a, b) in t1.points.iter().zip(t2.points.iter()) {
            assert_eq!(a.action, b.action);
            assert!((a.reward - b.reward).abs() < 1e-12);
            assert_eq!(a.state_hash, b.state_hash);
        }
    }

    #[test]
    fn divergence_rejects_different_genomes() {
        let g1 = DevelopmentalGenome::named("g1");
        let g2 = DevelopmentalGenome::named("g2");
        let t1 = run_trajectory(&g1, 1, 5);
        let t2 = run_trajectory(&g2, 1, 5);
        let err = DevelopmentalDivergence::between(&t1, &t2).unwrap_err();
        assert!(err.contains("genome hashes"));
    }

    #[test]
    fn divergence_rejects_different_lengths() {
        let g = DevelopmentalGenome::named("len");
        let t1 = run_trajectory(&g, 1, 5);
        let t2 = run_trajectory(&g, 1, 10);
        let err = DevelopmentalDivergence::between(&t1, &t2).unwrap_err();
        assert!(err.contains("lengths"));
    }

    #[test]
    fn divergence_between_same_world_is_zero() {
        let g = DevelopmentalGenome::named("zero");
        let t = run_trajectory(&g, 7, 15);
        let d = DevelopmentalDivergence::between(&t, &t).unwrap();
        assert_eq!(d.reward_distance, 0.0);
        assert_eq!(d.action_distance, 0.0);
        assert_eq!(d.mean_state_distance, 0.0);
        assert!(!d.stage_divergence);
    }

    #[test]
    fn divergence_between_different_worlds_is_positive() {
        let g = DevelopmentalGenome::named("diverge");
        // Use very different seeds and enough steps for the agent to encounter
        // the (differently-placed) resources. Resource placement is a function
        // of the seed, so two different seeds put resources at different cells;
        // over enough steps the agent will accumulate different reward histories.
        let t1 = run_trajectory(&g, 1, 60);
        let t2 = run_trajectory(&g, 987654321, 60);
        let d = DevelopmentalDivergence::between(&t1, &t2).unwrap();
        // Different environments should produce SOME divergence — either in
        // the developmental state vector, in actions, or in rewards.
        assert!(
            d.mean_state_distance > 0.0
                || d.action_distance > 0.0
                || d.reward_distance > 0.0
                || d.prediction_error_distance > 0.0,
            "expected divergence but got: state={:?} action={:?} reward={:?} pe={:?}",
            d.mean_state_distance, d.action_distance, d.reward_distance, d.prediction_error_distance,
        );
        let report = d.render();
        assert!(report.contains("Developmental Divergence"));
    }

    #[test]
    fn per_step_csv_has_correct_length() {
        let g = DevelopmentalGenome::named("csv");
        let t1 = run_trajectory(&g, 1, 10);
        let t2 = run_trajectory(&g, 2, 10);
        let d = DevelopmentalDivergence::between(&t1, &t2).unwrap();
        let csv = d.per_step_csv();
        let lines: Vec<&str> = csv.lines().collect();
        assert_eq!(lines.len(), 11); // header + 10
    }
}
