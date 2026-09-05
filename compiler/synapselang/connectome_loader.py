"""Connectome loader for SynapseLang.

This module parses the open-source connectome data (from FlyWire .h5
files) and translates it into hardware-agnostic NIR bytecode.

Biological correspondence
-------------------------
This is the equivalent of reading the genome and producing the
*connectome* — the full wiring diagram of the brain. In biology, the
genome does not specify every synapse; instead, it specifies
*developmental rules* that, when executed, produce the connectome.
Here, we read the *result* of that developmental process (the .h5 file)
and convert it into a form the kernel can use.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import numpy as np


@dataclass
class ConnectomeNeuron:
    """A single neuron from the connectome dataset."""

    neuron_id: int
    region: str
    cell_type: str
    neurotransmitter: str  # "glutamate", "gaba", "acetylcholine", etc.


@dataclass
class ConnectomeSynapse:
    """A single synaptic connection from the connectome dataset."""

    pre_id: int
    post_id: int
    weight: float
    neurotransmitter: str
    delay_ms: float


@dataclass
class ConnectomeSummary:
    """Summary statistics of a loaded connectome."""

    neuron_count: int
    synapse_count: int
    region_counts: dict[str, int]
    neurotransmitter_counts: dict[str, int]


class ConnectomeLoader:
    """Loads a *Drosophila* connectome from a FlyWire .h5 file.

    In v0.1.0, this loader supports a *mini* version of the dataset
    (125M synapses, ~2 GB compressed). The full dataset (~500 GB) will
    be supported in v0.3.0 via memory-mapped access.

    Usage:
        >>> loader = ConnectomeLoader("data/connectome/drosophila-mini.h5")
        >>> summary = loader.summary()
        >>> print(summary.neuron_count, summary.synapse_count)
        (140000, 125000000)
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._neurons: list[ConnectomeNeuron] | None = None
        self._synapses: list[ConnectomeSynapse] | None = None
        self._summary: ConnectomeSummary | None = None

    def summary(self) -> ConnectomeSummary:
        """Return summary statistics. Loads the file lazily on first call."""
        if self._summary is None:
            self._load()
        assert self._summary is not None
        return self._summary

    def neurons(self) -> Iterator[ConnectomeNeuron]:
        """Iterate over all neurons."""
        if self._neurons is None:
            self._load()
        assert self._neurons is not None
        yield from self._neurons

    def synapses(self) -> Iterator[ConnectomeSynapse]:
        """Iterate over all synapses.

        ⚠️ This can yield ~125 million items for the full dataset.
        Prefer `summary()` if you only need counts.
        """
        if self._synapses is None:
            self._load()
        assert self._synapses is not None
        yield from self._synapses

    def to_nir(self, output_path: str | Path) -> None:
        """Convert the connectome to a NIR module and write to disk.

        The resulting NIR module has one circuit per neuropil, with
        concrete neurons and synapses (no projection rules — everything
        is expanded).
        """
        if self._neurons is None:
            self._load()
        assert self._neurons is not None and self._synapses is not None

        # Group neurons by region.
        regions: dict[str, list[ConnectomeNeuron]] = {}
        for n in self._neurons:
            regions.setdefault(n.region, []).append(n)

        circuits = []
        for region_name, neurons_in_region in regions.items():
            circuits.append({
                "name": region_name,
                "ports": [],
                "neurons": [
                    {
                        "name": f"n{n.neuron_id}",
                        "count": 1,
                        "model": "LIF",
                        "params": {
                            "tau_m": 18.0,
                            "theta": -55.0,
                            "v_rest": -70.0,
                            "v_reset": -80.0,
                            "tau_refrac": 2.0,
                            "neurotransmitter": n.neurotransmitter,
                            "cell_type": n.cell_type,
                        },
                    }
                    for n in neurons_in_region
                ],
                "synapses": [],
                "inhibitions": [],
            })

        # Add synapses (cross-region and intra-region).
        for syn in self._synapses:
            circuits.append({
                "name": f"synapse_{syn.pre_id}_{syn.post_id}",
                "ports": [],
                "neurons": [],
                "synapses": [{
                    "source": f"n{syn.pre_id}",
                    "target": f"n{syn.post_id}",
                    "pattern": "fixed",
                    "density": 1.0,
                    "plasticity": "fixed",
                    "plasticity_params": {"weight": syn.weight},
                }],
                "inhibitions": [],
            })

        nir = {
            "version": "0.1.0",
            "circuits": circuits,
            "syscalls": [],
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(nir, f, indent=2)

    def _load(self) -> None:
        """Load the .h5 file. Falls back to synthetic data if missing."""
        if not self.path.exists():
            print(f"[ConnectomeLoader] File not found: {self.path}. Using synthetic data.")
            self._load_synthetic()
            return

        try:
            import h5py
        except ImportError:
            print("[ConnectomeLoader] h5py not installed. Using synthetic data.")
            self._load_synthetic()
            return

        print(f"[ConnectomeLoader] Loading {self.path}...")
        with h5py.File(self.path, "r") as f:
            self._load_from_h5(f)

    def _load_from_h5(self, f: Any) -> None:
        """Load from an open h5py.File object.

        Expected dataset layout:
            /neurons/id           — int32 array
            /neurons/region       — bytes array (region name)
            /neurons/cell_type    — bytes array
            /neurons/neurotransmitter — bytes array
            /synapses/pre_id      — int32 array
            /synapses/post_id     — int32 array
            /synapses/weight      — float32 array
            /synapses/neurotransmitter — bytes array
            /synapses/delay_ms    — float32 array
        """
        neurons = []
        n_ids = f["neurons/id"][:]
        n_regions = f["neurons/region"][:]
        n_types = f["neurons/cell_type"][:]
        n_nts = f["neurons/neurotransmitter"][:]

        for i, nid in enumerate(n_ids):
            region = _decode_bytes(n_regions[i])
            cell_type = _decode_bytes(n_types[i])
            nt = _decode_bytes(n_nts[i])
            neurons.append(ConnectomeNeuron(
                neuron_id=int(nid),
                region=region,
                cell_type=cell_type,
                neurotransmitter=nt,
            ))
        self._neurons = neurons

        synapses = []
        pre_ids = f["synapses/pre_id"][:]
        post_ids = f["synapses/post_id"][:]
        weights = f["synapses/weight"][:]
        s_nts = f["synapses/neurotransmitter"][:]
        delays = f["synapses/delay_ms"][:]

        for i in range(len(pre_ids)):
            synapses.append(ConnectomeSynapse(
                pre_id=int(pre_ids[i]),
                post_id=int(post_ids[i]),
                weight=float(weights[i]),
                neurotransmitter=_decode_bytes(s_nts[i]),
                delay_ms=float(delays[i]),
            ))
        self._synapses = synapses

        self._compute_summary()

    def _load_synthetic(self) -> None:
        """Generate a small synthetic connectome for testing.

        Mimics the *topology* (not the scale) of *Drosophila*:
        - 3 regions: antennal_lobe, mushroom_body, lateral_horn
        - 1000 neurons
        - 10000 synapses
        """
        rng = np.random.default_rng(seed=42)
        regions = ["antennal_lobe", "mushroom_body", "lateral_horn"]
        nts = ["glutamate", "gaba", "acetylcholine"]
        cell_types = ["projection", "kenyon", "mbon", "local_interneuron"]

        neurons = []
        for i in range(1000):
            region = regions[i % 3]
            nt = nts[i % 3]
            ct = cell_types[i % 4]
            neurons.append(ConnectomeNeuron(
                neuron_id=i,
                region=region,
                cell_type=ct,
                neurotransmitter=nt,
            ))
        self._neurons = neurons

        synapses = []
        for _ in range(10000):
            pre = int(rng.integers(0, 1000))
            post = int(rng.integers(0, 1000))
            weight = float(rng.uniform(0.01, 1.0))
            nt = nts[pre % 3]
            delay = float(rng.uniform(0.5, 2.0))
            synapses.append(ConnectomeSynapse(
                pre_id=pre, post_id=post, weight=weight,
                neurotransmitter=nt, delay_ms=delay,
            ))
        self._synapses = synapses

        self._compute_summary()

    def _compute_summary(self) -> None:
        """Compute summary statistics from loaded data."""
        assert self._neurons is not None and self._synapses is not None

        region_counts: dict[str, int] = {}
        nt_counts_neurons: dict[str, int] = {}
        for n in self._neurons:
            region_counts[n.region] = region_counts.get(n.region, 0) + 1
            nt_counts_neurons[n.neurotransmitter] = (
                nt_counts_neurons.get(n.neurotransmitter, 0) + 1
            )

        self._summary = ConnectomeSummary(
            neuron_count=len(self._neurons),
            synapse_count=len(self._synapses),
            region_counts=region_counts,
            neurotransmitter_counts=nt_counts_neurons,
        )


def _decode_bytes(b: Any) -> str:
    """Decode an h5py bytes object to a Python string."""
    if isinstance(b, bytes):
        return b.decode("utf-8")
    return str(b)
