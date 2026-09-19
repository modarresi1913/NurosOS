//! Developmental Genome.
//!
//! The genome represents the **initial developmental conditions** of an
//! artificial organism — not a fully specified architecture. Two organisms
//! instantiated from the same genome, placed in different environments,
//! should produce divergent developmental trajectories. That divergence is
//! the central research object of NurosOS.
//!
//! The genome is serializable (canonical JSON) and has a deterministic
//! SHA-256 hash. The hash becomes part of experiment provenance: every
//! checkpoint, trajectory, and manifest records the genome hash that
//! produced it.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

use crate::hash;

/// Architectural specification of the organism's cognitive substrate.
///
/// This is intentionally minimal: a tagged type plus a free-form map of
/// parameters. The genome does NOT specify weights, topologies, or learned
/// state — those emerge through development.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArchitectureSpec {
    /// Tag identifying the cognitive engine type (e.g. "deterministic_reactive",
    /// "predictive_symbolic", "snn_lif"). The runtime uses this to dispatch
    /// to the correct engine.
    pub engine: String,
    /// Free-form parameters passed to the engine constructor.
    #[serde(default)]
    pub parameters: BTreeMap<String, serde_json::Value>,
}

impl Default for ArchitectureSpec {
    fn default() -> Self {
        Self {
            engine: "deterministic_reactive".to_string(),
            parameters: BTreeMap::new(),
        }
    }
}

/// Initial memory seeds. The organism is born with these memories already
/// in its memory contract — they are not learned. Useful for studying how
/// "innate" structure biases development.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct InitialMemorySpec {
    /// Episodic memories seeded at birth.
    #[serde(default)]
    pub episodic: Vec<serde_json::Value>,
    /// Semantic facts seeded at birth.
    #[serde(default)]
    pub semantic: Vec<serde_json::Value>,
}

/// Rules governing plasticity (how the organism changes its decision policy
/// as a function of experience). For the MVP deterministic engine this is
/// just a learning rate; richer engines may add Hebbian/STDP rules.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct PlasticityRulesSpec {
    /// Learning rate applied to prediction-error-driven updates.
    #[serde(default = "default_lr")]
    pub learning_rate: f64,
    /// Discount factor for prediction error (higher = forget faster).
    #[serde(default = "default_forget")]
    pub forgetting_rate: f64,
}

fn default_lr() -> f64 { 0.1 }
fn default_forget() -> f64 { 0.01 }

/// Maturation schedule: at what experience count does each developmental
/// milestone trigger. Maps milestone name → step threshold.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct MaturationScheduleSpec {
    /// Step at which the organism transitions NASCENT → DEVELOPING.
    #[serde(default = "default_nasant_step")]
    pub nascent_to_developing: u64,
    /// Step at which DEVELOPING → MATURING.
    #[serde(default = "default_maturing_step")]
    pub developing_to_maturing: u64,
    /// Step at which MATURING → MATURE.
    #[serde(default = "default_mature_step")]
    pub maturing_to_mature: u64,
}

fn default_nasant_step() -> u64 { 10 }
fn default_maturing_step() -> u64 { 100 }
fn default_mature_step() -> u64 { 500 }

/// Homeostasis parameters: setpoints + adaptation rates for the internal
/// regulation variables.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct HomeostasisSpec {
    /// Setpoint for energy (organism tries to keep energy at this level).
    #[serde(default = "default_energy_setpoint")]
    pub energy_setpoint: f64,
    /// Setpoint for prediction_error (target).
    #[serde(default = "default_pe_setpoint")]
    pub prediction_error_setpoint: f64,
    /// Setpoint for uncertainty (target).
    #[serde(default = "default_uncertainty_setpoint")]
    pub uncertainty_setpoint: f64,
}

fn default_energy_setpoint() -> f64 { 0.8 }
fn default_pe_setpoint() -> f64 { 0.1 }
fn default_uncertainty_setpoint() -> f64 { 0.2 }

