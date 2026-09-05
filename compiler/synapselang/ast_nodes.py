"""SynapseLang AST node definitions.

Biological correspondence
-------------------------
The AST is the equivalent of the **protein structure** produced by
translation. Just as a protein has a hierarchy (primary sequence →
secondary structure → tertiary fold → quaternary complex), the AST
has a hierarchy: tokens → expressions → declarations → circuits →
modules. Each level adds semantic structure that the next stage can
operate on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Union


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

# A connection pattern: how to wire source → target.
ConnectionPattern = Literal["sparse", "dense", "fixed"]

# A plasticity rule tag.
PlasticityRule = Literal["hebbian", "stdp", "fixed", "dopamine"]


@dataclass
class UnitValue:
    """A numeric literal with a unit suffix (e.g., `18ms`, `-55mV`).

    The biological scale matters — we preserve units through the AST
    so the codegen can validate them (e.g., a threshold must be in mV,
    not in ms).
    """

    value: float
    unit: str  # one of: "ms", "mV", "Hz", "nA", "pA", "uF"

    def __repr__(self) -> str:
        return f"{self.value}{self.unit}"


# An expression in a parameter list: either a bare number or a unit value.
Expr = Union[float, int, UnitValue, str]


# ---------------------------------------------------------------------------
# Neuron model parameters
# ---------------------------------------------------------------------------

@dataclass
class LifParams:
    """Parameters for the Leaky Integrate-and-Fire neuron model.

    Defaults are the *Drosophila* mushroom-body Kenyon cell values
    (Acerbo et al., 2012).
    """

    tau_m: UnitValue = field(default_factory=lambda: UnitValue(18.0, "ms"))
    tau_s: UnitValue = field(default_factory=lambda: UnitValue(5.5, "ms"))
    theta: UnitValue = field(default_factory=lambda: UnitValue(-55.0, "mV"))
    v_rest: UnitValue = field(default_factory=lambda: UnitValue(-70.0, "mV"))
    v_reset: UnitValue = field(default_factory=lambda: UnitValue(-80.0, "mV"))
    tau_refrac: UnitValue = field(default_factory=lambda: UnitValue(2.0, "ms"))


@dataclass
class NeuronModelSpec:
    """A neuron model instantiation: type name + parameters."""

    model: Literal["LIF"]  # Only LIF supported in v0.1.0
    params: LifParams


# Alias: in v0.1.0 LIF is the only supported model, so the spec is
# LIF-specific in practice. The parser uses `LifModelSpec` for clarity.
LifModelSpec = NeuronModelSpec


# ---------------------------------------------------------------------------
# Plasticity rule specs
# ---------------------------------------------------------------------------

@dataclass
class HebbianSpec:
    """Hebbian plasticity: Δw = η · pre · post."""

    learning_rate: float = 0.01


@dataclass
class StdpSpec:
    """Spike-Timing-Dependent Plasticity.

    Mimics the dominant plasticity model in *Drosophila* associative
    learning (mushroom body).
    """

    eta_plus: float = 0.01
    eta_minus: float = 0.01
    tau_plus: UnitValue = field(default_factory=lambda: UnitValue(20.0, "ms"))
    tau_minus: UnitValue = field(default_factory=lambda: UnitValue(20.0, "ms"))


@dataclass
class FixedSpec:
    """No plasticity — fixed weight."""

    weight: float = 0.5


@dataclass
class DopamineSpec:
    """Dopamine-modulated plasticity (mimics PAM→MBON signaling)."""

    eta: float = 0.02
    dopamine: float = 0.0


PlasticitySpec = Union[HebbianSpec, StdpSpec, FixedSpec, DopamineSpec]


# ---------------------------------------------------------------------------
# Connection pattern specs
# ---------------------------------------------------------------------------

@dataclass
class SparseSpec:
    """Sparse connectivity: only `density` fraction of possible edges exist.

    Mirrors the ~5% sparse connectivity of ORN→KC projections in the
    Drosophila antennal lobe.
    """

    density: float = 0.05


@dataclass
class DenseSpec:
    """All-to-all connectivity (every source connects to every target)."""

    pass


ConnectionSpec = Union[SparseSpec, DenseSpec]


# ---------------------------------------------------------------------------
# Top-level declarations
# ---------------------------------------------------------------------------

@dataclass
class NeuronDecl:
    """A `neuron` declaration: instantiates a population of neurons.

    Example:
        neuron kc[4096] : LIF(tau_m=18ms, theta=-55mV);
    """

    name: str
    count: int
    model: NeuronModelSpec


@dataclass
class ConnectDecl:
    """A `connect` declaration: wires a source population to a target.

    Example:
        connect odor -> kc : sparse(density=0.05) : hebbian(lr=0.01);
    """

    source: str
    target: str
    pattern: ConnectionSpec
    plasticity: PlasticitySpec


@dataclass
class InhibitDecl:
    """An `inhibit` declaration: lateral inhibition within a population.

    Example:
        inhibit kc : lateral(radius=5, strength=0.3);

    Biological correspondence
    -------------------------
    This mimics the lateral inhibition mediated by GABAergic local
    interneurons in the Drosophila antennal lobe — it sharpens odor
    identity by suppressing non-principal responses.
    """

    target: str
    radius: int
    strength: float


@dataclass
class PortDecl:
    """An input or output port declaration.

    Example:
        input odor[256];
        output recall[256];
    """

    direction: Literal["input", "output"]
    name: str
    size: int


@dataclass
class CircuitDecl:
    """A `circuit` declaration: the top-level container for a neural circuit.

    A circuit is the SynapseLang equivalent of a *neuropil* — a
    topologically-bounded cluster of neurons that performs a specific
    function (e.g., the mushroom body is a circuit for associative memory).
    """

    name: str
    ports: list[PortDecl]
    neurons: list[NeuronDecl]
    connections: list[ConnectDecl]
    inhibitions: list[InhibitDecl]


@dataclass
class SyscallDecl:
    """A `syscall` declaration: wraps a circuit as a queryable API.

    Example:
        syscall memorize(odor: Tensor[256]) -> Handle { ... }

    Biological correspondence
    -------------------------
    A syscall is the equivalent of a *behavior* — a coordinated activation
    pattern across multiple circuits that produces an observable output
    (e.g., "approach this odor", "avoid this odor").
    """

    name: str
    params: list[tuple[str, str]]  # (name, type)
    return_type: str
    body: list["Statement"]


@dataclass
class Statement:
    """A single statement inside a syscall body."""

    kind: Literal["inject", "wait_until", "return", "assign"]
    args: dict


@dataclass
class NirModule:
    """A complete SynapseLang module (one .syn file)."""

    circuits: list[CircuitDecl]
    syscalls: list[SyscallDecl]
