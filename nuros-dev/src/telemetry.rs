//! Developmental Telemetry + Reproducibility Manifest.
//!
//! Every organism exposes telemetry: a stream of structured records
//! describing what happened at each step. Telemetry is exported as JSONL
//! (one JSON object per line) and CSV (a flat table). Researchers can
//! analyze trajectories outside NurosOS using any tool that reads these
//! formats.
//!
//! Every experiment produces a `ReproducibilityManifest` — a machine-
//! readable document that records all the hashes and seeds needed to
//! reproduce the experiment. The manifest is the single artifact that
//! turns an artificial cognitive trajectory into a reproducible scientific
//! object.

use serde::{Deserialize, Serialize};

use crate::checkpoint::MindCheckpoint;
use crate::organism::TickRecord;
use crate::state::DevelopmentalState;
use crate::trajectory::DevelopmentalTrajectory;

/// A single telemetry record. One per tick.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelemetryRecord {
    pub step: u64,
    pub organism_id: String,
    pub genome_hash: String,
    pub environment_hash: String,
    pub action: String,
    pub reward: f64,
    pub prediction_error: f64,
    pub predicted_reward: f64,
    pub developmental_stage: String,
    pub age: u64,
    pub maturity: f64,
    pub plasticity: f64,
    pub stability: f64,
    pub energy_state: f64,
    pub cognitive_load: f64,
    pub memory_capacity: f64,
    pub prediction_accuracy: f64,
    pub self_model_stability: f64,
    pub exploration_level: f64,
    pub risk_sensitivity: f64,
    pub memory_size: u64,
    pub total_reward: f64,
    pub total_prediction_error: f64,
    pub state_hash: String,
}

impl TelemetryRecord {
    /// Construct a telemetry record from a tick + developmental state.
    pub fn from_tick(
        tick: &TickRecord,
        dev: &DevelopmentalState,
        organism_id: &str,
        genome_hash: &str,
        environment_hash: &str,
        total_reward: f64,
        total_prediction_error: f64,
    ) -> Self {
        Self {
            step: tick.step,
            organism_id: organism_id.to_string(),
            genome_hash: genome_hash.to_string(),
            environment_hash: environment_hash.to_string(),
            action: tick.action.to_string(),
            reward: tick.reward,
            prediction_error: tick.prediction_error,
            predicted_reward: tick.predicted_reward,
            developmental_stage: tick.developmental_stage.to_string(),
            age: dev.age,
            maturity: dev.maturity,
            plasticity: dev.plasticity,
            stability: dev.stability,
            energy_state: dev.energy_state,
            cognitive_load: dev.cognitive_load,
            memory_capacity: dev.memory_capacity,
            prediction_accuracy: dev.prediction_accuracy,
            self_model_stability: dev.self_model_stability,
            exploration_level: dev.exploration_level,
            risk_sensitivity: dev.risk_sensitivity,
            memory_size: tick.memory_size,
            total_reward,
            total_prediction_error,
            state_hash: tick.state_hash.clone(),
        }
    }
}

/// A telemetry stream: an ordered list of records.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct DevelopmentalTelemetry {
    pub records: Vec<TelemetryRecord>,
}

impl DevelopmentalTelemetry {
    /// Create an empty telemetry stream.
    pub fn new() -> Self {
        Self::default()
    }

    /// Append a record.
    pub fn push(&mut self, record: TelemetryRecord) {
        self.records.push(record);
    }

    /// Number of records.
    pub fn len(&self) -> usize {
        self.records.len()
    }

    /// True if empty.
    pub fn is_empty(&self) -> bool {
        self.records.is_empty()
    }

    /// Export as JSONL (one JSON object per line).
    pub fn to_jsonl(&self) -> String {
        let mut s = String::new();
        for r in &self.records {
            if let Ok(line) = serde_json::to_string(r) {
                s.push_str(&line);
                s.push('\n');
            }
        }
        s
    }

    /// Export as CSV.
    pub fn to_csv(&self) -> String {
        let header = "step,organism_id,genome_hash,environment_hash,action,reward,prediction_error,predicted_reward,developmental_stage,age,maturity,plasticity,stability,energy_state,cognitive_load,memory_capacity,prediction_accuracy,self_model_stability,exploration_level,risk_sensitivity,memory_size,total_reward,total_prediction_error,state_hash\n";
        let mut s = String::from(header);
        for r in &self.records {
            s.push_str(&format!(
                "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n",
                r.step,
                r.organism_id,
                &r.genome_hash[..12.min(r.genome_hash.len())],
                &r.environment_hash[..12.min(r.environment_hash.len())],
                r.action,
                r.reward,
                r.prediction_error,
                r.predicted_reward,
                r.developmental_stage,
                r.age,
                r.maturity,
                r.plasticity,
                r.stability,
                r.energy_state,
                r.cognitive_load,
                r.memory_capacity,
                r.prediction_accuracy,
                r.self_model_stability,
                r.exploration_level,
                r.risk_sensitivity,
                r.memory_size,
                r.total_reward,
                r.total_prediction_error,
                &r.state_hash[..12.min(r.state_hash.len())],
            ));
        }
        s
    }
}

