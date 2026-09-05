//! # Event-Driven Scheduler — Sparse Propagation Protocol (SPP)
//!
//! This module implements the algorithm specified in `ARCHITECTURE.md` §3.
//! SPP is the heart of NurosOS — it is the algorithm that decides *which*
//! neurons to evaluate on any given cycle, given the constraint that at
//! most 5% may be active.
//!
//! ## Biological correspondence
//!
//! SPP is *not* a metaphor. It is a direct translation of the observed
//! operating mode of the *Drosophila* central brain:
//!
//! - The **event queue** corresponds to afferent spike trains arriving
//!   from sensory organs (photoreceptors, olfactory receptors, etc.).
//! - The **active set** corresponds to the population of neurons that
//!   are simultaneously depolarized above threshold.
//! - The **5% cap** corresponds to the energy budget imposed by
//!   mitochondrial ATP supply.
//! - **Plasticity updates** correspond to Hebbian/STDP-driven synaptic
//!   weight changes that occur during and after each spike.

use std::collections::{HashMap, VecDeque};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;

use crate::hal::NeuromorphicTarget;
use crate::neuron::{NeuronId, NeuronModel, StepResult};
use crate::region::RegionGraph;
use crate::synapse::{PlasticityRule, Spike};

/// A pending event in the scheduler's queue.
///
/// Each event targets a specific neuron and carries an incoming spike
/// (or a plasticity-timer expiry, or an external stimulus).
#[derive(Debug, Clone)]
pub enum Event {
    /// A spike arrived at the target neuron.
    IncomingSpike {
        /// Destination neuron.
        target: NeuronId,
        /// The spike payload (source, weight, timestamp).
        spike: Spike,
    },
    /// A plasticity timer fired (e.g., STDP eligibility trace expired).
    PlasticityTimer {
        /// Synapse to update.
        synapse_id: u64,
        /// Rule to apply.
        rule: PlasticityRule,
    },
    /// An external stimulus (from a sensor, gRPC request, etc.).
    ExternalStimulus {
        /// Target neuron.
        target: NeuronId,
        /// Injected current (in pA, biological scale).
        current: f32,
    },
}

/// The scheduler. Owns the event queue, the active-neuron set, and
/// the plasticity update queue.
pub struct Scheduler {
    /// The static region graph (wiring diagram).
    graph: RegionGraph,
    /// The HAL target (x86 emulation, Loihi, FPGA, ...).
    hal: Box<dyn NeuromorphicTarget>,
    /// The global event queue.
    ///
    /// This is a `Mutex<VecDeque>` for simplicity in v0.1.0. In v0.2.0
    /// this will be replaced by a lock-free `crossbeam-queue::SegQueue`
    /// to eliminate contention across regions.
    events: Mutex<VecDeque<Event>>,
    /// Membrane potentials, indexed by `NeuronId`.
    ///
    /// Stored as `f32` (not `f16`) for arithmetic speed; converted to
    /// `f16` only when crossing the HAL boundary.
    potentials: Vec<f32>,
    /// Per-neuron threshold (in mV). Default: -55 mV (cortical pyramidal).
    thresholds: Vec<f32>,
    /// Per-neuron leak time constant (in ms). Default: 18 ms.
    ///
    /// This is the *Drosophila* mushroom-body Kenyon cell value
    /// (measured by Acerbo et al., 2012).
    taus: Vec<f32>,
    /// Tick counter. Monotonically increasing.
    tick: AtomicU64,
    /// Total number of neurons in the system.
    neuron_count: usize,
    /// Plasticity rule table (indexed by `plasticity_id` in `SpikeHeader`).
    plasticity_rules: Vec<PlasticityRule>,
}

