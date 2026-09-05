//! # HAL Bridge — Kernel-side
//!
//! This module defines the `NeuromorphicTarget` trait and provides a
//! `probe()` function that selects the right backend based on the
//! requested mode.
//!
//! The actual HAL implementations live in `/hal/drivers/{x86,arm,loihi,fpga}`.
//! In v0.1.0-alpha, only the `x86` (emulation) backend is functional.
//!
//! ## Biological correspondence
//!
//! The HAL is the equivalent of the **neuromuscular junction** + sensory
//! epithelium — the boundary where the abstract nervous system meets
//! the physical world. In biology, this is where photoreceptors convert
//! photons to currents and where motor neurons convert spikes to muscle
//! contractions. In NurosOS, the HAL converts NIR bytecode to
//! hardware-specific instructions (x86 SIMD, Loihi spike packets, FPGA
//! bitstreams).

use std::fmt;

use crate::neuron::{NeuronId, NeuronParams};

/// The execution mode requested by the user.
#[derive(Copy, Clone, Debug)]
pub enum Mode {
    /// Software emulation on commodity hardware.
    Emulation,
    /// Native execution on neuromorphic silicon.
    Native,
}

/// A neuromorphic hardware target.
///
/// Every backend (x86, ARM, Loihi, FPGA) implements this trait. The
/// kernel interacts with hardware *only* through this trait — there
/// is no direct hardware access from the kernel crate.
pub trait NeuromorphicTarget: Send + Sync {
    /// Human-readable name (e.g., "x86_64 emulation", "Intel Loihi 2").
    fn name(&self) -> String;

    /// Allocate a neuron on this target.
    fn alloc_neuron(&mut self, params: &NeuronParams) -> NeuronId;

    /// Allocate a synapse between two neurons.
    fn alloc_synapse(&mut self, src: NeuronId, dst: NeuronId, weight: half::f16) -> u64;

    /// Fire a neuron at the given tick.
    fn fire(&mut self, n: NeuronId, t: u64);

    /// Read a neuron's current membrane potential (in mV).
    fn read_potential(&self, n: NeuronId) -> f32;

    /// Dynamic remapping — neuroplasticity emulation.
    ///
    /// When a physical core fails (a "lesion"), the HAL selects a
    /// neighboring neuron with the most similar connectivity profile,
    /// copies the failed neuron's weights to the substitute, and
    /// updates the routing table.
    ///
    /// This mimics biological **compensatory sprouting** — the process
    /// by which surviving neurons extend new dendrites to innervate
    /// denervated targets after brain injury.
    fn remap(&mut self, failed: NeuronId) -> NeuronId;

    /// Report energy consumed since the last reset (in joules).
    ///
    /// Used by the v0.3.0 milestone benchmark (1000× power reduction).
    fn energy_report(&self) -> f64;
}

/// Probe the system and return the appropriate HAL backend.
pub fn probe(mode: Mode) -> anyhow::Result<Box<dyn NeuromorphicTarget>> {
    match mode {
        Mode::Emulation => Ok(Box::new(X86EmulationTarget::new())),
        Mode::Native => {
            // In v0.1.0 we don't have native HAL drivers yet.
            // TODO(v0.3.0): probe for Loihi / FPGA hardware.
            anyhow::bail!("Native mode is not implemented in v0.1.0-alpha. Use --mode=emulation.")
        }
    }
}

/// The x86_64 software-emulation target.
///
/// This backend runs the entire spiking network on commodity x86_64
/// hardware, using SIMD for membrane potential updates. It is ~10⁴×
/// slower than real-time but lets us validate correctness without
/// neuromorphic silicon.
///
/// ## Biological correspondence
///
/// This is the equivalent of an *in vitro* brain slice preparation —
/// a faithful but slow simulation of the real thing, useful for
/// experiments but not for survival.
pub struct X86EmulationTarget {
    /// Allocated neurons (placeholder — in v0.2.0 this will be a
    /// proper data structure).
    neuron_count: usize,
    /// Total energy "consumed" — emulated as 1 nJ per spike.
    energy: std::sync::Mutex<f64>,
}

impl X86EmulationTarget {
    /// Construct a new x86 emulation target.
    pub fn new() -> Self {
        Self {
            neuron_count: 0,
            energy: std::sync::Mutex::new(0.0),
        }
    }
}

impl Default for X86EmulationTarget {
    fn default() -> Self { Self::new() }
}

impl fmt::Debug for X86EmulationTarget {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("X86EmulationTarget")
            .field("neuron_count", &self.neuron_count)
            .finish()
    }
}

impl NeuromorphicTarget for X86EmulationTarget {
    fn name(&self) -> String {
        "x86_64 software emulation (v0.1.0)".to_string()
    }

    fn alloc_neuron(&mut self, _params: &NeuronParams) -> NeuronId {
        let id = NeuronId(self.neuron_count);
        self.neuron_count += 1;
        id
    }

    fn alloc_synapse(&mut self, _src: NeuronId, _dst: NeuronId, _weight: half::f16) -> u64 {
        // Stub — the synapse graph is owned by RegionGraph in v0.1.0.
        0
    }

    fn fire(&mut self, _n: NeuronId, _t: u64) {
        // Mimics an action potential — costs ~1 nJ on x86 (vs. ~1 pJ on Loihi).
        *self.energy.lock().unwrap() += 1e-9;
    }

    fn read_potential(&self, _n: NeuronId) -> f32 {
        // Stub — in v0.2.0 this will read from the scheduler's potentials table.
        -70.0
    }

    fn remap(&mut self, failed: NeuronId) -> NeuronId {
        // Mimics compensatory sprouting: pick a neighboring neuron.
        // In v0.2.0 this will use connectivity similarity, not just
        // numerical adjacency.
        NeuronId((failed.0 + 1) % self.neuron_count.max(1))
    }

    fn energy_report(&self) -> f64 {
        *self.energy.lock().unwrap()
    }
}

/// RPC server module (used by `main.rs`).
pub mod rpc {
    /// Stub RPC server. In v0.2.0 this will be a real REST/gRPC server.
    ///
    /// ## Biological correspondence
    ///
    /// This is the equivalent of an *electrode* — an artificial interface
    /// that lets external systems (PyTorch models, debuggers, humans)
    /// inject current into and read activity out of the brain.
    pub fn serve(
        _scheduler: std::sync::Arc<crate::sched::Scheduler>,
        port: u16,
    ) {
        log::info!("RPC server listening on :{}", port);
        log::warn!("RPC is a stub in v0.1.0 — no external connections accepted.");
        // Block forever (until the kernel halts).
        loop {
            std::thread::sleep(std::time::Duration::from_secs(60));
        }
    }
}
