# NurosOS Tools

This directory contains profiling, debugging, and visualization tools for NurosOS.

| Tool         | Language | Purpose                                                      |
|--------------|----------|--------------------------------------------------------------|
| `profiler/`  | Python   | Sampling profiler that attaches to a running kernel via RPC. |
| `debugger/`  | Python   | Interactive neuron inspector + lesion simulator.             |
| `visualizer/`| Python   | Real-time raster plots of spike trains.                      |

## Quickstart

```bash
# Profile a running kernel for 60 seconds.
python tools/profiler/profiler.py --host=127.0.0.1 --port=8080 --duration=60

# Open the interactive debugger.
python tools/debugger/debugger.py --host=127.0.0.1 --port=8080

# Render a real-time raster plot of the antennal lobe.
python tools/visualizer/raster.py --region=antennal_lobe --port=8080
```

All tools are stubs in v0.1.0 — they connect to the kernel's RPC port
and issue commands from the [shell protocol](../compiler/synapselang/shell.py).