/// Energy model: how much each cognitive operation costs in energy.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct EnergyModelSpec {
    #[serde(default = "default_perceive_cost")]
    pub perceive_cost: f64,
    #[serde(default = "default_predict_cost")]
    pub predict_cost: f64,
    #[serde(default = "default_act_cost")]
    pub act_cost: f64,
    #[serde(default = "default_idle_regen")]
    pub idle_regen: f64,
}

fn default_perceive_cost() -> f64 { 0.01 }
fn default_predict_cost() -> f64 { 0.02 }
fn default_act_cost() -> f64 { 0.05 }
fn default_idle_regen() -> f64 { 0.03 }

/// Mutation parameters used by the (PROPOSED) artificial evolution layer.
/// Recorded here so that the genome is self-describing about how it can be
/// mutated.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct MutationSpec {
    /// Probability of mutating each numeric field during reproduction.
    #[serde(default = "default_mut_rate")]
    pub mutation_rate: f64,
    /// Standard deviation of Gaussian perturbation applied during mutation.
    #[serde(default = "default_mut_sigma")]
    pub mutation_sigma: f64,
}

fn default_mut_rate() -> f64 { 0.05 }
fn default_mut_sigma() -> f64 { 0.1 }

/// Initial capabilities the organism is born with. Capabilities are
/// coarse-grained abilities (e.g. "locate_resource", "avoid_risk") that
/// can be acquired or lost during development.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct InitialCapabilitiesSpec {
    /// Map of capability name → initial proficiency in [0, 1].
    #[serde(default)]
    pub capabilities: BTreeMap<String, f64>,
}

/// Exploration / prediction / value biases that shape early behavior.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BiasesSpec {
    /// Initial exploration drive in [0, 1]. Higher = more random actions.
    #[serde(default = "default_exploration_bias")]
    pub exploration_bias: f64,
    /// Initial prediction confidence in [0, 1]. Higher = trusts own model more.
    #[serde(default = "default_prediction_bias")]
    pub prediction_bias: f64,
    /// Initial risk sensitivity in [0, 1]. Higher = more risk-averse.
    #[serde(default = "default_risk_sensitivity")]
    pub risk_sensitivity: f64,
    /// PHASE 4 (Scientific Audit): when true, `MinimumOrganism::heuristic_bias()`
    /// returns 0.0 for all (action, observation) pairs. This enables the
    /// ablation condition F (no heuristic bias) from `experiments/ABLATION_MATRIX.md`.
    /// Default: false (backward compatible — bias is enabled by default).
    #[serde(default)]
    pub disable_heuristic_bias: bool,
}

fn default_exploration_bias() -> f64 { 0.3 }
fn default_prediction_bias() -> f64 { 0.5 }
fn default_risk_sensitivity() -> f64 { 0.5 }

impl Default for BiasesSpec {
    fn default() -> Self {
        Self {
            exploration_bias: default_exploration_bias(),
            prediction_bias: default_prediction_bias(),
            risk_sensitivity: default_risk_sensitivity(),
            disable_heuristic_bias: false,
        }
    }
}

/// The Developmental Genome.
///
/// This structure is the **complete** specification of an organism's
/// initial developmental conditions. It is intentionally richer than
/// architecture alone: it specifies memory seeds, plasticity rules,
/// maturation schedule, homeostasis setpoints, energy model, biases,
/// and mutation parameters.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DevelopmentalGenome {
    /// Human-readable name for this genome.
    pub name: String,
    /// Semantic version of the genome schema.
    #[serde(default = "default_genome_version")]
    pub version: String,
    /// Architectural specification (engine + parameters).
    #[serde(default)]
    pub architecture: ArchitectureSpec,
    /// Initial memory seeds.
    #[serde(default)]
    pub initial_memory: InitialMemorySpec,
    /// Initial capability proficiencies.
    #[serde(default)]
    pub initial_capabilities: InitialCapabilitiesSpec,
    /// Plasticity rules (learning + forgetting rates).
    #[serde(default)]
    pub plasticity_rules: PlasticityRulesSpec,
    /// Cognitive biases (exploration, prediction, risk).
    #[serde(default)]
    pub biases: BiasesSpec,
    /// Maturation schedule.
    #[serde(default)]
    pub maturation_schedule: MaturationScheduleSpec,
    /// Homeostasis setpoints.
    #[serde(default)]
    pub homeostasis: HomeostasisSpec,
    /// Energy model.
    #[serde(default)]
    pub energy_model: EnergyModelSpec,
    /// Mutation parameters (for the evolution layer).
    #[serde(default)]
    pub mutation_parameters: MutationSpec,
    /// Optional parent genome hash (for tracking lineage in evolution).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parent_genome_hash: Option<String>,
}

