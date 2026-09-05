"""SynapseLang standard library — pre-built cognitive primitives.

Biological correspondence
-------------------------
This is the equivalent of **conserved gene families** — circuits that
appear, with minor variations, across many species. Just as the Hox
gene family specifies body-plan development in everything from fruit
flies to humans, these stdlib modules specify basic cognitive
operations (pattern completion, lateral inhibition, winner-take-all)
that any neuromorphic system needs.
"""

from __future__ import annotations

from synapselang.ast_nodes import (
    CircuitDecl,
    ConnectDecl,
    DenseSpec,
    HebbianSpec,
    InhibitDecl,
    LifParams,
    LifModelSpec,
    NeuronDecl,
    PortDecl,
    SparseSpec,
    StdpSpec,
)


def kenyon_cell_layer(name: str = "kc", count: int = 4096) -> NeuronDecl:
    """Instantiate a population of αβ Kenyon cells.

    Biological correspondence
    -------------------------
    Kenyon cells are the principal neurons of the *Drosophila* mushroom
    body. They are famously sparse — only ~5% are active at any time —
    which gives the mushroom body its high-dimensional odor coding
    capacity. Default parameters are from Acerbo et al. (2012).
    """
    return NeuronDecl(
        name=name,
        count=count,
        model=LifModelSpec(model="LIF", params=LifParams()),
    )


def antennal_lobe_circuit(name: str = "antennal_lobe") -> CircuitDecl:
    """A canonical antennal lobe circuit.

    Biological correspondence
    -------------------------
    The antennal lobe is the first relay of the olfactory system in
    *Drosophila* (analogous to the olfactory bulb in mammals). Odorant
    receptor neurons (ORNs) project to glomeruli, where they synapse
    onto projection neurons (PNs) and local interneurons (LNs). The
    LNs provide lateral inhibition, which sharpens odor identity.

    This circuit is the *hello world* of neuromorphic computing —
    every NurosOS tutorial starts here.
    """
    return CircuitDecl(
        name=name,
        ports=[
            PortDecl(direction="input", name="orn", size=1200),  # 1200 ORN types
            PortDecl(direction="output", name="pn", size=200),   # 200 glomeruli
        ],
        neurons=[
            NeuronDecl(name="pn", count=200, model=LifModelSpec(
                model="LIF",
                params=LifParams(tau_m=10.0, theta=-50.0),
            )),
        ],
        connections=[
            # ORN → PN: dense, fixed-weight (this is hard-wired biology).
            ConnectDecl(
                source="orn", target="pn",
                pattern=DenseSpec(),
                plasticity=StdpSpec(),
            ),
        ],
        inhibitions=[
            # Lateral inhibition sharpens odor identity.
            InhibitDecl(target="pn", radius=5, strength=0.3),
        ],
    )


def mushroom_body_circuit(name: str = "mushroom_body") -> CircuitDecl:
    """A canonical mushroom body circuit for associative memory.

    Biological correspondence
    -------------------------
    The mushroom body is the seat of associative learning in *Drosophila*.
    Kenyon cells (sparse, high-dimensional) project to mushroom body
    output neurons (MBONs), which encode approach/avoid valence. The
    KC→MBON synapse is the site of dopamine-modulated plasticity —
    this is where the fly learns that "odor X = bad" (when paired with
    shock) or "odor Y = good" (when paired with sugar).
    """
    return CircuitDecl(
        name=name,
        ports=[
            PortDecl(direction="input", name="odor", size=256),
            PortDecl(direction="output", name="valence", size=16),
        ],
        neurons=[
            kenyon_cell_layer("kc", count=4096),
            NeuronDecl(name="mbon", count=16, model=LifModelSpec(
                model="LIF",
                params=LifParams(tau_m=10.0, theta=-50.0),
            )),
        ],
        connections=[
            # ORN → KC: sparse, Hebbian (5% density, like the fly).
            ConnectDecl(
                source="odor", target="kc",
                pattern=SparseSpec(density=0.05),
                plasticity=HebbianSpec(learning_rate=0.01),
            ),
            # KC → MBON: dense, STDP (this is where learning happens).
            ConnectDecl(
                source="kc", target="mbon",
                pattern=DenseSpec(),
                plasticity=StdpSpec(),
            ),
        ],
        inhibitions=[
            # Lateral inhibition among KCs (sharpens sparse coding).
            InhibitDecl(target="kc", radius=5, strength=0.3),
        ],
    )


STDLIB_CIRCUITS = {
    "antennal_lobe": antennal_lobe_circuit,
    "mushroom_body": mushroom_body_circuit,
}
"""Registry of standard-library circuits.

Used by the SynapseLang `import` statement (planned for v0.2.0) to
look up pre-built circuits by name."""
