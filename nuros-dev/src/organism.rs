//! Minimum Artificial Organism — deterministic cognitive engine.
//!
//! This is the simplest organism that exercises the full developmental loop:
//!
//! ```text
//! GENOME → INITIAL STATE → SENSATION → PREDICTION → PREDICTION ERROR
//!        → MEMORY UPDATE → SELF-MODEL UPDATE → VALUE EVALUATION
//!        → DECISION → ACTION → ENVIRONMENTAL CONSEQUENCE
//!        → LEARNING → DEVELOPMENTAL UPDATE → NEW STATE → REPEAT
//! ```
//!
//! The engine is intentionally NOT an LLM, NOT a neural network, and NOT
//! stochastic. It is a small deterministic policy over a finite action
//! space, parameterized by a plasticity rule. This makes trajectories
//! fully reproducible and lets us isolate the effect of environment from
//! the effect of engine.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

use crate::environment::{Action, Environment, Observation};
use crate::genome::DevelopmentalGenome;
use crate::hash;
use crate::lifecycle::{LifecycleMachine, LifecycleState};
use crate::state::{DevelopmentalStage, DevelopmentalState};

/// A single memory record. Memories are simple key→value pairs with an
/// importance weight that controls decay.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryRecord {
    /// A free-form key (typically a stringified observation signature).
    pub key: String,
    /// The value associated with the key (typically the action taken and
    /// the reward observed).
    pub value: serde_json::Value,
    /// Importance in [0, 1]. Higher = decays slower.
    pub importance: f64,
    /// Step at which the memory was formed.
    pub step: u64,
    /// Number of times this memory has been accessed.
    pub access_count: u64,
}

/// A simple self-model: the organism's current beliefs about its own
/// capabilities and recent performance.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct SelfModel {
    /// Believed proficiency for each capability. Updated by learning.
    pub believed_capabilities: BTreeMap<String, f64>,
    /// Rolling mean of recent rewards.
    pub expected_reward: f64,
    /// Rolling mean of recent prediction errors.
    pub expected_prediction_error: f64,
    /// Number of self-model updates so far.
    pub update_count: u64,
}

/// The complete state of the minimum organism. This is what gets
/// checkpointed, diffed, and replayed.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrganismState {
    /// The organism's developmental state vector.
    pub developmental: DevelopmentalState,
    /// The lifecycle machine.
    pub lifecycle: LifecycleMachine,
    /// The memory store (a flat list of records).
    pub memory: Vec<MemoryRecord>,
    /// The self-model.
    pub self_model: SelfModel,
    /// The current action preferences (action → score in [-1, 1]).
    /// Higher score = more likely to be selected.
    pub action_preferences: BTreeMap<String, f64>,
    /// The most recent observation (for inspection).
    pub last_observation: serde_json::Value,
    /// The most recent action taken.
    pub last_action: Option<Action>,
    /// Total reward accumulated.
    pub total_reward: f64,
    /// Total prediction error accumulated.
    pub total_prediction_error: f64,
    /// Step counter.
    pub step: u64,
}

impl OrganismState {
    /// Construct the initial state from a genome.
    pub fn from_genome(genome: &DevelopmentalGenome) -> Self {
        let mut developmental = DevelopmentalState::default();
        developmental.exploration_level = genome.biases.exploration_bias;
        developmental.risk_sensitivity = genome.biases.risk_sensitivity;
        developmental.plasticity = 0.8; // high at birth
        developmental.energy_state = 1.0;
        developmental.capabilities = genome.initial_capabilities.capabilities.clone();

        let mut self_model = SelfModel::default();
        for (cap, prof) in &genome.initial_capabilities.capabilities {
            self_model.believed_capabilities.insert(cap.clone(), *prof);
        }

        // Seed action preferences with mild biases.
        let mut action_preferences = BTreeMap::new();
        for a in Action::all() {
            action_preferences.insert(a.to_string(), 0.0);
        }

        Self {
            developmental,
            lifecycle: LifecycleMachine::new(),
            memory: Vec::new(),
            self_model,
            action_preferences,
            last_observation: serde_json::Value::Null,
            last_action: None,
            total_reward: 0.0,
            total_prediction_error: 0.0,
            step: 0,
        }
    }

    /// Canonical hash of the complete organism state.
    pub fn hash(&self) -> String {
        hash::hash(self)
    }

    /// Short form of the hash.
    pub fn short_hash(&self) -> String {
        hash::short_hash(&self.hash())
    }
}