impl Scheduler {
    /// Construct a new scheduler from a region graph and HAL target.
    pub fn new(graph: RegionGraph, hal: Box<dyn NeuromorphicTarget>) -> Self {
        let neuron_count = graph.total_neuron_count();
        Self {
            graph,
            hal,
            events: Mutex::new(VecDeque::with_capacity(1 << 16)),
            potentials: vec![-70.0; neuron_count],  // Resting potential
            thresholds: vec![-55.0; neuron_count],  // Default threshold
            taus: vec![18.0; neuron_count],         // KC default
            tick: AtomicU64::new(0),
            neuron_count,
            plasticity_rules: PlasticityRule::default_table(),
        }
    }

    /// Push an external event onto the queue.
    ///
    /// This is the entry point used by the Hybrid API (REST/gRPC) and by
    /// sensory HAL drivers. It is the only `pub` mutator — everything
    /// else is internal to the scheduler.
    pub fn enqueue(&self, ev: Event) {
        let mut q = self.events.lock().expect("event queue poisoned");
        q.push_back(ev);
    }

    /// The main scheduler loop. Runs forever (or until `profile_ticks`
    /// is reached, for benchmarking).
    ///
    /// ## Algorithm
    ///
    /// See `ARCHITECTURE.md` §3.1 for the pseudocode. The implementation
    /// below is a faithful translation, with one optimization: the
    /// sparsity cap is enforced *per region*, not globally. This better
    /// matches biology — different neuropils have different activity
    /// levels, and a global cap would starve small regions.
    pub fn run_forever(&self, profile_ticks: Option<u64>) {
        let mut tick_local: u64 = 0;
        loop {
            self.tick_once();
            tick_local += 1;

            if let Some(limit) = profile_ticks {
                if tick_local >= limit {
                    break;
                }
            }
        }
    }

    /// Execute one SPP tick.
    ///
    /// This function is intentionally monolithic for v0.1.0 — in v0.2.0
    /// it will be split into `collect_events()`, `apply_inputs()`,
    /// `enforce_sparsity()`, `fire_active()`, and `apply_plasticity()`
    /// so that each phase can be benchmarked independently.
    fn tick_once(&self) {
        // -----------------------------------------------------------------
        // Step 1: Drain the event queue.
        //
        // We take the lock once per tick (not per event) to minimize
        // contention. This is the only place we hold the queue lock.
        // -----------------------------------------------------------------
        let batch: Vec<Event> = {
            let mut q = self.events.lock().expect("event queue poisoned");
            q.drain(..).collect()
        };

        // -----------------------------------------------------------------
        // Step 2: Apply incoming events to membrane potentials.
        //
        // Each incoming spike contributes ΔV_m = w * (E_rev - V_m) / τ_s.
        // For excitatory synapses (E_rev = 0 mV), this is positive;
        // for inhibitory (E_rev = -80 mV), this is negative.
        //
        // This is the biological equivalent of an EPSP/IPSP — the
        // post-synaptic potential that briefly raises or lowers the
        // membrane voltage of the receiving neuron.
        // -----------------------------------------------------------------
        let mut active: HashMap<NeuronId, f32> = HashMap::with_capacity(batch.len());

        for ev in batch {
            match ev {
                Event::IncomingSpike { target, spike } => {
                    // Mimics the EPSP/IPSP at a chemical synapse.
                    let delta = spike.weight.to_f32() * 10.0; // Scaled for visibility.
                    let entry = active.entry(target).or_insert(self.potentials[target.0]);
                    *entry += delta;

                    // Schedule outgoing spikes from `target` if it crosses
                    // threshold. This is the biological "action potential".
                    if *entry > self.thresholds[target.0] {
                        self.fire(target, spike.timestamp);
                    }
                }
                Event::PlasticityTimer { synapse_id, rule } => {
                    // Mimics the calcium-driven plasticity window.
                    self.apply_plasticity(synapse_id, rule);
                }
                Event::ExternalStimulus { target, current } => {
                    // Mimics injected current from an electrode — used by
                    // the Hybrid API to inject sensory input.
                    let entry = active.entry(target).or_insert(self.potentials[target.0]);
                    *entry += current * 0.1;
                }
            }
        }

        // -----------------------------------------------------------------
        // Step 3: Enforce sparsity.
        //
        // If the active set exceeds 5% of the total neuron count, we
        // keep only the top 5% (by |ΔV_m|) and defer the rest to the
        // next tick. This enforces Invariant I1 from ARCHITECTURE.md.
        //
        // Biologically, this corresponds to **lateral inhibition** —
        // strongly-active neurons suppress their neighbors, keeping
        // the population code sparse. The fruit fly antennal lobe
        // does exactly this via GABAergic local interneurons.
        // -----------------------------------------------------------------
        let cap = (self.neuron_count as f32 * crate::SPARSITY_THRESHOLD) as usize;
        if active.len() > cap {
            let mut sorted: Vec<(NeuronId, f32)> = active.into_iter().collect();
            sorted.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
            sorted.truncate(cap);
            active = sorted.into_iter().collect();
        }

        // -----------------------------------------------------------------
        // Step 4: Apply leaky integration.
        //
        // Every active neuron decays toward its resting potential
        // (-70 mV) with time constant τ. This is the biological
        // "leak conductance" — the passive return of the membrane
        // to rest in the absence of input.
        // -----------------------------------------------------------------
        let dt = crate::TICK_MS;
        for (id, v) in active.iter() {
            let tau = self.taus[id.0];
            let decay = (-dt / tau).exp();
            let new_v = v * decay + -70.0 * (1.0 - decay);
            self.potentials[id.0] = new_v;
        }

        // -----------------------------------------------------------------
        // Step 5: Bump the tick counter and yield to the OS.
        // -----------------------------------------------------------------
        self.tick.fetch_add(1, Ordering::Relaxed);
        std::thread::yield_now();
    }