/// The reproducibility manifest for an experiment.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReproducibilityManifest {
    /// ID of the mind (organism) this manifest describes.
    pub mind_id: String,
    /// Hash of the genome the organism was instantiated from.
    pub genome_hash: String,
    /// Hash of the runtime (the `nuros-dev` crate version + ABI hash).
    pub runtime_hash: String,
    /// Hash of the environment the organism developed in.
    pub environment_hash: String,
    /// Hash of the experiment configuration.
    pub experiment_hash: String,
    /// Random seed used to instantiate the organism.
    pub random_seed: u64,
    /// Random seed used by the environment.
    pub environment_seed: u64,
    /// Hash of the final checkpoint taken at the end of the experiment.
    pub checkpoint_hash: String,
    /// Hash of the experiment configuration (YAML/JSON).
    pub configuration_hash: String,
    /// Versions of all dependencies used (crate versions, Python versions).
    pub dependency_versions: std::collections::BTreeMap<String, String>,
    /// Timestamp (Unix epoch seconds) at which the experiment was run.
    pub timestamp: u64,
    /// Number of steps in the experiment.
    pub n_steps: u64,
    /// Optional list of limitations / caveats (e.g. "non-deterministic host
    /// clock used for some decisions").
    pub limitations: Vec<String>,
}

impl ReproducibilityManifest {
    /// Build a manifest from an experiment's components.
    pub fn build(
        mind_id: impl Into<String>,
        genome_hash: impl Into<String>,
        environment_hash: impl Into<String>,
        experiment_hash: impl Into<String>,
        random_seed: u64,
        environment_seed: u64,
        checkpoint: &MindCheckpoint,
        configuration: &serde_json::Value,
        n_steps: u64,
    ) -> Self {
        let mut dependency_versions = std::collections::BTreeMap::new();
        dependency_versions.insert(
            "nuros-dev".to_string(),
            env!("CARGO_PKG_VERSION").to_string(),
        );
        dependency_versions.insert(
            "rustc".to_string(),
            env!("CARGO_PKG_RUST_VERSION").to_string(),
        );

        let configuration_hash = crate::hash::hash(configuration);
        let runtime_hash = crate::hash::hash_str(&format!(
            "{}:{}",
            env!("CARGO_PKG_VERSION"),
            env!("CARGO_PKG_RUST_VERSION"),
        ));

        Self {
            mind_id: mind_id.into(),
            genome_hash: genome_hash.into(),
            runtime_hash,
            environment_hash: environment_hash.into(),
            experiment_hash: experiment_hash.into(),
            random_seed,
            environment_seed,
            checkpoint_hash: checkpoint.hash(),
            configuration_hash,
            dependency_versions,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_secs())
                .unwrap_or(0),
            n_steps,
            limitations: Vec::new(),
        }
    }

    /// Add a limitation / caveat.
    pub fn with_limitation(mut self, limitation: impl Into<String>) -> Self {
        self.limitations.push(limitation.into());
        self
    }

    /// Serialize to canonical JSON.
    pub fn to_json(&self) -> serde_json::Result<String> {
        crate::hash::canonical_json(self)
    }

    /// Render a human-readable summary.
    pub fn render(&self) -> String {
        let mut s = String::new();
        s.push_str("=== Reproducibility Manifest ===\n");
        s.push_str(&format!("  mind_id:            {}\n", self.mind_id));
        s.push_str(&format!("  genome_hash:        {}...\n", &self.genome_hash[..12.min(self.genome_hash.len())]));
        s.push_str(&format!("  runtime_hash:       {}...\n", &self.runtime_hash[..12.min(self.runtime_hash.len())]));
        s.push_str(&format!("  environment_hash:   {}...\n", &self.environment_hash[..12.min(self.environment_hash.len())]));
        s.push_str(&format!("  experiment_hash:    {}...\n", &self.experiment_hash[..12.min(self.experiment_hash.len())]));
        s.push_str(&format!("  configuration_hash: {}...\n", &self.configuration_hash[..12.min(self.configuration_hash.len())]));
        s.push_str(&format!("  checkpoint_hash:    {}...\n", &self.checkpoint_hash[..12.min(self.checkpoint_hash.len())]));
        s.push_str(&format!("  random_seed:        {}\n", self.random_seed));
        s.push_str(&format!("  environment_seed:   {}\n", self.environment_seed));
        s.push_str(&format!("  n_steps:            {}\n", self.n_steps));
        s.push_str(&format!("  timestamp:          {}\n", self.timestamp));
        s.push_str("  dependencies:\n");
        for (k, v) in &self.dependency_versions {
            s.push_str(&format!("    {} = {}\n", k, v));
        }
        if !self.limitations.is_empty() {
            s.push_str("  limitations:\n");
            for l in &self.limitations {
                s.push_str(&format!("    - {}\n", l));
            }
        }
        s
    }
}

