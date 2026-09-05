"""Interactive SynapseLang shell.

Connects to a running NurosOS kernel instance and provides a REPL for
inspecting neuron state, injecting stimuli, and querying the
Associative Memory Store.

Biological correspondence
-------------------------
This is the equivalent of an **in vivo electrophysiology rig** — the
equipment a neuroscientist uses to record from and stimulate a living
brain. The shell provides the same affordances: read activity, inject
current, lesion neurons, observe behavior.
"""

from __future__ import annotations

import socket
import sys

import click
from rich.console import Console
from rich.prompt import Prompt

console = Console()


@click.command()
@click.option("--host", default="127.0.0.1", help="Kernel host")
@click.option("--port", default=8080, type=int, help="Kernel RPC port")
def main(host: str, port: int) -> None:
    """Attach to a running NurosOS kernel."""
    console.print(f"[bold]NurosOS Shell[/bold] — connecting to {host}:{port}...")

    try:
        sock = socket.create_connection((host, port), timeout=5.0)
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        console.print(f"[red]✗[/red] Could not connect: {e}")
        console.print("[yellow]Hint:[/yellow] Is the kernel running? "
                       "Start it with `./nuros-cli start --mode=emulation`.")
        sys.exit(1)

    console.print("[green]✓[/green] Connected. Type 'help' for commands, 'exit' to quit.")
    console.print("")

    try:
        _repl(sock)
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
    finally:
        sock.close()


def _repl(sock: socket.socket) -> None:
    """The main read-eval-print loop."""
    while True:
        try:
            line = Prompt.ask("[bold cyan]nuros>[/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            break

        line = line.strip()
        if not line:
            continue
        if line in ("exit", "quit"):
            break
        if line == "help":
            _print_help()
            continue

        # Send the command to the kernel.
        try:
            sock.sendall((line + "\n").encode("utf-8"))
            # Read the response (line-based for v0.1.0).
            data = sock.recv(4096).decode("utf-8", errors="replace")
            console.print(data, end="")
        except OSError as e:
            console.print(f"[red]Connection error:[/red] {e}")
            break


def _print_help() -> None:
    """Print the help table."""
    from rich.table import Table
    t = Table(title="NurosOS Shell commands")
    t.add_column("Command", style="cyan")
    t.add_column("Description", style="white")
    t.add_row("status", "Print kernel status (tick, neuron count, energy)")
    t.add_row("neurons <region>", "List neurons in a region")
    t.add_row("potential <id>", "Read membrane potential of a neuron")
    t.add_row("stim <id> <current>", "Inject current into a neuron (pA)")
    t.add_row("lesion <id>", "Lesion a neuron (triggers neuroplasticity)")
    t.add_row("ams query <vec>", "Query the Associative Memory Store")
    t.add_row("ams reinforce <handle> <reward>", "Reinforce a stored memory")
    t.add_row("benchmark <name>", "Run a Fly Benchmark sub-suite")
    t.add_row("exit", "Disconnect from the kernel")
    console.print(t)


if __name__ == "__main__":
    main()
