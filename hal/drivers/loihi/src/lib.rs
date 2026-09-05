//! # Intel Loihi HAL driver.
//!
//! Targets Intel Loihi 1 / Loihi 2 neuromorphic research chips. This
//! is the **target backend** for the v0.3.0 milestone (1000× power
//! reduction for pattern recognition).
//!
//! ## Biological correspondence
//!
//! Loihi is the closest commercially-available hardware to biological
//! neural tissue: it has on-chip learning, event-driven spiking, and
//! operates at picojoule-per-spike energy. Running NurosOS on Loihi
//! is the equivalent of moving from an *in vitro* simulation to an
//! *in vivo* preparation — the dynamics become real-time.
//!
//! ## Status
//!
//! v0.1.0: stub. The actual Loihi SDK integration is scheduled for v0.3.0.
//! See `docs/adr/0005-loihi-integration.md` (planned).

use nuros_hal::{NeuronId, NeuronParams, NeuromorphicTarget};

pub struct LoihiTarget {
    neuron_count: usize,
    energy: f64,
}

impl LoihiTarget {
    pub fn new() -> Self {
        Self { neuron_count: 0, energy: 0.0 }
    }
}

impl Default for LoihiTarget {
    fn default() -> Self { Self::new() }
}

impl NeuromorphicTarget for LoihiTarget {
    fn name(&self) -> &str { "Intel Loihi 2 (v0.3.0 stub)" }

    fn alloc_neuron(&mut self, _: &NeuronParams) -> NeuronId {
        let id = self.neuron_count as NeuronId;
        self.neuron_count += 1;
        id
    }

    fn alloc_synapse(&mut self, _: NeuronId, _: NeuronId, _: half::f16) -> u64 { 0 }
    fn fire(&mut self, _: NeuronId, _: u64) { self.energy += 1e-12; }  // ~1 pJ
    fn read_potential(&self, _: NeuronId) -> f32 { -70.0 }
    fn remap(&mut self, failed: NeuronId) -> NeuronId { (failed + 1) % self.neuron_count.max(1) as NeuronId }
    fn energy_report(&self) -> f64 { self.energy }
}
