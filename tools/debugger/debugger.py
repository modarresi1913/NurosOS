#!/usr/bin/env python3
"""NurosOS interactive debugger.

Biological correspondence
-------------------------
This is the equivalent of a **patch-clamp rig** — the equipment a
neuroscientist uses to record from and stimulate individual neurons
in a living brain slice. Just as a patch-clamp electrode can inject
current and measure membrane potential, this debugger can inject
stimuli and read neuron state.

Status: v0.1.0 stub.
"""

from __future__ import annotations

import argparse
import socket
import sys
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

console = Console()


def main() -> int:
    parser = argparse.ArgumentParser(description="NurosOS interactive debugger")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    console.print(f"[bold]NurosOS Debugger[/bold] — connecting to {args.host}:{args.port}...")
    try:
        sock = socket.create_connection((args.host, args.port), timeout=5.0)
    except OSError as e:
        console.print(f"[red]✗[/red] Could not connect: {e}")
        return 1

    console.print("[green]✓[/green] Connected.")
    console.print("Commands: status, neuron <id>, stim <id> <current_pA>, "
                  "lesion <id>, quit")

    while True:
        try:
            cmd = Prompt.ask("[bold cyan]debug>[/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            break

        if cmd in ("quit", "exit"):
            break

        try:
            sock.sendall((cmd + "\n").encode())
            data = sock.recv(4096).decode("utf-8", errors="replace")
            console.print(data, end="")
        except OSError as e:
            console.print(f"[red]Connection error:[/red] {e}")
            break

    sock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
