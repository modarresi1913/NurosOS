//! # nuros-dev — Developmental substrate for NurosOS.
//!
//! This crate provides the runtime, interfaces, environments, developmental
//! mechanisms, observability, and reproducibility infrastructure required
//! to instantiate, develop, measure, fork, replay, and compare artificial
//! cognitive systems.
//!
//! ## Module map
//!
//! | Module           | Responsibility                                                |
//! |------------------|---------------------------------------------------------------|
//! | [`hash`]         | Canonical JSON + SHA-256 (single source of truth for hashes)  |
//! | [`lifecycle`]    | Organism lifecycle state machine                              |
//! | [`genome`]       | `DevelopmentalGenome` + canonical hash                         |
//! | [`state`]        | `DevelopmentalState` vector + distance metric                 |
//! | [`environment`]  | `Environment` trait + `ResourceWorld` + `ChangingWorld`       |
//! | [`organism`]     | `MinimumOrganism` — deterministic cognitive engine            |
//! | [`trajectory`]   | `DevelopmentalTrajectory` + divergence metrics                |
//! | [`checkpoint`]   | `MindCheckpoint` + replay + fidelity classification           |
//! | [`diff`]         | `MindDiff` — structured comparison of two organism states     |
//! | [`causality`]    | `DevelopmentalCausalityGraph` — provenance DAG                |
//! | [`telemetry`]    | `DevelopmentalTelemetry` + `ReproducibilityManifest`          |

#![warn(missing_docs)]

pub mod hash;
pub mod lifecycle;
pub mod genome;
pub mod state;
pub mod environment;
pub mod organism;
pub mod trajectory;
pub mod checkpoint;
pub mod diff;
pub mod causality;
pub mod telemetry;
pub mod counterfactual;
pub mod metabolism;
pub mod aging;

// Re-export the most commonly used types at the crate root for convenience.
pub use genome::DevelopmentalGenome;
pub use state::{DevelopmentalState, DevelopmentalStage};
pub use lifecycle::{LifecycleMachine, LifecycleState, LifecycleTransition};
pub use environment::{Action, Environment, Observation, ResourceWorld, ChangingWorld};
pub use organism::{MinimumOrganism, OrganismState, TickRecord};
pub use trajectory::{DevelopmentalTrajectory, DevelopmentalDivergence, TrajectoryPoint};
pub use checkpoint::{MindCheckpoint, ReplayFidelity, ReplayResult, replay_from_checkpoint};
pub use diff::MindDiff;
pub use causality::{DevelopmentalCausalityGraph, EventKind, CausalEvent};
pub use telemetry::{DevelopmentalTelemetry, TelemetryRecord, ReproducibilityManifest, trajectory_to_telemetry};
pub use counterfactual::{CounterfactualSelf, CounterfactualTrajectory, PossibleSelfSpace, COUNTERFACTUAL_LABELS};
pub use metabolism::{CognitiveMetabolism, CognitiveBudget, CognitiveCostModel, CognitiveOperation, BudgetSpending};
pub use aging::{AgingModel, AgingEffect};

/// The semantic version of this crate. Recorded in every manifest.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

// ============================================================================
// PyO3 bindings — expose the developmental substrate to Python as `nuros._dev`
// ============================================================================

use pyo3::prelude::*;

/// Python-facing wrapper around a `DevelopmentalGenome`.
#[pyclass(name = "DevelopmentalGenome")]
#[derive(Clone)]
pub struct PyGenome {
    pub inner: DevelopmentalGenome,
}

#[pymethods]
impl PyGenome {
    /// Construct a default genome with the given name.
    #[new]
    #[pyo3(signature = (name="unnamed".to_string()))]
    fn new(name: String) -> Self {
        Self { inner: DevelopmentalGenome::named(name) }
    }

    /// Canonical SHA-256 hash of the genome (64-char hex string).
    #[getter]
    fn hash(&self) -> String { self.inner.hash() }

    /// Short form of the hash (first 12 chars).
    #[getter]
    fn short_hash(&self) -> String { self.inner.short_hash() }

