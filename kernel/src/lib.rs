//! # NurosOS Kernel — Library Entry Point
//!
//! This crate implements the microkernel described in `ARCHITECTURE.md`.
//! It is organized as a library so that integration tests (in `/tests`)
//! can import individual subsystems without spawning a full OS process.
//!
//! ## Module map
//!
//! | Module      | Responsibility                                                |
//! |-------------|---------------------------------------------------------------|
//! | [`sched`]   | Event-driven neuron scheduler (the Sparse Propagation Protocol) |
//! | [`ipc`]     | Zero-copy synaptic channels (lock-free ring buffers)          |
//! | [`mem`]     | Associative Memory Store (AMS) — replaces the filesystem      |
//! | [`neuron`]  | Core neuron model trait + LIF implementation                  |
//! | [`synapse`] | Synapse types, plasticity rules (STDP)                        |
//! | [`region`]  | Topological grouping of neurons (a "neuropil")                |
//! | [`hal`]     | Hardware Abstraction Layer bridge                             |
//! | [`connectome`] | Loader for the Drosophila connectome dataset              |

#![deny(missing_docs)]
#![deny(clippy::all)]
#![warn(clippy::pedantic)]

pub mod sched;
pub mod ipc;
pub mod mem;
pub mod neuron;
pub mod synapse;
pub mod region;
pub mod hal;
pub mod connectome;

/// Semantic version of the kernel ABI.
/// Any change to the on-disk NIR format MUST bump this.
pub const ABI_VERSION: &str = "0.1.0";

/// The maximum fraction of neurons that may be active in a single tick.
///
/// This enforces Invariant I1 (Sparsity) from `ARCHITECTURE.md` §1.2.
/// The 5% figure matches the observed simultaneous activation rate in the
/// *Drosophila* central complex during walking behavior (~4.2%, measured
/// by two-photon calcium imaging).
pub const SPARSITY_THRESHOLD: f32 = 0.05;

/// The duration of one kernel tick, in milliseconds (biological time).
///
/// This is *not* wall-clock time — it is the simulated biological time
/// elapsed per scheduler iteration. The mapping to wall-clock depends on
/// the HAL target (1× for real-time Loihi, ~10⁻⁴× for x86 emulation).
pub const TICK_MS: f32 = 1.0;