/// The minimum artificial organism.
///
/// It owns a genome and a mutable state. The state is the only thing that
/// changes during development — the genome is immutable.
pub struct MinimumOrganism {
    /// The genome this organism was instantiated from.
    pub genome: DevelopmentalGenome,
    /// The current state.
    pub state: OrganismState,
}

impl MinimumOrganism {
    /// Instantiate a new organism from a genome.
    pub fn instantiate(genome: DevelopmentalGenome) -> Self {
        let state = OrganismState::from_genome(&genome);
        Self { genome, state }
    }

    /// Initialize: transition from CREATED → INITIALIZED. Idempotent.
    pub fn initialize(&mut self) -> Result<(), String> {
        self.state.lifecycle.transition(
            LifecycleState::Initialized,
            self.state.step,
            "instantiated from genome",
        )
    }

    /// Begin development: transition from INITIALIZED → DEVELOPING.
    pub fn begin_development(&mut self) -> Result<(), String> {
        self.state.lifecycle.transition(
            LifecycleState::Developing,
            self.state.step,
            "birth",
        )?;
        self.state.developmental.developmental_stage = DevelopmentalStage::Nascent;
        Ok(())
    }

    /// Run one tick of the developmental loop against an environment.
    ///
    /// This is the central computational loop of the substrate. Each tick:
    ///   1. Observe the environment.
    ///   2. Predict the reward of each candidate action.
    ///   3. Select an action (greedy + exploration).
    ///   4. Execute the action; receive the new observation + reward.
    ///   5. Compute prediction error; update action preferences.
    ///   6. Update memory, self-model, developmental state.
    ///   7. Apply maturation schedule (stage transitions).
    pub fn tick(&mut self, env: &mut dyn Environment) -> TickRecord {
        self.state.step += 1;
        let step = self.state.step;

        // 1. Sensation
        let obs = env.observe();
        self.state.last_observation = obs.payload.clone();

        // 2. Prediction: predict the reward of each action under the current
        //    state. The "prediction" is just the action's current preference
        //    score; prediction error is |predicted - actual|.
        let candidate = self.select_action(&obs);

        // 3-4. Decision + Action
        let predicted_reward = self
            .state
            .action_preferences
            .get(&candidate.to_string())
            .copied()
            .unwrap_or(0.0);
        let new_obs = env.step(candidate);
        let actual_reward = new_obs.reward;

        // 5. Learning: update action preference based on prediction error.
        let prediction_error = (predicted_reward - actual_reward).abs();
        let lr = self.genome.plasticity_rules.learning_rate
            * self.state.developmental.plasticity;
        let entry = self
            .state
            .action_preferences
            .entry(candidate.to_string())
            .or_insert(0.0);
        *entry += lr * (actual_reward - predicted_reward);
        // Light forgetting toward 0.
        *entry *= 1.0 - self.genome.plasticity_rules.forgetting_rate;

        self.state.total_reward += actual_reward;
        self.state.total_prediction_error += prediction_error;
        self.state.last_action = Some(candidate);

        // 6a. Memory update: store the (observation signature, action, reward).
        let sig = observation_signature(&obs.payload);
        self.state.memory.push(MemoryRecord {
            key: sig.clone(),
            value: serde_json::json!({
                "action": candidate.to_string(),
                "reward": actual_reward,
                "prediction_error": prediction_error,
            }),
            importance: (actual_reward.abs() + 0.1).min(1.0),
            step,
            access_count: 0,
        });
        // Cap memory size to avoid unbounded growth; drop lowest-importance.
        if self.state.memory.len() > 200 {
            self.state.memory.sort_by(|a, b| b.importance.partial_cmp(&a.importance).unwrap_or(std::cmp::Ordering::Equal));
            self.state.memory.truncate(200);
        }

        // 6b. Self-model update: rolling averages.
        let alpha = 0.1;
        self.state.self_model.expected_reward =
            (1.0 - alpha) * self.state.self_model.expected_reward + alpha * actual_reward;
        self.state.self_model.expected_prediction_error =
            (1.0 - alpha) * self.state.self_model.expected_prediction_error + alpha * prediction_error;
        self.state.self_model.update_count += 1;
        // Update believed capability for "consume" based on reward.
        if candidate == Action::Consume {
            let cap = self.state.self_model.believed_capabilities
                .entry("consume".to_string())
                .or_insert(0.0);
            *cap = (1.0 - alpha) * *cap + alpha * (actual_reward > 0.0) as u64 as f64;
        }

        // 6c. Developmental state update.
        let dev = &mut self.state.developmental;
        dev.age = step;
        dev.cognitive_load = (dev.cognitive_load * 0.95 + 0.05).min(1.0);
        dev.memory_capacity = (self.state.memory.len() as f64 / 200.0).min(1.0);
        dev.prediction_accuracy =
            1.0 / (1.0 + self.state.self_model.expected_prediction_error);
        dev.self_model_stability =
            (dev.self_model_stability * 0.99 + 0.01 * (1.0 - dev.cognitive_load)).min(1.0);
        // Energy: cost of perception + prediction + action, regen by idle.
        let cost = self.genome.energy_model.perceive_cost
            + self.genome.energy_model.predict_cost
            + if candidate == Action::Idle { 0.0 } else { self.genome.energy_model.act_cost };
        let regen = if candidate == Action::Idle { self.genome.energy_model.idle_regen } else { 0.0 };
        dev.energy_state = (dev.energy_state - cost + regen).clamp(0.0, 1.0);
        // Plasticity decays slowly with age.
        dev.plasticity = (dev.plasticity * 0.999).max(0.05);
        // Stability rises as prediction accuracy rises.
        dev.stability = 0.5 * dev.stability + 0.5 * dev.prediction_accuracy;
        dev.record_event();

        // 7. Maturation schedule.
        self.apply_maturation();

        TickRecord {
            step,
            action: candidate,
            observation: new_obs.payload.clone(),
            reward: actual_reward,
            prediction_error,
            predicted_reward,
            developmental_stage: self.state.developmental.developmental_stage,
            energy: self.state.developmental.energy_state,
            plasticity: self.state.developmental.plasticity,
            memory_size: self.state.memory.len() as u64,
            state_hash: self.state.short_hash(),
        }
    }