    /// Genome name.
    #[getter]
    fn name(&self) -> String { self.inner.name.clone() }

    /// Serialize to canonical JSON.
    fn to_json(&self) -> PyResult<String> {
        self.inner.to_canonical_json().map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }

    /// Deserialize from JSON.
    #[staticmethod]
    fn from_json(s: &str) -> PyResult<Self> {
        DevelopmentalGenome::from_json(s)
            .map(|g| Self { inner: g })
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }

    /// Set the learning rate.
    fn with_learning_rate(mut slf: PyRefMut<Self>, lr: f64) -> PyRefMut<Self> {
        slf.inner.plasticity_rules.learning_rate = lr;
        slf
    }

    /// Set the forgetting rate.
    fn with_forgetting_rate(mut slf: PyRefMut<Self>, fr: f64) -> PyRefMut<Self> {
        slf.inner.plasticity_rules.forgetting_rate = fr;
        slf
    }

    /// Set the exploration bias.
    fn with_exploration_bias(mut slf: PyRefMut<Self>, b: f64) -> PyRefMut<Self> {
        slf.inner.biases.exploration_bias = b;
        slf
    }

    /// Set the prediction bias.
    fn with_prediction_bias(mut slf: PyRefMut<Self>, b: f64) -> PyRefMut<Self> {
        slf.inner.biases.prediction_bias = b;
        slf
    }

    /// Set the risk sensitivity.
    fn with_risk_sensitivity(mut slf: PyRefMut<Self>, b: f64) -> PyRefMut<Self> {
        slf.inner.biases.risk_sensitivity = b;
        slf
    }

    /// Set the maturation thresholds (nascent→developing, developing→maturing, maturing→mature).
    fn with_maturation(mut slf: PyRefMut<Self>, n2d: u64, d2m: u64, m2m: u64) -> PyRefMut<Self> {
        slf.inner.maturation_schedule.nascent_to_developing = n2d;
        slf.inner.maturation_schedule.developing_to_maturing = d2m;
        slf.inner.maturation_schedule.maturing_to_mature = m2m;
        slf
    }
}

/// Python-facing wrapper around a `ResourceWorld`.
#[pyclass(name = "ResourceWorld")]
pub struct PyResourceWorld {
    pub inner: ResourceWorld,
}

#[pymethods]
impl PyResourceWorld {
    /// Construct a new ResourceWorld(width, height, seed).
    #[new]
    fn new(width: u32, height: u32, seed: u64) -> Self {
        Self { inner: ResourceWorld::new(width, height, seed) }
    }

    /// Reset to initial state. Returns observation payload as a Python dict.
    fn reset(&mut self) -> PyResult<PyObject> {
        let obs = self.inner.reset();
        Python::with_gil(|py| Ok(py_obj_from_json(&obs.payload, py)))
    }

    /// Get the current observation without stepping.
    fn observe(&self) -> PyResult<PyObject> {
        let obs = self.inner.observe();
        Python::with_gil(|py| Ok(py_obj_from_json(&obs.payload, py)))
    }

    /// Apply an action. Returns (observation, reward, done, step).
    fn step(&mut self, action: &str) -> PyResult<(PyObject, f64, bool, u64)> {
        let act = parse_action(action)?;
        let obs = self.inner.step(act);
        Python::with_gil(|py| {
            Ok((
                py_obj_from_json(&obs.payload, py),
                obs.reward,
                obs.done,
                obs.step,
            ))
        })
    }

    /// Hash of the current state.
    #[getter]
    fn hash(&self) -> String { self.inner.hash() }

    /// Render the world as a string.
    fn render(&self) -> String { self.inner.render() }

    /// Snapshot the full state to a JSON string.
    fn snapshot(&self) -> String {
        serde_json::to_string(&self.inner.snapshot()).unwrap_or_default()
    }
}

/// Python-facing wrapper around a `ChangingWorld`.
#[pyclass(name = "ChangingWorld")]
pub struct PyChangingWorld {
    pub inner: ChangingWorld,
}

