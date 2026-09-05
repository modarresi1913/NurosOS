#!/usr/bin/env python3
"""NurosOS raster plot visualizer.

Biological correspondence
-------------------------
This is the equivalent of a **multi-electrode array (MEA) recording** —
the visualization neuroscientists use to display spike trains from
many neurons simultaneously. Each row is a neuron; each tick mark is
a spike.

Status: v0.1.0 stub.
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description="NurosOS raster plot")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--region", default="antennal_lobe",
                       help="Region to visualize")
    parser.add_argument("--duration", type=float, default=10.0,
                       help="Recording duration in seconds")
    args = parser.parse_args()

    try:
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm
        # Ensure Chinese characters render if any are present in labels.
        try:
            fm.fontManager.addfont("/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf")
            plt.rcParams["font.sans-serif"] = ["Noto Sans SC", "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False
        except Exception:
            pass
    except ImportError:
        print("[visualizer] matplotlib is required. Install with: pip install matplotlib",
              file=sys.stderr)
        return 1

    print(f"[visualizer] Connecting to {args.host}:{args.port}...", file=sys.stderr)
    try:
        sock = socket.create_connection((args.host, args.port), timeout=5.0)
    except OSError as e:
        print(f"[visualizer] Could not connect: {e}", file=sys.stderr)
        return 1

    # Sample spikes.
    spikes: list[tuple[int, float]] = []  # (neuron_id, time_s)
    n_samples = int(args.duration * 30)
    for i in range(n_samples):
        sock.sendall(f"neurons {args.region}\n".encode())
        # In v0.1.0 the kernel returns a stub response.
        data = sock.recv(4096).decode("utf-8", errors="replace").strip()
        # Parse and accumulate (placeholder logic).
        spikes.append((i % 50, i / 30.0))
        time.sleep(1.0 / 30.0)

    sock.close()

    # Plot.
    fig, ax = plt.subplots(constrained_layout=True, figsize=(10, 6))
    if spikes:
        xs = [t for _, t in spikes]
        ys = [n for n, _ in spikes]
        ax.scatter(xs, ys, s=3, c="black", marker="|")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Neuron ID")
    ax.set_title(f"Spike raster — {args.region}")
    ax.set_xlim(0, args.duration)
    plt.savefig("/home/z/my-project/download/nuros_raster.png", dpi=120)
    print("[visualizer] Saved raster plot to /home/z/my-project/download/nuros_raster.png",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