    /// Run one tick with a **forced action** (bypassing the organism's policy).
    ///
    /// This is the entry point used by the [`CounterfactualSelf`](crate::counterfactual::CounterfactualSelf)
    /// module to replay alternative action sequences. The organism still
    /// learns from the outcome (updates preferences, memory, developmental
    /// state), but the action selection is overridden.
    ///
    /// **Safety**: this method is for **simulation only**. It must never be
    /// called against the organism's real environment during normal
    /// operation — only against a counterfactual environment snapshot.
    pub fn tick_with_action(&mut self, env: &mut dyn Environment, forced: Action) -> TickRecord {
        self.state.step += 1;
        let step = self.state.step;

        let obs = env.observe();
        self.state.last_observation = obs.payload.clone();

        let candidate = forced;
        let predicted_reward = self
            .state
            .action_preferences
            .get(&candidate.to_string())
            .copied()
            .unwrap_or(0.0);
        let new_obs = env.step(candidate);
        let actual_reward = new_obs.reward;

        let prediction_error = (predicted_reward - actual_reward).abs();
        let lr = self.genome.plasticity_rules.learning_rate
            * self.state.developmental.plasticity;
        let entry = self
            .state
            .action_preferences
            .entry(candidate.to_string())
            .or_insert(0.0);
        *entry += lr * (actual_reward - predicted_reward);
        *entry *= 1.0 - self.genome.plasticity_rules.forgetting_rate;

        self.state.total_reward += actual_reward;
        self.state.total_prediction_error += prediction_error;
        self.state.last_action = Some(candidate);

        let sig = observation_signature(&obs.payload);
        self.state.memory.push(MemoryRecord {
            key: sig,
            value: serde_json::json!({
                "action": candidate.to_string(),
                "reward": actual_reward,
                "prediction_error": prediction_error,
                "forced": true,
            }),
            importance: (actual_reward.abs() + 0.1).min(1.0),
            step,
            access_count: 0,
        });
        if self.state.memory.len() > 200 {
            self.state.memory.sort_by(|a, b| b.importance.partial_cmp(&a.importance).unwrap_or(std::cmp::Ordering::Equal));
            self.state.memory.truncate(200);
        }

        let alpha = 0.1;
        self.state.self_model.expected_reward =
            (1.0 - alpha) * self.state.self_model.expected_reward + alpha * actual_reward;
        self.state.self_model.expected_prediction_error =
            (1.0 - alpha) * self.state.self_model.expected_prediction_error + alpha * prediction_error;
        self.state.self_model.update_count += 1;
        if candidate == Action::Consume {
            let cap = self.state.self_model.believed_capabilities
                .entry("consume".to_string())
                .or_insert(0.0);
            *cap = (1.0 - alpha) * *cap + alpha * (actual_reward > 0.0) as u64 as f64;
        }

        let dev = &mut self.state.developmental;
        dev.age = step;
        dev.cognitive_load = (dev.cognitive_load * 0.95 + 0.05).min(1.0);
        dev.memory_capacity = (self.state.memory.len() as f64 / 200.0).min(1.0);
        dev.prediction_accuracy =
            1.0 / (1.0 + self.state.self_model.expected_prediction_error);
        dev.self_model_stability =
            (dev.self_model_stability * 0.99 + 0.01 * (1.0 - dev.cognitive_load)).min(1.0);
        let cost = self.genome.energy_model.perceive_cost
            + self.genome.energy_model.predict_cost
            + if candidate == Action::Idle { 0.0 } else { self.genome.energy_model.act_cost };
        let regen = if candidate == Action::Idle { self.genome.energy_model.idle_regen } else { 0.0 };
        dev.energy_state = (dev.energy_state - cost + regen).clamp(0.0, 1.0);
        dev.plasticity = (dev.plasticity * 0.999).max(0.05);
        dev.stability = 0.5 * dev.stability + 0.5 * dev.prediction_accuracy;
        dev.record_event();

        self.apply_maturation();

        TickRecord {
            step,
            action: candidate,
            observation: new_obs.payload.clone(),
            reward: actual_reward,
            prediction_error,
            predicted_reward,
            developmental_stage: self.state.developmental.developmental_stage,
            energy: self.state.developmental.energy_state,
            plasticity: self.state.developmental.plasticity,
            memory_size: self.state.memory.len() as u64,
            state_hash: self.state.short_hash(),
        }
    }