#[pymethods]
impl PyChangingWorld {
    /// Construct a new ChangingWorld(size, shift_interval, seed).
    #[new]
    fn new(size: u32, shift_interval: u64, seed: u64) -> Self {
        Self { inner: ChangingWorld::new(size, shift_interval, seed) }
    }

    /// Reset to initial state. Returns observation payload as a Python dict.
    fn reset(&mut self) -> PyResult<PyObject> {
        let obs = self.inner.reset();
        Python::with_gil(|py| Ok(py_obj_from_json(&obs.payload, py)))
    }

    /// Get the current observation without stepping.
    fn observe(&self) -> PyResult<PyObject> {
        let obs = self.inner.observe();
        Python::with_gil(|py| Ok(py_obj_from_json(&obs.payload, py)))
    }

    /// Apply an action.
    fn step(&mut self, action: &str) -> PyResult<(PyObject, f64, bool, u64)> {
        let act = parse_action(action)?;
        let obs = self.inner.step(act);
        Python::with_gil(|py| {
            Ok((
                py_obj_from_json(&obs.payload, py),
                obs.reward,
                obs.done,
                obs.step,
            ))
        })
    }

    /// Hash of the current state.
    #[getter]
    fn hash(&self) -> String { self.inner.hash() }

    /// Render the world as a string.
    fn render(&self) -> String { self.inner.render() }
}

/// Python-facing wrapper around a `MinimumOrganism`.
#[pyclass(name = "MinimumOrganism")]
pub struct PyOrganism {
    pub inner: MinimumOrganism,
}

#[pymethods]
impl PyOrganism {
    /// Instantiate a new organism from a genome.
    #[new]
    fn new(genome: &PyGenome) -> Self {
        Self { inner: MinimumOrganism::instantiate(genome.inner.clone()) }
    }

    /// Initialize (transition CREATED → INITIALIZED).
    fn initialize(&mut self) -> PyResult<()> {
        self.inner.initialize().map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
    }

    /// Begin development (INITIALIZED → DEVELOPING).
    fn begin_development(&mut self) -> PyResult<()> {
        self.inner.begin_development().map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
    }

    /// Run one tick against a ResourceWorld. Returns a dict with tick metadata.
    fn tick_resource(&mut self, env: &mut PyResourceWorld) -> PyResult<PyObject> {
        let tick = self.inner.tick(&mut env.inner);
        let tick_json = serde_json::to_value(&tick).unwrap_or(serde_json::Value::Null);
        Python::with_gil(|py| Ok(py_obj_from_json(&tick_json, py)))
    }

    /// Run one tick against a ChangingWorld.
    fn tick_changing(&mut self, env: &mut PyChangingWorld) -> PyResult<PyObject> {
        let tick = self.inner.tick(&mut env.inner);
        let tick_json = serde_json::to_value(&tick).unwrap_or(serde_json::Value::Null);
        Python::with_gil(|py| Ok(py_obj_from_json(&tick_json, py)))
    }

    /// State hash (short form, 12 chars).
    #[getter]
    fn state_hash(&self) -> String { self.inner.state.short_hash() }

    /// Step counter.
    #[getter]
    fn step(&self) -> u64 { self.inner.state.step }

    /// Total reward accumulated.
    #[getter]
    fn total_reward(&self) -> f64 { self.inner.state.total_reward }

    /// Current developmental stage as a string.
    #[getter]
    fn developmental_stage(&self) -> String {
        self.inner.state.developmental.developmental_stage.to_string()
    }

    /// Snapshot the full organism state to a JSON string.
    fn snapshot(&self) -> String {
        serde_json::to_string(&self.inner.snapshot()).unwrap_or_default()
    }