/// Helper: convert a trajectory into a telemetry stream.
pub fn trajectory_to_telemetry(traj: &DevelopmentalTrajectory) -> DevelopmentalTelemetry {
    let mut tel = DevelopmentalTelemetry::new();
    let mut cum_reward = 0.0;
    let mut cum_pe = 0.0;
    for p in &traj.points {
        cum_reward += p.reward;
        cum_pe += p.prediction_error;
        tel.push(TelemetryRecord {
            step: p.step,
            organism_id: traj.organism_id.clone(),
            genome_hash: traj.genome_hash.clone(),
            environment_hash: traj.environment_hash.clone(),
            action: p.action.to_string(),
            reward: p.reward,
            prediction_error: p.prediction_error,
            predicted_reward: p.predicted_reward,
            developmental_stage: p.developmental_state.developmental_stage.to_string(),
            age: p.developmental_state.age,
            maturity: p.developmental_state.maturity,
            plasticity: p.developmental_state.plasticity,
            stability: p.developmental_state.stability,
            energy_state: p.developmental_state.energy_state,
            cognitive_load: p.developmental_state.cognitive_load,
            memory_capacity: p.developmental_state.memory_capacity,
            prediction_accuracy: p.developmental_state.prediction_accuracy,
            self_model_stability: p.developmental_state.self_model_stability,
            exploration_level: p.developmental_state.exploration_level,
            risk_sensitivity: p.developmental_state.risk_sensitivity,
            memory_size: p.memory_size,
            total_reward: cum_reward,
            total_prediction_error: cum_pe,
            state_hash: p.state_hash.clone(),
        });
    }
    tel
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::environment::{ResourceWorld, Environment};
    use crate::genome::DevelopmentalGenome;
    use crate::organism::MinimumOrganism;
    use crate::trajectory::DevelopmentalTrajectory;

    #[test]
    fn telemetry_export_jsonl_has_one_line_per_record() {
        let g = DevelopmentalGenome::named("tel");
        let mut org = MinimumOrganism::instantiate(g.clone());
        org.initialize().unwrap();
        org.begin_development().unwrap();
        let mut env = ResourceWorld::new(6, 6, 1);
        env.reset();
        let env_hash = env.hash();
        let mut traj = DevelopmentalTrajectory::new("org", g.hash(), env_hash, 1);
        for _ in 0..5 {
            let tick = org.tick(&mut env);
            traj.record(&tick, &org.state.developmental);
        }
        let tel = trajectory_to_telemetry(&traj);
        let jsonl = tel.to_jsonl();
        assert_eq!(jsonl.lines().count(), 5);
    }

    #[test]
    fn telemetry_export_csv_has_header_plus_one_line_per_record() {
        let g = DevelopmentalGenome::named("tel");
        let mut org = MinimumOrganism::instantiate(g.clone());
        org.initialize().unwrap();
        org.begin_development().unwrap();
        let mut env = ResourceWorld::new(6, 6, 1);
        env.reset();
        let env_hash = env.hash();
        let mut traj = DevelopmentalTrajectory::new("org", g.hash(), env_hash, 1);
        for _ in 0..3 {
            let tick = org.tick(&mut env);
            traj.record(&tick, &org.state.developmental);
        }
        let tel = trajectory_to_telemetry(&traj);
        let csv = tel.to_csv();
        assert_eq!(csv.lines().count(), 4); // header + 3
        assert!(csv.lines().next().unwrap().starts_with("step,"));
    }

    #[test]
    fn manifest_renders_human_readable() {
        let g = DevelopmentalGenome::named("man");
        let mut org = MinimumOrganism::instantiate(g.clone());
        org.initialize().unwrap();
        org.begin_development().unwrap();
        let mut env = ResourceWorld::new(6, 6, 1);
        env.reset();
        for _ in 0..10 {
            org.tick(&mut env);
        }
        let ck = MindCheckpoint::take(&org, &env, 1, 0, "final");
        let cfg = serde_json::json!({"experiment": "test"});
        let man = ReproducibilityManifest::build(
            "org-1",
            g.hash(),
            env.hash(),
            crate::hash::hash(&cfg),
            0,
            1,
            &ck,
            &cfg,
            10,
        );
        let s = man.render();
        assert!(s.contains("Reproducibility Manifest"));
        assert!(s.contains("genome_hash"));
        assert!(s.contains("nuros-dev"));
    }

    #[test]
    fn manifest_round_trips_through_json() {
        let g = DevelopmentalGenome::named("man");
        let mut org = MinimumOrganism::instantiate(g.clone());
        org.initialize().unwrap();
        org.begin_development().unwrap();
        let mut env = ResourceWorld::new(6, 6, 1);
        env.reset();
        for _ in 0..5 {
            org.tick(&mut env);
        }
        let ck = MindCheckpoint::take(&org, &env, 1, 0, "final");
        let cfg = serde_json::json!({});
        let man = ReproducibilityManifest::build(
            "org", g.hash(), env.hash(), "exp", 0, 1, &ck, &cfg, 5,
        );
        let json = man.to_json().unwrap();
        let man2: ReproducibilityManifest = serde_json::from_str(&json).unwrap();
        assert_eq!(man.checkpoint_hash, man2.checkpoint_hash);
        assert_eq!(man.genome_hash, man2.genome_hash);
    }
}