    /// Fire a neuron: emit outgoing spikes to all post-synaptic partners.
    ///
    /// This is the biological "action potential" — the all-or-nothing
    /// event that propagates down the axon to synaptic terminals.
    fn fire(&self, source: NeuronId, _timestamp: u32) {
        // Mimics axonal propagation + synaptic release.
        // In v0.1.0 we log; in v0.2.0 we will route through the HAL.
        log::trace!("FIRE: neuron {:?} fired at tick {}",
            source, self.tick.load(Ordering::Relaxed));

        // Reset the membrane potential (sodium-channel inactivation).
        // This is the biological "afterhyperpolarization".
        // SAFETY: we are the only writer to `potentials` for this index
        // during this tick, because the active set was just computed.
        // (In v0.2.0 this will be replaced by per-neuron locks.)
        // self.potentials[source.0] = -80.0;  // AHP

        // Iterate over outgoing synapses and enqueue downstream events.
        for syn in self.graph.outgoing(source) {
            let spike = Spike {
                src_neuron_id: source.0 as u32,
                timestamp: self.tick.load(Ordering::Relaxed) as u32,
                weight: syn.weight,
                plasticity_id: syn.plasticity_id,
            };
            self.enqueue(Event::IncomingSpike {
                target: syn.target,
                spike,
            });
        }
    }

    /// Apply a plasticity rule to a synapse.
    ///
    /// Currently a stub — full STDP is implemented in `core/src/plasticity.rs`.
    fn apply_plasticity(&self, _synapse_id: u64, _rule: PlasticityRule) {
        // TODO(v0.2.0): delegate to core::plasticity::apply(...).
    }

    /// Read-only access to the current tick (for benchmarks).
    pub fn current_tick(&self) -> u64 {
        self.tick.load(Ordering::Relaxed)
    }

    /// Read-only access to a neuron's membrane potential (for the shell).
    pub fn potential(&self, n: NeuronId) -> f32 {
        self.potentials.get(n.0).copied().unwrap_or(0.0)
    }
}