    /// Restore from a JSON snapshot.
    fn restore(&mut self, snapshot: &str) -> PyResult<()> {
        let v: serde_json::Value = serde_json::from_str(snapshot)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        self.inner.restore(&v).map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))
    }

    /// Genome hash.
    #[getter]
    fn genome_hash(&self) -> String { self.inner.genome.hash() }

    /// Take a checkpoint against a ResourceWorld (returns a JSON string).
    fn checkpoint_resource(&self, env: &PyResourceWorld, env_seed: u64, random_seed: u64, label: &str) -> PyResult<String> {
        let ck = MindCheckpoint::take(&self.inner, &env.inner, env_seed, random_seed, label);
        serde_json::to_string(&ck).map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }

    /// Take a checkpoint against a ChangingWorld.
    fn checkpoint_changing(&self, env: &PyChangingWorld, env_seed: u64, random_seed: u64, label: &str) -> PyResult<String> {
        let ck = MindCheckpoint::take(&self.inner, &env.inner, env_seed, random_seed, label);
        serde_json::to_string(&ck).map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }
}

/// Run the Same Genome / Different World experiment from Python.
///
/// Returns a JSON string with: trajectory_a, trajectory_b, divergence, manifest_a, manifest_b.
#[pyfunction]
#[pyo3(signature = (steps=200, env_a_seed=1, env_b_seed=999, width=6, height=6, genome_name="flagship".to_string()))]
fn run_same_genome_different_world(
    steps: usize,
    env_a_seed: u64,
    env_b_seed: u64,
    width: u32,
    height: u32,
    genome_name: String,
) -> PyResult<String> {
    let genome = DevelopmentalGenome::named(genome_name);
    let result = crate_runner::run_flagship(&genome, steps, env_a_seed, env_b_seed, width, height);
    serde_json::to_string_pretty(&result)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

/// Run a counterfactual "What if the environment had been different?" simulation.
///
/// Takes a checkpoint JSON (from a previous experiment), an alternative environment seed,
/// and the number of steps to simulate. Returns a JSON string with the counterfactual
/// trajectory + the divergence from the actual trajectory segment.
///
/// The counterfactual trajectory is marked with epistemic labels SIMULATED + COUNTERFACTUAL
/// and is NEVER executed in the real environment.
#[pyfunction]
#[pyo3(signature = (checkpoint_json, actual_trajectory_json, alt_env_seed, n_steps, width=6, height=6))]
fn run_counterfactual_environment(
    checkpoint_json: &str,
    actual_trajectory_json: &str,
    alt_env_seed: u64,
    n_steps: u64,
    width: u32,
    height: u32,
) -> PyResult<String> {
    let checkpoint: MindCheckpoint = serde_json::from_str(checkpoint_json)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("checkpoint: {}", e)))?;
    let actual: DevelopmentalTrajectory = serde_json::from_str(actual_trajectory_json)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("trajectory: {}", e)))?;

    let cs = CounterfactualSelf::new(checkpoint, actual);
    let mut alt_env = ResourceWorld::new(width, height, alt_env_seed);
    alt_env.reset();
    let cf = cs.what_if_environment(&mut alt_env, n_steps, alt_env_seed);
    let divergence = cs.compare_to_actual(&cf)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))?;

    let result = serde_json::json!({
        "counterfactual": cf,
        "divergence_from_actual": divergence,
    });
    serde_json::to_string_pretty(&result)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

/// Build a Possible-Self Space from a checkpoint + multiple alternative environment seeds.
///
/// Returns a JSON string with the possible-self space (current self, possible futures,
/// coverage, distances from current).
#[pyfunction]
#[pyo3(signature = (checkpoint_json, alt_env_seeds, n_steps, width=6, height=6))]
fn run_possible_self_space(
    checkpoint_json: &str,
    alt_env_seeds: Vec<u64>,
    n_steps: u64,
    width: u32,
    height: u32,
) -> PyResult<String> {
    let checkpoint: MindCheckpoint = serde_json::from_str(checkpoint_json)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("checkpoint: {}", e)))?;

    // Build a placeholder actual trajectory (empty) — the space only needs the checkpoint.
    let actual = DevelopmentalTrajectory::new(
        "placeholder",
        checkpoint.genome_hash.clone(),
        checkpoint.environment_hash.clone(),
        checkpoint.environment_seed,
    );
    let cs = CounterfactualSelf::new(checkpoint.clone(), actual);

    let mut space = PossibleSelfSpace::new(
        checkpoint.organism_state.developmental.clone(),
        checkpoint.hash(),
    );

    for seed in alt_env_seeds {
        let mut alt_env = ResourceWorld::new(width, height, seed);
        alt_env.reset();
        let cf = cs.what_if_environment(&mut alt_env, n_steps, seed);
        space.add_future(cf);
    }

    let distances = space.distances_from_current();
    let result = serde_json::json!({
        "space": space,
        "coverage": space.coverage(),
        "distances_from_current": distances,
    });
    serde_json::to_string_pretty(&result)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

