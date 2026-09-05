"""SynapseLang — A DSL for compiling cognitive functions into weighted graphs.

SynapseLang is the Layer 2 component of NurosOS. It compiles high-level
cognitive function descriptions (pattern recognition, associative memory,
motor pattern generation) into a hardware-agnostic bytecode called NIR
(Neuromorphic Intermediate Representation). The kernel then loads NIR
and executes it on the underlying neuromorphic substrate (x86 emulation,
Intel Loihi, FPGA, etc.).

Biological correspondence
-------------------------
SynapseLang is the equivalent of **developmental gene expression** in
biology. Just as the fly's genome does not specify every synapse
explicitly — instead, it specifies *rules* (e.g., "Kenyon cells project
randomly to the mushroom body calyx with 5% probability") that are
executed during development to wire up the brain — SynapseLang specifies
*rules* for circuit construction, not the full wiring diagram.

The full wiring diagram comes from two sources, combined at compile time:

1. **The connectome** (from .h5 files) — provides the *ground-truth*
   biological connections for circuits that should mimic the fly
   exactly.
2. **SynapseLang source** (from .syn files) — provides the *rules* for
   synthesizing new circuits that the fly does not have (e.g., a
   human-engineered associative memory with 4096 dimensions).
"""

from synapselang.lexer import Lexer, Token
from synapselang.parser import Parser
from synapselang.ast_nodes import (
    CircuitDecl,
    NeuronDecl,
    ConnectDecl,
    InhibitDecl,
    SyscallDecl,
)
from synapselang.codegen import NirEmitter, NirModule
from synapselang.connectome_loader import ConnectomeLoader

__version__ = "0.1.0-alpha"

__all__ = [
    "Lexer",
    "Token",
    "Parser",
    "CircuitDecl",
    "NeuronDecl",
    "ConnectDecl",
    "InhibitDecl",
    "SyscallDecl",
    "NirEmitter",
    "NirModule",
    "ConnectomeLoader",
    "__version__",
]
