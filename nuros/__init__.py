"""
NurosOS — The Experimental Substrate for Synthetic Development.

NurosOS is an open, modular, inspectable substrate for synthetic development —
a runtime in which artificial organisms can be instantiated, developed,
embodied, observed, measured, forked, replayed, and experimentally compared.

Core Principles:
    1. Substrate Independence
    2. Development Over Static Programming
    3. Memory With Provenance
    4. Simulation != Reality
    5. Safety by Architecture
    6. Reproducibility
    7. Embodiment
    8. Modularity
    9. Human Correctability
    10. Scientific Humility

The central research question:
    What happens when we stop programming the final behavior of an artificial
    mind and instead program the conditions under which its cognitive
    structure can develop?
"""

__version__ = "0.3.0-alpha"
__status__ = "experimental"

CENTRAL_THESIS = (
    "NurosOS is an experimental substrate for studying how artificial minds "
    "develop. The fundamental object is not MODEL but TRAJECTORY; not AGENT "
    "but DEVELOPING ORGANISM."
)

PHILOSOPHY = (
    "Don't train a mind. Instantiate its developmental conditions. "
    "Don't program the mind. Program the conditions under which a mind "
    "can develop."
)

DISTINCTIONS = (
    "Memory is not storage. "
    "Development is not deployment. "
    "Simulation is not observation. "
    "Intelligence is not consciousness. "
    "Divergence is not individuality."
)

# Try to import the optional Rust-backed developmental substrate.
# This is built from nuros-dev/ via `maturin develop` or `pip install`.
try:
    from nuros import _dev  # type: ignore
    _DEV_AVAILABLE = True
    _DEV_VERSION = _dev.version()
except ImportError:
    _DEV_AVAILABLE = False
    _DEV_VERSION = None