/// Compute a MindDiff between two organism snapshots (JSON strings).
#[pyfunction]
fn mind_diff(state_a_json: &str, state_b_json: &str) -> PyResult<String> {
    let a: OrganismState = serde_json::from_str(state_a_json)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("state_a: {}", e)))?;
    let b: OrganismState = serde_json::from_str(state_b_json)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("state_b: {}", e)))?;
    let diff = MindDiff::between(&a, &b);
    serde_json::to_string_pretty(&diff)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

/// Run a metabolism budget sweep experiment.
///
/// For each budget value in `budget_values`, instantiate an organism with
/// a metabolism whose energy budget is set to that value, develop it for
/// `n_steps` in a ResourceWorld, and record the total reward + refusal count.
/// Returns a JSON string with the sweep results.
///
/// This demonstrates how resource constraints shape developmental trajectories.
#[pyfunction]
#[pyo3(signature = (budget_values, n_steps=60, env_seed=1, width=6, height=6, genome_name="metabolism_sweep".to_string()))]
fn run_metabolism_sweep(
    budget_values: Vec<f64>,
    n_steps: u64,
    env_seed: u64,
    width: u32,
    height: u32,
    genome_name: String,
) -> PyResult<String> {
    let genome = DevelopmentalGenome::named(genome_name);
    let mut results: Vec<serde_json::Value> = Vec::new();

    for &budget_val in &budget_values {
        let mut org = MinimumOrganism::instantiate(genome.clone());
        org.initialize().unwrap();
        org.begin_development().unwrap();
        let mut env = ResourceWorld::new(width, height, env_seed);
        env.reset();

        // Attach a metabolism with the given energy budget.
        let mut metabolism = CognitiveMetabolism::default();
        metabolism.budget.energy = budget_val;

        let mut total_reward = 0.0_f64;
        let mut refusals = 0_u64;

        for _ in 0..n_steps {
            metabolism.reset_tick();
            // Spend for perceive + predict.
            if metabolism.spend(CognitiveOperation::Perceive) {
                // ok
            }
            if metabolism.spend(CognitiveOperation::Predict) {
                // ok
            }
            let tick = org.tick(&mut env);
            total_reward += tick.reward;
            // Spend for the action.
            let _ = metabolism.spend(CognitiveOperation::Act);
            refusals = metabolism.refusals;
        }

        results.push(serde_json::json!({
            "energy_budget": budget_val,
            "total_reward": total_reward,
            "mean_reward": total_reward / n_steps as f64,
            "refusals": refusals,
            "final_state_hash": org.state.short_hash(),
        }));
    }

    let result = serde_json::json!({
        "experiment": "metabolism_sweep",
        "genome_hash": genome.hash(),
        "n_steps": n_steps,
        "env_seed": env_seed,
        "results": results,
    });
    serde_json::to_string_pretty(&result)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

/// Evaluate the value-of-information decision rule for a single operation.
///
/// Returns a JSON string with: { operation, cost, expected_info_gain, worth_it }.
#[pyfunction]
#[pyo3(signature = (operation, expected_info_gain))]
fn evaluate_value_of_information(
    operation: &str,
    expected_info_gain: f64,
) -> PyResult<String> {
    let op = match operation.to_lowercase().as_str() {
        "perceive" => CognitiveOperation::Perceive,
        "predict" => CognitiveOperation::Predict,
        "memorize" => CognitiveOperation::Memorize,
        "plan" => CognitiveOperation::Plan,
        "simulate" => CognitiveOperation::Simulate,
        "act" => CognitiveOperation::Act,
        "explore" => CognitiveOperation::Explore,
        "reduce_uncertainty" => CognitiveOperation::ReduceUncertainty,
        "take_risk" => CognitiveOperation::TakeRisk,
        _ => return Err(pyo3::exceptions::PyValueError::new_err(format!("unknown operation: {}", operation))),
    };
    let m = CognitiveMetabolism::default();
    let cost = m.cost_of(op);
    let worth_it = m.is_worth_it(expected_info_gain, op);
    let result = serde_json::json!({
        "operation": operation,
        "cost": cost,
        "expected_info_gain": expected_info_gain,
        "worth_it": worth_it,
    });
    serde_json::to_string_pretty(&result)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

/// Get the crate version.
#[pyfunction]
fn version() -> &'static str {
    VERSION
}

/// Run an aging comparison experiment.
///
/// Develops two organisms from the same genome: one with no aging, one with
/// the given aging model (as JSON). Returns a JSON string comparing their
/// final developmental states.
///
/// This demonstrates how accumulated computational history affects future cognition.
#[pyfunction]
#[pyo3(signature = (aging_model_json, n_steps=100, env_seed=1, width=6, height=6, genome_name="aging_demo".to_string()))]
fn run_aging_comparison(
    aging_model_json: &str,
    n_steps: u64,
    env_seed: u64,
    width: u32,
    height: u32,
    genome_name: String,
) -> PyResult<String> {
    let aging_model: AgingModel = serde_json::from_str(aging_model_json)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("aging_model: {}", e)))?;

    let genome = DevelopmentalGenome::named(genome_name);

    // Organism A: no aging
    let mut org_a = MinimumOrganism::instantiate(genome.clone());
    org_a.initialize().unwrap();
    org_a.begin_development().unwrap();
    let mut env_a = ResourceWorld::new(width, height, env_seed);
    env_a.reset();
    for _ in 0..n_steps {
        org_a.tick(&mut env_a);
    }

    // Organism B: with aging
    let mut org_b = MinimumOrganism::instantiate(genome.clone());
    org_b.initialize().unwrap();
    org_b.begin_development().unwrap();
    let mut env_b = ResourceWorld::new(width, height, env_seed);
    env_b.reset();
    for _ in 0..n_steps {
        org_b.tick(&mut env_b);
        aging_model.apply(&mut org_b.state.developmental);
    }

    let dev_a = &org_a.state.developmental;
    let dev_b = &org_b.state.developmental;

    let result = serde_json::json!({
        "experiment": "aging_comparison",
        "genome_hash": genome.hash(),
        "n_steps": n_steps,
        "env_seed": env_seed,
        "aging_model_hash": aging_model.hash(),
        "no_aging": {
            "plasticity": dev_a.plasticity,
            "stability": dev_a.stability,
            "energy_state": dev_a.energy_state,
            "cognitive_load": dev_a.cognitive_load,
            "memory_capacity": dev_a.memory_capacity,
            "prediction_accuracy": dev_a.prediction_accuracy,
            "self_model_stability": dev_a.self_model_stability,
            "state_hash": org_a.state.short_hash(),
        },
        "with_aging": {
            "plasticity": dev_b.plasticity,
            "stability": dev_b.stability,
            "energy_state": dev_b.energy_state,
            "cognitive_load": dev_b.cognitive_load,
            "memory_capacity": dev_b.memory_capacity,
            "prediction_accuracy": dev_b.prediction_accuracy,
            "self_model_stability": dev_b.self_model_stability,
            "state_hash": org_b.state.short_hash(),
        },
        "deltas": {
            "plasticity": dev_b.plasticity - dev_a.plasticity,
            "stability": dev_b.stability - dev_a.stability,
            "energy_state": dev_b.energy_state - dev_a.energy_state,
            "cognitive_load": dev_b.cognitive_load - dev_a.cognitive_load,
            "memory_capacity": dev_b.memory_capacity - dev_a.memory_capacity,
            "prediction_accuracy": dev_b.prediction_accuracy - dev_a.prediction_accuracy,
            "self_model_stability": dev_b.self_model_stability - dev_a.self_model_stability,
        },
    });
    serde_json::to_string_pretty(&result)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