    /// Select an action using an ε-greedy policy over action preferences.
    /// Exploration level is taken from the developmental state.
    ///
    /// The observation influences the action through a small set of
    /// hand-coded heuristic biases (in addition to the learned preferences).
    /// These biases ensure that two organisms in different environments
    /// will, all else equal, take different actions — which is what we
    /// need for the Same Genome / Different World experiment to produce
    /// divergence.
    fn select_action(&self, obs: &Observation) -> Action {
        // ε-greedy: with probability = exploration_level, pick uniformly random.
        // We use a deterministic hash of (step, state_hash, observation signature)
        // as our "random" source so the policy is reproducible AND depends on
        // the current observation.
        let obs_sig = observation_signature(&obs.payload);
        let pseudo = deterministic_random(self.state.step, &format!("{}|{}", self.state.short_hash(), obs_sig));
        if pseudo < self.state.developmental.exploration_level {
            let actions = Action::all();
            let idx = (deterministic_random(self.state.step.wrapping_add(1), &format!("{}|{}", self.state.short_hash(), obs_sig))
                * actions.len() as f64) as usize
                % actions.len();
            return actions[idx];
        }

        // Greedy: pick the action with the highest (learned preference + heuristic bias).
        let mut best = Action::Idle;
        let mut best_score = f64::NEG_INFINITY;
        for a in Action::all() {
            let pref = self
                .state
                .action_preferences
                .get(&a.to_string())
                .copied()
                .unwrap_or(0.0);
            let bias = self.heuristic_bias(*a, obs);
            let score = pref + bias;
            if score > best_score {
                best_score = score;
                best = *a;
            }
        }
        best
    }

