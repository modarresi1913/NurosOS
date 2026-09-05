"""SynapseLang NIR (Neuromorphic Intermediate Representation) emitter.

Lowers the AST into a hardware-agnostic bytecode that the kernel can load.

Biological correspondence
-------------------------
This is the equivalent of **protein folding** — the linear amino-acid
sequence (AST) is folded into a 3D structure (NIR graph) that can
actually perform its biological function. Just as a misfolded protein
is non-functional, a malformed NIR module will fail to load on the
kernel and raise an error at boot time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import msgpack

from synapselang.ast_nodes import (
    CircuitDecl,
    ConnectDecl,
    DenseSpec,
    DopamineSpec,
    FixedSpec,
    HebbianSpec,
    InhibitDecl,
    NeuronDecl,
    NirModule,
    PortDecl,
    SparseSpec,
    Statement,
    StdpSpec,
    SyscallDecl,
    UnitValue,
)


# NIR format version. Bump this whenever the on-disk layout changes.
NIR_VERSION = "0.1.0"


@dataclass
class NirNeuron:
    """A neuron in the NIR graph."""

    name: str
    count: int
    model: str  # "LIF" (only supported model in v0.1.0)
    params: dict[str, Any]


@dataclass
class NirSynapse:
    """A synaptic connection in the NIR graph.

    Note: in NIR, we represent *projection rules* (e.g., "all-to-all with
    5% sparsity") rather than individual synapses. The kernel expands
    these rules into concrete synapses at load time, using the connectome
    dataset as a constraint.
    """

    source: str
    target: str
    pattern: str  # "sparse" or "dense"
    density: float
    plasticity: str  # "hebbian", "stdp", "fixed", "dopamine"
    plasticity_params: dict[str, Any]


@dataclass
class NirInhibition:
    """A lateral inhibition rule in the NIR graph."""

    target: str
    radius: int
    strength: float


@dataclass
class NirCircuit:
    """A fully-lowered circuit in the NIR graph."""

    name: str
    ports: list[dict[str, Any]]
    neurons: list[NirNeuron]
    synapses: list[NirSynapse]
    inhibitions: list[NirInhibition]


@dataclass
class NirSyscall:
    """A syscall (behavioral API) in the NIR graph."""

    name: str
    params: list[tuple[str, str]]
    return_type: str
    body: list[dict[str, Any]]


@dataclass
class NirModule:
    """A complete NIR module — the output of the SynapseLang compiler."""

    version: str = NIR_VERSION
    circuits: list[NirCircuit] = field(default_factory=list)
    syscalls: list[NirSyscall] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict (for JSON / msgpack)."""
        return {
            "version": self.version,
            "circuits": [
                {
                    "name": c.name,
                    "ports": c.ports,
                    "neurons": [
                        {"name": n.name, "count": n.count, "model": n.model, "params": n.params}
                        for n in c.neurons
                    ],
                    "synapses": [
                        {
                            "source": s.source,
                            "target": s.target,
                            "pattern": s.pattern,
                            "density": s.density,
                            "plasticity": s.plasticity,
                            "plasticity_params": s.plasticity_params,
                        }
                        for s in c.synapses
                    ],
                    "inhibitions": [
                        {"target": i.target, "radius": i.radius, "strength": i.strength}
                        for i in c.inhibitions
                    ],
                }
                for c in self.circuits
            ],
            "syscalls": [
                {
                    "name": s.name,
                    "params": s.params,
                    "return_type": s.return_type,
                    "body": s.body,
                }
                for s in self.syscalls
            ],
        }

    def to_json(self) -> str:
        """Serialize to a pretty-printed JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def to_msgpack(self) -> bytes:
        """Serialize to msgpack bytes (the canonical on-disk NIR format)."""
        return msgpack.packb(self.to_dict(), use_bin_type=True)


class NirEmitter:
    """Lowers a SynapseLang AST into a NirModule.

    Usage:
        >>> parser = Parser(source)
        >>> ast = parser.parse()
        >>> emitter = NirEmitter()
        >>> nir = emitter.emit(ast)
        >>> with open("out.nir", "wb") as f:
        ...     f.write(nir.to_msgpack())
    """

    def emit(self, module: NirModule) -> NirModule:
        """Lower the AST into a NIR module."""
        nir = NirModule()
        for circuit in module.circuits:
            nir.circuits.append(self._emit_circuit(circuit))
        for syscall in module.syscalls:
            nir.syscalls.append(self._emit_syscall(syscall))
        return nir

    # ------------------------------------------------------------------
    # Circuit lowering
    # ------------------------------------------------------------------

    def _emit_circuit(self, c: CircuitDecl) -> NirCircuit:
        """Lower a single circuit declaration."""
        ports = [
            {"direction": p.direction, "name": p.name, "size": p.size}
            for p in c.ports
        ]
        neurons = [self._emit_neuron(n) for n in c.neurons]
        synapses = [self._emit_connect(conn) for conn in c.connections]
        inhibitions = [self._emit_inhibit(i) for i in c.inhibitions]
        return NirCircuit(
            name=c.name,
            ports=ports,
            neurons=neurons,
            synapses=synapses,
            inhibitions=inhibitions,
        )

    def _emit_neuron(self, n: NeuronDecl) -> NirNeuron:
        """Lower a neuron declaration.

        Validates that the model is LIF (the only supported model in
        v0.1.0) and that all parameters have valid units.
        """
        if n.model.model != "LIF":
            raise ValueError(
                f"Unsupported neuron model {n.model.model!r}. Only 'LIF' is "
                f"supported in v0.1.0."
            )
        params = self._serialize_lif_params(n.model.params)
        return NirNeuron(
            name=n.name, count=n.count, model="LIF", params=params
        )

    def _serialize_lif_params(self, params) -> dict[str, Any]:
        """Serialize LIF parameters, validating units.

        Validates that time constants are in `ms` and voltages are in `mV`.
        """
        out: dict[str, Any] = {}
        for field_name in ("tau_m", "tau_s", "tau_refrac"):
            v = getattr(params, field_name)
            if not isinstance(v, UnitValue):
                continue
            if v.unit != "ms":
                raise ValueError(
                    f"{field_name} must be in 'ms', got {v.unit!r}"
                )
            out[field_name] = v.value
        for field_name in ("theta", "v_rest", "v_reset"):
            v = getattr(params, field_name)
            if not isinstance(v, UnitValue):
                continue
            if v.unit != "mV":
                raise ValueError(
                    f"{field_name} must be in 'mV', got {v.unit!r}"
                )
            out[field_name] = v.value
        return out

    def _emit_connect(self, c: ConnectDecl) -> NirSynapse:
        """Lower a connect declaration."""
        if isinstance(c.pattern, SparseSpec):
            pattern = "sparse"
            density = c.pattern.density
        elif isinstance(c.pattern, DenseSpec):
            pattern = "dense"
            density = 1.0
        else:
            raise TypeError(f"Unknown pattern type {type(c.pattern)}")

        if isinstance(c.plasticity, HebbianSpec):
            plast = "hebbian"
            plast_params = {"learning_rate": c.plasticity.learning_rate}
        elif isinstance(c.plasticity, StdpSpec):
            plast = "stdp"
            plast_params = {
                "eta_plus": c.plasticity.eta_plus,
                "eta_minus": c.plasticity.eta_minus,
                "tau_plus_ms": c.plasticity.tau_plus.value,
                "tau_minus_ms": c.plasticity.tau_minus.value,
            }
        elif isinstance(c.plasticity, FixedSpec):
            plast = "fixed"
            plast_params = {"weight": c.plasticity.weight}
        elif isinstance(c.plasticity, DopamineSpec):
            plast = "dopamine"
            plast_params = {"eta": c.plasticity.eta, "dopamine": c.plasticity.dopamine}
        else:
            raise TypeError(f"Unknown plasticity type {type(c.plasticity)}")

        return NirSynapse(
            source=c.source,
            target=c.target,
            pattern=pattern,
            density=density,
            plasticity=plast,
            plasticity_params=plast_params,
        )

    def _emit_inhibit(self, i: InhibitDecl) -> NirInhibition:
        """Lower an inhibit declaration.

        Lateral inhibition is a key feature of the *Drosophila* antennal
        lobe — it sharpens odor identity by suppressing non-principal
        responses.
        """
        return NirInhibition(
            target=i.target, radius=i.radius, strength=i.strength
        )

    # ------------------------------------------------------------------
    # Syscall lowering
    # ------------------------------------------------------------------

    def _emit_syscall(self, s: SyscallDecl) -> NirSyscall:
        """Lower a syscall declaration."""
        body = [self._emit_statement(stmt) for stmt in s.body]
        return NirSyscall(
            name=s.name,
            params=s.params,
            return_type=s.return_type,
            body=body,
        )

    def _emit_statement(self, s: Statement) -> dict[str, Any]:
        """Lower a single statement."""
        return {"kind": s.kind, "args": s.args}