fn parse_action(s: &str) -> PyResult<Action> {
    Ok(match s.to_lowercase().as_str() {
        "move_right" | "right" | "r" => Action::MoveRight,
        "move_left" | "left" | "l" => Action::MoveLeft,
        "move_up" | "up" | "u" => Action::MoveUp,
        "move_down" | "down" | "d" => Action::MoveDown,
        "idle" | "stay" | "i" => Action::Idle,
        "consume" | "c" => Action::Consume,
        _ => return Err(pyo3::exceptions::PyValueError::new_err(format!("unknown action: {}", s))),
    })
}

fn py_obj_from_json(v: &serde_json::Value, py: Python<'_>) -> PyObject {
    // Convert a serde_json::Value into a native Python object.
    use pyo3::types::{PyBool, PyDict, PyFloat, PyList, PyString};
    match v {
        serde_json::Value::Null => py.None(),
        serde_json::Value::Bool(b) => PyBool::new_bound(py, *b).to_object(py),
        serde_json::Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                i.to_object(py)
            } else if let Some(u) = n.as_u64() {
                u.to_object(py)
            } else {
                PyFloat::new_bound(py, n.as_f64().unwrap_or(0.0)).to_object(py)
            }
        }
        serde_json::Value::String(s) => PyString::new_bound(py, s).to_object(py),
        serde_json::Value::Array(arr) => {
            let list = PyList::empty_bound(py);
            for item in arr {
                list.append(py_obj_from_json(item, py)).ok();
            }
            list.to_object(py)
        }
        serde_json::Value::Object(map) => {
            let dict = PyDict::new_bound(py);
            for (k, val) in map {
                let _ = dict.set_item(k, py_obj_from_json(val, py));
            }
            dict.to_object(py)
        }
    }
}