fn default_genome_version() -> String { "0.1.0".to_string() }

impl DevelopmentalGenome {
    /// Compute the canonical SHA-256 hash of this genome.
    ///
    /// Two genomes that produce the same hash are *guaranteed* to be
    /// structurally identical (modulo floating-point representation,
    /// which is normalized by canonical JSON).
    pub fn hash(&self) -> String {
        hash::hash(self)
    }

    /// Short form of the hash (first 12 hex chars) for human-readable display.
    pub fn short_hash(&self) -> String {
        hash::short_hash(&self.hash())
    }

    /// Serialize to canonical JSON string.
    pub fn to_canonical_json(&self) -> serde_json::Result<String> {
        hash::canonical_json(self)
    }

    /// Deserialize from a JSON string.
    pub fn from_json(s: &str) -> serde_json::Result<Self> {
        serde_json::from_str(s)
    }

    /// Construct a default genome with the given name.
    pub fn named(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            version: default_genome_version(),
            architecture: ArchitectureSpec::default(),
            initial_memory: InitialMemorySpec::default(),
            initial_capabilities: InitialCapabilitiesSpec::default(),
            plasticity_rules: PlasticityRulesSpec::default(),
            biases: BiasesSpec::default(),
            maturation_schedule: MaturationScheduleSpec::default(),
            homeostasis: HomeostasisSpec::default(),
            energy_model: EnergyModelSpec::default(),
            mutation_parameters: MutationSpec::default(),
            parent_genome_hash: None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn genome_hash_is_deterministic() {
        let g1 = DevelopmentalGenome::named("test");
        let g2 = DevelopmentalGenome::named("test");
        assert_eq!(g1.hash(), g2.hash());
    }

    #[test]
    fn genome_hash_changes_with_name() {
        let g1 = DevelopmentalGenome::named("alpha");
        let g2 = DevelopmentalGenome::named("beta");
        assert_ne!(g1.hash(), g2.hash());
    }

    #[test]
    fn genome_round_trips_through_json() {
        let g = DevelopmentalGenome::named("round_trip");
        let json = g.to_canonical_json().unwrap();
        let g2: DevelopmentalGenome = serde_json::from_str(&json).unwrap();
        assert_eq!(g.hash(), g2.hash());
    }

    #[test]
    fn genome_hash_is_sixtyfour_chars() {
        let g = DevelopmentalGenome::named("len_test");
        let h = g.hash();
        assert_eq!(h.len(), 64);
    }

    #[test]
    fn same_logical_genome_has_same_hash_after_json_roundtrip() {
        let g1 = DevelopmentalGenome::named("consistency");
        let json = serde_json::to_string(&g1).unwrap();
        let g2: DevelopmentalGenome = serde_json::from_str(&json).unwrap();
        // Even though serde_json::to_string doesn't sort keys, the hash
        // function uses canonical_json internally which does sort.
        assert_eq!(g1.hash(), g2.hash());
    }

    #[test]
    fn different_plasticity_rates_change_hash() {
        let mut g1 = DevelopmentalGenome::named("plasticity");
        let mut g2 = DevelopmentalGenome::named("plasticity");
        g1.plasticity_rules.learning_rate = 0.1;
        g2.plasticity_rules.learning_rate = 0.2;
        assert_ne!(g1.hash(), g2.hash());
    }
}