    /// Compute a small heuristic bias for an action under an observation.
    /// This is what makes the organism environment-sensitive.
    ///
    /// Heuristics:
    ///   - If on a resource → bias toward Consume.
    ///   - If on a hazard → bias away from staying (Idle).
    ///   - Bias toward the direction of the nearest resource (if known).
    ///   - When far from any resource, encourage exploration over Idling.
    fn heuristic_bias(&self, action: Action, obs: &Observation) -> f64 {
        // PHASE 4 (Scientific Audit): when genome.biases.disable_heuristic_bias
        // is true, return 0.0 for all (action, observation) pairs. This enables
        // the ablation condition F from experiments/ABLATION_MATRIX.md.
        // See docs/RESEARCH_AUDIT.md §9.
        if self.genome.biases.disable_heuristic_bias {
            return 0.0;
        }

        let on_resource = obs.payload.get("on_resource").and_then(|v| v.as_bool()).unwrap_or(false);
        let on_hazard = obs.payload.get("on_hazard").and_then(|v| v.as_bool()).unwrap_or(false);

        let mut bias = 0.0;

        if on_resource && action == Action::Consume {
            bias += 0.5;
        }
        if on_hazard && action == Action::Idle {
            bias -= 0.3;
        }

        // Direction-aware movement bias: if the observation tells us the
        // direction to the nearest resource, prefer the action that moves
        // us closer (reduces Manhattan distance).
        let dir = obs.payload.get("direction_to_resource").and_then(|v| v.as_array());
        if let Some(arr) = dir {
            if arr.len() == 2 {
                let dx = arr[0].as_i64().unwrap_or(0) as i32;
                let dy = arr[1].as_i64().unwrap_or(0) as i32;
                // Prefer moving in the direction that has the larger |delta|.
                // If |dx| >= |dy|, prefer horizontal movement; else vertical.
                if dx.abs() >= dy.abs() {
                    if dx > 0 && action == Action::MoveRight { bias += 0.2; }
                    if dx < 0 && action == Action::MoveLeft  { bias += 0.2; }
                    if dy > 0 && action == Action::MoveUp    { bias += 0.1; }
                    if dy < 0 && action == Action::MoveDown  { bias += 0.1; }
                } else {
                    if dy > 0 && action == Action::MoveUp    { bias += 0.2; }
                    if dy < 0 && action == Action::MoveDown  { bias += 0.2; }
                    if dx > 0 && action == Action::MoveRight { bias += 0.1; }
                    if dx < 0 && action == Action::MoveLeft  { bias += 0.1; }
                }
                // When on the resource (dx=0, dy=0) but not yet consumed,
                // strongly prefer Consume (the on_resource branch already
                // handles this, but reinforce it).
                if dx == 0 && dy == 0 && action == Action::Consume {
                    bias += 0.1;
                }
            }
        }

        // Encourage movement over Idling when far from resource.
        let nearest = obs.payload.get("nearest_resource_distance").and_then(|v| v.as_f64());
        if let Some(d) = nearest {
            if d > 1.0 && action != Action::Idle && action != Action::Consume {
                bias += 0.02;
            }
        }

        bias
    }

    /// Apply the maturation schedule: transition between developmental stages
    /// based on step count thresholds from the genome.
    fn apply_maturation(&mut self) {
        let stage = self.state.developmental.developmental_stage;
        let age = self.state.developmental.age;
        let sched = &self.genome.maturation_schedule;
        let new_stage = match stage {
            DevelopmentalStage::Embryonic => Some(DevelopmentalStage::Nascent),
            DevelopmentalStage::Nascent if age >= sched.nascent_to_developing => {
                Some(DevelopmentalStage::Developing)
            }
            DevelopmentalStage::Developing if age >= sched.developing_to_maturing => {
                Some(DevelopmentalStage::Maturing)
            }
            DevelopmentalStage::Maturing if age >= sched.maturing_to_mature => {
                Some(DevelopmentalStage::Mature)
            }
            _ => None,
        };
        if let Some(s) = new_stage {
            self.state.developmental.developmental_stage = s;
            self.state.developmental.record_event();
        }
    }

    /// Terminate the organism.
    pub fn terminate(&mut self) -> Result<(), String> {
        self.state.lifecycle.transition(
            LifecycleState::Terminated,
            self.state.step,
            "terminated",
        )?;
        self.state.developmental.developmental_stage = DevelopmentalStage::Terminated;
        Ok(())
    }

    /// Snapshot the full organism state as JSON.
    pub fn snapshot(&self) -> serde_json::Value {
        serde_json::to_value(&self.state).unwrap_or(serde_json::Value::Null)
    }

    /// Restore from a JSON snapshot.
    pub fn restore(&mut self, snapshot: &serde_json::Value) -> Result<(), String> {
        let restored: OrganismState = serde_json::from_value(snapshot.clone())
            .map_err(|e| format!("restore failed: {}", e))?;
        self.state = restored;
        Ok(())
    }
}

/// A record of a single tick, suitable for trajectory logging.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TickRecord {
    pub step: u64,
    pub action: Action,
    pub observation: serde_json::Value,
    pub reward: f64,
    pub prediction_error: f64,
    pub predicted_reward: f64,
    pub developmental_stage: DevelopmentalStage,
    pub energy: f64,
    pub plasticity: f64,
    pub memory_size: u64,
    pub state_hash: String,
}