/// Python module definition. The module is exposed as `nuros._dev`.
#[pymodule]
fn _dev(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyGenome>()?;
    m.add_class::<PyResourceWorld>()?;
    m.add_class::<PyChangingWorld>()?;
    m.add_class::<PyOrganism>()?;
    m.add_function(wrap_pyfunction!(run_same_genome_different_world, m)?)?;
    m.add_function(wrap_pyfunction!(run_counterfactual_environment, m)?)?;
    m.add_function(wrap_pyfunction!(run_possible_self_space, m)?)?;
    m.add_function(wrap_pyfunction!(mind_diff, m)?)?;
    m.add_function(wrap_pyfunction!(run_metabolism_sweep, m)?)?;
    m.add_function(wrap_pyfunction!(evaluate_value_of_information, m)?)?;
    m.add_function(wrap_pyfunction!(run_aging_comparison, m)?)?;
    m.add_function(wrap_pyfunction!(version, m)?)?;
    Ok(())
}

// ============================================================================
// Internal: flagship experiment runner (also used by the Python binding).
// ============================================================================

mod crate_runner {
    use super::*;
    use serde::Serialize;
    use std::collections::BTreeMap;

    #[derive(Serialize)]
    pub struct FlagshipResult {
        pub genome_hash: String,
        pub genome_short_hash: String,
        pub trajectory_a: serde_json::Value,
        pub trajectory_b: serde_json::Value,
        pub divergence: serde_json::Value,
        pub manifest_a: serde_json::Value,
        pub manifest_b: serde_json::Value,
        pub summary: BTreeMap<String, String>,
    }

