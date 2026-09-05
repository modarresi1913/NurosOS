# ADR 0002: Rust over C++ for the kernel

## Status
Accepted

## Context
The kernel needs:
- Zero-cost abstractions (for picojoule-scale energy accounting).
- Memory safety (a kernel panic is fatal — there is no "restart" in
  embedded neuromorphic deployments).
- Fearless concurrency (the scheduler is highly parallel).
- A vibrant ecosystem for systems programming.

The two candidate languages were Rust and C++.

## Decision
NurosOS is written in **Rust**. C++ was considered and rejected.

## Consequences
- **Pro:** Memory safety without garbage collection. The borrow checker
  eliminates use-after-free, data races, and null pointer dereferences
  at compile time — critical for a kernel that must run for months
  without restart.
- **Pro:** `cargo` provides reproducible builds, dependency management,
  and a unified test/benchmark/doc pipeline — all of which C++ lacks
  in any standardized form.
- **Pro:** The `no_std` ecosystem lets us target embedded neuromorphic
  hardware (ARM Cortex-M, RISC-V) without a libc dependency.
- **Con:** The borrow checker sometimes forces awkward code shapes
  (e.g., the `Arc<Scheduler>` pattern in `main.rs`). This is a one-time
  cost; the long-term benefit is bug-free concurrency.
- **Con:** The Rust compilation model is slow for incremental builds.
  Mitigated by `sccache` and `cargo-nextest`.

## References
- CONTRIBUTING.md §6 (Coding Standards)
