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

pub use nuros_hal_api::{NeuromorphicTarget, NeuronId, NeuronParams};

// Re-export driver crates when their features are enabled.
#[cfg(feature = "x86")]
pub use nuros_hal_x86::X86Target;

#[cfg(feature = "arm")]
pub use nuros_hal_arm::ArmTarget;

#[cfg(feature = "loihi")]
pub use nuros_hal_loihi::LoihiTarget;

#[cfg(feature = "fpga")]
pub use nuros_hal_fpga::FpgaTarget;
