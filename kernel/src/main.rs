//! # NurosOS Kernel — Main Entry Point
//!
//! This binary boots the NurosOS microkernel. The boot sequence is
//! described in `ARCHITECTURE.md` §2.1:
//!
//! 1. HAL init          (probe CPU, set up page tables)
//! 2. Load connectome   (parse NIR bytecode → build Neuron graph in memory)
//! 3. Spawn sensory regions   (vision, olfaction, mechanosensation)
//! 4. Spawn motor regions     (locomotion, grooming, courtship)
//! 5. Enter main loop   (Sparse Propagation Protocol)
//!
//! ## Biological correspondence
//!
//! Steps 1–4 correspond to embryonic neurogenesis and circuit wiring
//! (which in *Drosophila* happens during pupal development, ~100 hours).
//! Step 5 corresponds to the onset of active behavior — the moment the
//! fly "wakes up" and starts processing sensory input.

use std::path::PathBuf;
use std::sync::Arc;

use clap::{Parser, ValueEnum};
use log::{info, warn};

use nuros_kernel::{
    connectome::ConnectomeLoader,
    hal,
    region::RegionGraph,
    sched::Scheduler,
};

/// Command-line interface for the NurosOS kernel binary.
///
/// These flags mirror the options documented in the README's "Quickstart".
#[derive(Parser, Debug)]
#[command(
    name = "nuros-kernel",
    version,
    about = "Bio-inspired neuromorphic microkernel (Drosophila connectome)"
)]
struct Cli {
    /// Execution mode. `emulation` runs everything in software on x86_64;
    /// `native` runs on real neuromorphic silicon via the HAL.
    #[arg(long, value_enum, default_value_t = Mode::Emulation)]
    mode: Mode,

    /// Which biological target to emulate. Currently only `drosophila`
    /// (male, adult) is supported. Future targets: `drosophila_larva`,
    /// `c_elegans` (301 neurons, useful for unit testing).
    #[arg(long, default_value = "drosophila")]
    target: String,

    /// Path to the compressed connectome dataset (.h5).
    #[arg(long)]
    connectome: PathBuf,

    /// TCP port for the Hybrid API (REST/gRPC) server.
    #[arg(long, default_value_t = 8080)]
    rpc_port: u16,

    /// If set, dump a flamegraph of the scheduler after N ticks
    /// (debugging only — degrades performance).
    #[arg(long)]
    profile_ticks: Option<u64>,
}

#[derive(Copy, Clone, Debug, ValueEnum)]
enum Mode {
    /// Software emulation on commodity hardware.
    Emulation,
    /// Native execution on neuromorphic silicon.
    Native,
}

/// Entry point. The actual work happens in `run()` so that integration
/// tests can call it without spawning a new process.
fn main() -> anyhow::Result<()> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info"))
        .format_timestamp_ms()
        .init();

    let cli = Cli::parse();
    info!("NurosOS kernel v{} booting...", nuros_kernel::ABI_VERSION);
    info!("  mode       = {:?}", cli.mode);
    info!("  target     = {}", cli.target);
    info!("  connectome = {}", cli.connectome.display());
    info!("  rpc_port   = {}", cli.rpc_port);

    run(cli)
}

/// Boot the kernel. This function is the runtime equivalent of biological
/// "neurogenesis completion" — the moment the connectome is fully wired
/// and ready to receive sensory input.
fn run(cli: Cli) -> anyhow::Result<()> {
    // -------------------------------------------------------------------------
    // Step 1: HAL init.
    //
    // In biology this corresponds to the onset of glial-cell metabolic
    // support — the infrastructure that keeps neurons alive. In NurosOS
    // it is the moment we acquire access to physical compute resources.
    // -------------------------------------------------------------------------
    let hal = hal::probe(cli.mode)?;
    info!("[1/5] HAL initialized: {}", hal.name());

    // -------------------------------------------------------------------------
    // Step 2: Load the connectome.
    //
    // This parses the FlyWire .h5 dataset into an in-memory RegionGraph.
    // The graph is the *static wiring diagram* — synaptic weights at this
    // point are the "naive" values from the dataset; plasticity will
    // modify them during runtime.
    // -------------------------------------------------------------------------
    info!("[2/5] Loading connectome...");
    let connectome = ConnectomeLoader::load(&cli.connectome)?;
    info!(
        "       Loaded {} neurons, {} synapses",
        connectome.neuron_count(),
        connectome.synapse_count()
    );

    // -------------------------------------------------------------------------
    // Step 3: Build the region graph.
    //
    // Neurons are grouped into Regions (neuropils): antennal lobe, mushroom
    // body, central complex, lateral horn, etc. This grouping is critical
    // for the Sparse Propagation Protocol — SPP operates per-region, not
    // globally, to preserve locality (Invariant I2).
    // -------------------------------------------------------------------------
    info!("[3/5] Building region graph...");
    let graph = RegionGraph::from_connectome(&connectome)?;
    info!(
        "       {} regions instantiated (target={})",
        graph.region_count(),
        cli.target
    );

    // -------------------------------------------------------------------------
    // Step 4: Allocate the scheduler.
    //
    // The scheduler is the heart of the kernel. It owns the event queue,
    // the active-neuron set, and the plasticity update queue. It is the
    // only place in the kernel that mutates global state.
    // -------------------------------------------------------------------------
    info!("[4/5] Spawning scheduler (SPP, sparsity={:.0}%)...",
        nuros_kernel::SPARSITY_THRESHOLD * 100.0);
    let scheduler = Arc::new(Scheduler::new(graph, hal));

    // -------------------------------------------------------------------------
    // Step 5: Enter the main loop.
    //
    // This loop is event-driven — it does NOT sleep for TICK_MS between
    // iterations. Instead, it blocks on the event queue and wakes up only
    // when there is work to do. This is what gives NurosOS its energy
    // efficiency on neuromorphic silicon (where idle = zero power).
    //
    // Biologically, this loop corresponds to the moment the fly's nervous
    // system "goes live" — sensory afferents start firing, motor circuits
    // start generating descending commands, and behavior begins.
    // -------------------------------------------------------------------------
    info!("[5/5] Entering main loop. Press Ctrl-C to halt.");
    let runtime = std::thread::Builder::new()
        .name("nuros-main".into())
        .spawn({
            let sched = Arc::clone(&scheduler);
            move || sched.run_forever(cli.profile_ticks)
        })?;

    // Spawn the Hybrid API (REST/gRPC) on a separate thread. This lets
    // external AI clients (PyTorch, TensorFlow) query the running OS.
    let rpc_handle = std::thread::Builder::new()
        .name("nuros-rpc".into())
        .spawn({
            let sched = Arc::clone(&scheduler);
            move || nuros_kernel::hal::rpc::serve(sched, cli.rpc_port)
        })?;

    // Block until either thread exits or the user hits Ctrl-C.
    let _ = runtime.join();
    let _ = rpc_handle.join();
    warn!("Kernel halted.");
    Ok(())
}
