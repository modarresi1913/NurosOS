"""SynapseLang CLI — command-line interface.

Biological correspondence
-------------------------
This is the equivalent of a **lab technician's protocol sheet** — the
scripted set of steps that turn a biological question ("does this
circuit work?") into a concrete experimental procedure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from synapselang import (
    ConnectomeLoader,
    Lexer,
    NirEmitter,
    Parser,
)

console = Console()


@click.group()
def cli() -> None:
    """SynapseLang — compile .syn files to NIR bytecode."""


@cli.command()
@click.argument("source", type=click.Path(exists=True, dir_okay=False))
@click.option("-o", "--output", type=click.Path(dir_okay=False),
              default=None, help="Output .nir file path. Defaults to <source>.nir")
@click.option("--format", "fmt", type=click.Choice(["msgpack", "json"]),
              default="msgpack", help="Output format")
@click.option("--print-ast", is_flag=True, help="Print the parsed AST and exit")
def compile(source: str, output: str | None, fmt: str, print_ast: bool) -> None:
    """Compile a .syn file to NIR bytecode."""
    source_path = Path(source)
    source_code = source_path.read_text(encoding="utf-8")

    # Lex + parse.
    try:
        tokens = list(Lexer(source_code).tokens())
        ast = Parser(source_code).parse()
    except Exception as e:
        console.print(f"[red]Parse error:[/red] {e}")
        sys.exit(1)

    if print_ast:
        console.print_json(json.dumps(
            {"circuits": [c.name for c in ast.circuits],
             "syscalls": [s.name for s in ast.syscalls]},
        ))
        return

    # Lower to NIR.
    nir = NirEmitter().emit(ast)

    # Write output.
    if output is None:
        output = str(source_path.with_suffix(".nir"))
    out_path = Path(output)

    if fmt == "msgpack":
        out_path.write_bytes(nir.to_msgpack())
    else:
        out_path.write_text(nir.to_json(), encoding="utf-8")

    console.print(f"[green]✓[/green] Compiled {source_path.name} → {out_path.name}")
    console.print(f"  Circuits: {len(nir.circuits)}")
    console.print(f"  Syscalls: {len(nir.syscalls)}")
    total_neurons = sum(
        n.count for c in nir.circuits for n in c.neurons
    )
    total_synapses = sum(len(c.synapses) for c in nir.circuits)
    console.print(f"  Total neurons (declared): {total_neurons}")
    console.print(f"  Total synapse rules: {total_synapses}")


@cli.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
def inspect(path: str) -> None:
    """Inspect a connectome .h5 file. Prints summary statistics."""
    loader = ConnectomeLoader(path)
    summary = loader.summary()

    console.print(f"[bold]Connectome:[/bold] {path}")
    console.print(f"  Neurons:  {summary.neuron_count:,}")
    console.print(f"  Synapses: {summary.synapse_count:,}")

    # Region breakdown.
    region_table = Table(title="Regions (neuropils)")
    region_table.add_column("Region", style="cyan")
    region_table.add_column("Neurons", justify="right", style="green")
    for region, count in sorted(summary.region_counts.items(),
                                 key=lambda x: -x[1]):
        region_table.add_row(region, f"{count:,}")
    console.print(region_table)

    # Neurotransmitter breakdown.
    nt_table = Table(title="Neurotransmitter distribution")
    nt_table.add_column("Neurotransmitter", style="cyan")
    nt_table.add_column("Count", justify="right", style="green")
    for nt, count in sorted(summary.neurotransmitter_counts.items(),
                             key=lambda x: -x[1]):
        nt_table.add_row(nt, f"{count:,}")
    console.print(nt_table)


@cli.command()
@click.option("--target", type=click.Choice(["x86", "loihi", "fpga"]),
              default="x86", help="Target backend")
@click.option("--circuit", type=str, default=None,
              help="Specific circuit to benchmark (default: all)")
def bench(target: str, circuit: str | None) -> None:
    """Run built-in benchmarks."""
    console.print(f"[yellow]⚠[/yellow] Benchmarking is not yet implemented in v0.1.0.")
    console.print(f"  Target: {target}")
    if circuit:
        console.print(f"  Circuit: {circuit}")
    console.print("  Use `cargo bench` in /kernel for Rust-side benchmarks.")


def main() -> None:
    """Entry point for the `synapselang` console script."""
    cli()


if __name__ == "__main__":
    main()
