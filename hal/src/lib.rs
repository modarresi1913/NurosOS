//! # NurosOS Hardware Abstraction Layer (HAL)
//!
//! This crate defines the unified driver interface for neuromorphic
//! silicon (Intel Loihi, IBM TrueNorth, custom FPGA arrays, and x86
//! emulation). It is consumed by the kernel via the `hal` module.
//!
//! ## Biological correspondence
//!
//! The HAL is the equivalent of the **neuromuscular junction** + the
//! **sensory epithelium** — the boundary where the abstract nervous
//! system meets the physical world. In biology:
//!
//! - Photoreceptors convert photons → receptor potentials.
//! - Motor neurons convert spikes → muscle contractions.
//! - Mechanoreceptors convert pressure → receptor potentials.
//!
//! In NurosOS, the HAL converts abstract NIR bytecode → hardware-specific
//! instructions (x86 SIMD, Loihi spike packets, FPGA bitstream reconfig).

#![deny(missing_docs)]

pub mod energy;

/// A globally-unique neuron identifier (re-exported from the kernel).
pub type NeuronId = u32;

/// A neuromorphic hardware target.
///
/// Every backend (x86, ARM, Loihi, FPGA) implements this trait. The
/// kernel interacts with hardware *only* through this trait.
pub trait NeuromorphicTarget: Send + Sync {
    /// Human-readable name (e.g., "x86_64 emulation", "Intel Loihi 2").
    fn name(&self) -> &str;

    /// Allocate a neuron with the given parameters.
    ///
    /// Returns the neuron's ID. This ID is stable for the lifetime of
    /// the kernel (a neuron is never deleted — only lesioned, in which
    /// case `remap()` is called).
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
    /// This mimics biological **compensatory sprouting**.
    fn remap(&mut self, failed: NeuronId) -> NeuronId;

    /// Report energy consumed since the last reset (in joules).
    fn energy_report(&self) -> f64;
}

/// Generic neuron parameter bundle.
#[derive(Clone, Copy, Debug, Default)]
pub struct NeuronParams {
    /// Membrane time constant (ms).
    pub tau_m: f32,
    /// Spike threshold (mV).
    pub theta: f32,
    /// Resting potential (mV).
    pub v_rest: f32,
    /// Reset potential (mV).
    pub v_reset: f32,
    /// Refractory period (ms).
    pub tau_refrac: f32,
}

// Re-export driver crates when their features are enabled.
#[cfg(feature = "x86")]
pub use nuros_hal_x86::X86Target;

#[cfg(feature = "arm")]
pub use nuros_hal_arm::ArmTarget;

#[cfg(feature = "loihi")]
pub use nuros_hal_loihi::LoihiTarget;

#[cfg(feature = "fpga")]
pub use nuros_hal_fpga::FpgaTarget;
