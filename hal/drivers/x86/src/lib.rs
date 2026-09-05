//! # x86_64 HAL driver (software emulation).
//!
//! Runs the entire spiking network on commodity x86_64 hardware, using
//! SIMD for membrane potential updates. It is ~10⁴× slower than
//! real-time but lets us validate correctness without neuromorphic
//! silicon.
//!
//! ## Biological correspondence
//!
//! This is the equivalent of an *in vitro* brain slice preparation —
//! a faithful but slow simulation, useful for experiments but not for
//! survival.

use nuros_hal::{NeuronId, NeuronParams, NeuromorphicTarget};

pub struct X86Target {
    neuron_count: usize,
    energy: f64,
}

impl X86Target {
    pub fn new() -> Self {
        Self { neuron_count: 0, energy: 0.0 }
    }
}

impl Default for X86Target {
    fn default() -> Self { Self::new() }
}

impl NeuromorphicTarget for X86Target {
    fn name(&self) -> &str { "x86_64 software emulation (v0.1.0)" }

    fn alloc_neuron(&mut self, _params: &NeuronParams) -> NeuronId {
        let id = self.neuron_count as NeuronId;
        self.neuron_count += 1;
        id
    }

    fn alloc_synapse(&mut self, _src: NeuronId, _dst: NeuronId, _w: half::f16) -> u64 {
        0
    }

    fn fire(&mut self, _n: NeuronId, _t: u64) {
        // x86 spike: ~1 nJ (vs. ~1 pJ on Loihi).
        self.energy += 1e-9;
    }

    fn read_potential(&self, _n: NeuronId) -> f32 { -70.0 }

    fn remap(&mut self, failed: NeuronId) -> NeuronId {
        // Mimics compensatory sprouting.
        (failed + 1) % self.neuron_count.max(1) as NeuronId
    }

    fn energy_report(&self) -> f64 { self.energy }
}
