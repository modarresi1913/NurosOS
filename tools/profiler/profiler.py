#!/usr/bin/env python3
"""NurosOS profiler — sampling profiler for the running kernel.

Biological correspondence
-------------------------
This is the equivalent of **two-photon calcium imaging** — a method
neuroscientists use to record population activity in a living brain
with high spatial and temporal resolution. Just as calcium imaging
samples neuron activity at ~30 Hz, this profiler samples the kernel's
state at a configurable rate.

Status: v0.1.0 stub. The actual sampling logic will be implemented in v0.2.0
once the kernel's RPC server is functional.
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="NurosOS sampling profiler")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--duration", type=float, default=60.0,
                       help="Sampling duration in seconds")
    parser.add_argument("--rate", type=float, default=30.0,
                       help="Sampling rate in Hz (default: 30, like calcium imaging)")
    parser.add_argument("-o", "--output", type=Path, default=None,
                       help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    print(f"[profiler] Connecting to {args.host}:{args.port}...", file=sys.stderr)
    try:
        sock = socket.create_connection((args.host, args.port), timeout=5.0)
    except OSError as e:
        print(f"[profiler] Could not connect: {e}", file=sys.stderr)
        return 1

    samples: list[dict] = []
    interval = 1.0 / args.rate
    n_samples = int(args.duration * args.rate)

    print(f"[profiler] Sampling {n_samples} samples at {args.rate} Hz...", file=sys.stderr)
    for i in range(n_samples):
        sock.sendall(b"status\n")
        data = sock.recv(4096).decode("utf-8", errors="replace")
        try:
            samples.append({"t": i * interval, "raw": data.strip()})
        except Exception:
            pass
        time.sleep(interval)

    sock.close()

    report = {
        "host": args.host,
        "port": args.port,
        "rate_hz": args.rate,
        "duration_s": args.duration,
        "samples": samples,
    }

    if args.output:
        args.output.write_text(json.dumps(report, indent=2))
        print(f"[profiler] Wrote {args.output}", file=sys.stderr)
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
