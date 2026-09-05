//! # Energy instrumentation for the HAL.
//!
//! Every HAL driver must report energy consumption per tick. This is
//! how we validate the v0.3.0 milestone (1000× power reduction for
//! pattern recognition vs. traditional GPUs).
//!
//! ## Biological correspondence
//!
//! This is the equivalent of **mitochondrial ATP monitoring** — the
//! cell's mechanism for tracking energy expenditure. In biology, this
//! feedback drives metabolic homeostasis. In NurosOS, it drives
//! scheduler decisions (the SPP sparsity cap is fundamentally an
//! energy budget).

use std::sync::atomic::{AtomicU64, Ordering};

/// A thread-safe energy meter.
///
/// Implemented as a simple atomic counter that accumulates picojoules.
/// Each driver reports its own consumption; the kernel aggregates.
pub struct EnergyMeter {
    /// Total energy consumed, in picojoules.
    picojoules: AtomicU64,
}

impl EnergyMeter {
    /// Construct a new meter, initialized to zero.
    pub fn new() -> Self {
        Self { picojoules: AtomicU64::new(0) }
    }

    /// Record `pj` picojoules of energy consumption.
    pub fn record_pj(&self, pj: u64) {
        self.picojoules.fetch_add(pj, Ordering::Relaxed);
    }

    /// Record `nj` nanojoules of energy consumption.
    pub fn record_nj(&self, nj: f64) {
        let pj = (nj * 1000.0) as u64;
        self.record_pj(pj);
    }

    /// Total energy consumed, in joules.
    pub fn joules(&self) -> f64 {
        self.picojoules.load(Ordering::Relaxed) as f64 * 1e-12
    }

    /// Reset the meter to zero.
    pub fn reset(&self) {
        self.picojoules.store(0, Ordering::Relaxed);
    }
}

impl Default for EnergyMeter {
    fn default() -> Self { Self::new() }
}
