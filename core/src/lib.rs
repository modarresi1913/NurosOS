//! # NurosOS Core — Neural Network Algorithms
//!
//! This crate contains the biologically-detailed neuron models and
//! plasticity rules that the kernel invokes during SPP ticks. The
//! kernel provides the *scaffolding* (scheduler, IPC, HAL); this
//! crate provides the *biology* (LIF dynamics, STDP, Hebbian learning).
//!
//! ## Module map
//!
//! | Module         | Contents                                                |
//! |----------------|---------------------------------------------------------|
//! | [`models`]     | Neuron models (LIF, Izhikevich — planned)               |
//! | [`plasticity`] | Synaptic plasticity rules (Hebbian, STDP, dopamine-mod) |
//! | [`delays`]     | Axonal delay modeling                                   |

#![deny(missing_docs)]

pub mod models;
pub mod plasticity;
pub mod delays;

/// Re-export the most commonly used types.
pub use models::{LeakyIntegrateAndFire, NeuronModel, StepResult};
pub use plasticity::{HebbianRule, StdpRule, PlasticityRule};