/// Deterministic pseudo-random in [0, 1) derived from a step + salt.
/// Uses a simple xorshift on the bytes; sufficient for ε-greedy selection.
fn deterministic_random(step: u64, salt: &str) -> f64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for b in step.to_le_bytes().iter() {
        h ^= *b as u64;
        h = h.wrapping_mul(0x100000001b3);
    }
    for b in salt.as_bytes() {
        h ^= *b as u64;
        h = h.wrapping_mul(0x100000001b3);
    }
    (h >> 11) as f64 / ((1u64 << 53) as f64)
}

/// Build a compact string signature from an observation payload, for use
/// as a memory key. Uses canonical JSON of the payload.
fn observation_signature(payload: &serde_json::Value) -> String {
    let canonical = hash::canonical_json(payload).unwrap_or_default();
    // Truncate to keep memory keys short.
    if canonical.len() > 64 {
        canonical[..64].to_string()
    } else {
        canonical
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::environment::ResourceWorld;

    #[test]
    fn organism_starts_in_created_state() {
        let g = DevelopmentalGenome::named("test");
        let org = MinimumOrganism::instantiate(g);
        assert_eq!(org.state.lifecycle.current(), LifecycleState::Created);
        assert_eq!(org.state.developmental.developmental_stage, DevelopmentalStage::Embryonic);
    }

    #[test]
    fn begin_development_transitions_to_nascent() {
        let g = DevelopmentalGenome::named("test");
        let mut org = MinimumOrganism::instantiate(g);
        org.initialize().unwrap();
        org.begin_development().unwrap();
        assert_eq!(org.state.lifecycle.current(), LifecycleState::Developing);
        assert_eq!(org.state.developmental.developmental_stage, DevelopmentalStage::Nascent);
    }

    #[test]
    fn tick_produces_record_and_updates_state() {
        let g = DevelopmentalGenome::named("test");
        let mut org = MinimumOrganism::instantiate(g);
        org.initialize().unwrap();
        org.begin_development().unwrap();

        let mut env = ResourceWorld::new(6, 6, 1);
        env.reset();

        let rec = org.tick(&mut env);
        assert_eq!(rec.step, 1);
        assert!(org.state.memory.len() >= 1);
        assert!(org.state.total_reward.abs() < 1e6);
    }

    #[test]
    fn same_genome_same_seed_same_environment_produces_identical_trajectory() {
        let mk = || {
            let g = DevelopmentalGenome::named("repro");
            let mut org = MinimumOrganism::instantiate(g);
            org.initialize().unwrap();
            org.begin_development().unwrap();
            let mut env = ResourceWorld::new(6, 6, 123);
            env.reset();
            let mut records = Vec::new();
            for _ in 0..20 {
                records.push(org.tick(&mut env));
            }
            (org.state.short_hash(), records)
        };
        let (h1, r1) = mk();
        let (h2, r2) = mk();
        assert_eq!(h1, h2);
        assert_eq!(r1.len(), r2.len());
        for (a, b) in r1.iter().zip(r2.iter()) {
            assert_eq!(a.action, b.action);
            assert!((a.reward - b.reward).abs() < 1e-12);
        }
    }

    #[test]
    fn different_environments_produce_different_trajectories() {
        let g = DevelopmentalGenome::named("diverge");

        let mut org_a = MinimumOrganism::instantiate(g.clone());
        org_a.initialize().unwrap();
        org_a.begin_development().unwrap();
        let mut env_a = ResourceWorld::new(6, 6, 1);
        env_a.reset();
        for _ in 0..30 {
            org_a.tick(&mut env_a);
        }

        let mut org_b = MinimumOrganism::instantiate(g.clone());
        org_b.initialize().unwrap();
        org_b.begin_development().unwrap();
        let mut env_b = ResourceWorld::new(6, 6, 999); // different seed
        env_b.reset();
        for _ in 0..30 {
            org_b.tick(&mut env_b);
        }

        assert_ne!(org_a.state.short_hash(), org_b.state.short_hash());
    }

    #[test]
    fn snapshot_restore_round_trips() {
        let g = DevelopmentalGenome::named("snap");
        let mut org = MinimumOrganism::instantiate(g);
        org.initialize().unwrap();
        org.begin_development().unwrap();
        let mut env = ResourceWorld::new(6, 6, 1);
        env.reset();
        for _ in 0..5 {
            org.tick(&mut env);
        }
        let snap = org.snapshot();
        let hash_before = org.state.short_hash();

        // Mutate further.
        for _ in 0..5 {
            org.tick(&mut env);
        }
        assert_ne!(org.state.short_hash(), hash_before);

        // Restore.
        org.restore(&snap).unwrap();
        assert_eq!(org.state.short_hash(), hash_before);
    }
}