    pub fn run_flagship(
        genome: &DevelopmentalGenome,
        steps: usize,
        env_a_seed: u64,
        env_b_seed: u64,
        width: u32,
        height: u32,
    ) -> FlagshipResult {
        let genome_hash = genome.hash();

        // Run organism A in environment A.
        let mut org_a = MinimumOrganism::instantiate(genome.clone());
        org_a.initialize().unwrap();
        org_a.begin_development().unwrap();
        let mut env_a = ResourceWorld::new(width, height, env_a_seed);
        env_a.reset();
        let env_a_hash = env_a.hash();
        let mut traj_a = DevelopmentalTrajectory::new("organism_a", genome_hash.clone(), env_a_hash.clone(), env_a_seed);
        for _ in 0..steps {
            let tick = org_a.tick(&mut env_a);
            traj_a.record(&tick, &org_a.state.developmental);
        }
        let ck_a = MindCheckpoint::take(&org_a, &env_a, env_a_seed, 0, "final_a");

        // Run organism B in environment B (same genome, different seed).
        let mut org_b = MinimumOrganism::instantiate(genome.clone());
        org_b.initialize().unwrap();
        org_b.begin_development().unwrap();
        let mut env_b = ResourceWorld::new(width, height, env_b_seed);
        env_b.reset();
        let env_b_hash = env_b.hash();
        let mut traj_b = DevelopmentalTrajectory::new("organism_b", genome_hash.clone(), env_b_hash.clone(), env_b_seed);
        for _ in 0..steps {
            let tick = org_b.tick(&mut env_b);
            traj_b.record(&tick, &org_b.state.developmental);
        }
        let ck_b = MindCheckpoint::take(&org_b, &env_b, env_b_seed, 0, "final_b");

        // Compute divergence.
        let divergence = DevelopmentalDivergence::between(&traj_a, &traj_b).unwrap();

        // Build manifests.
        let cfg = serde_json::json!({
            "experiment": "same_genome_different_world",
            "genome_name": genome.name,
            "steps": steps,
            "env_a_seed": env_a_seed,
            "env_b_seed": env_b_seed,
            "width": width,
            "height": height,
        });
        let man_a = ReproducibilityManifest::build(
            "organism_a", genome_hash.clone(), env_a_hash.clone(),
            crate::hash::hash(&cfg), 0, env_a_seed, &ck_a, &cfg, steps as u64,
        );
        let man_b = ReproducibilityManifest::build(
            "organism_b", genome_hash.clone(), env_b_hash.clone(),
            crate::hash::hash(&cfg), 0, env_b_seed, &ck_b, &cfg, steps as u64,
        );

        // Summary strings.
        let mut summary = BTreeMap::new();
        summary.insert("genome_hash".to_string(), genome_hash.clone());
        summary.insert("n_steps".to_string(), steps.to_string());
        summary.insert("env_a_hash".to_string(), env_a_hash.clone());
        summary.insert("env_b_hash".to_string(), env_b_hash.clone());
        summary.insert("env_a_seed".to_string(), env_a_seed.to_string());
        summary.insert("env_b_seed".to_string(), env_b_seed.to_string());
        summary.insert("divergence_mean_state_distance".to_string(), format!("{:.4}", divergence.mean_state_distance));
        summary.insert("divergence_action_distance".to_string(), format!("{}", divergence.action_distance));
        summary.insert("divergence_reward_distance".to_string(), format!("{:.4}", divergence.reward_distance));
        summary.insert("divergence_stage_divergence".to_string(), divergence.stage_divergence.to_string());

        FlagshipResult {
            genome_hash: genome_hash.clone(),
            genome_short_hash: crate::hash::short_hash(&genome_hash),
            trajectory_a: serde_json::to_value(&traj_a).unwrap_or(serde_json::Value::Null),
            trajectory_b: serde_json::to_value(&traj_b).unwrap_or(serde_json::Value::Null),
            divergence: serde_json::to_value(&divergence).unwrap_or(serde_json::Value::Null),
            manifest_a: serde_json::to_value(&man_a).unwrap_or(serde_json::Value::Null),
            manifest_b: serde_json::to_value(&man_b).unwrap_or(serde_json::Value::Null),
            summary,
        }
    }
}
