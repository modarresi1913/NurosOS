# SynapseLang — Compiler for Cognitive Circuits

SynapseLang is a domain-specific language (DSL) that compiles high-level cognitive functions (e.g., pattern recognition, associative memory) into a weighted graph of excitatory/inhibitory connections. The output is hardware-agnostic bytecode (NIR — Neuromorphic Intermediate Representation) that can run on the NurosOS kernel or be re-targeted to Intel Loihi, IBM TrueNorth, or custom FPGA arrays.

## Example

```synapse
// A sparse associative memory circuit, modeled after the
// Drosophila mushroom body. Stores up to 1024 patterns of dimension 256.

circuit AssociativeMemory {
    input  odor[256];            // Sensory afferent (ORNs)
    output recall[256];          // Motor efferent (recall)

    // αβ Kenyon cells — sparse, high-dimensional odor coding.
    // ~5% active at any time (matches biological sparsity).
    neuron kc[4096] : LIF(
        tau_m=18ms, tau_s=5.5ms,
        theta=-55mV, v_rest=-70mV
    );

    // Mushroom Body Output Neurons — approach/avoid valence.
    neuron mbon[16] : LIF(
        tau_m=10ms, theta=-50mV
    );

    // ORN → KC: random sparse projections (1:5 ratio, like the fly).
    connect odor -> kc : sparse(density=0.05) : hebbian(lr=0.01);

    // KC → MBON: dense, plastic (this is where learning happens).
    connect kc -> mbon : dense : stdp(
        eta_plus=0.01, eta_minus=0.01,
        tau_plus=20ms, tau_minus=20ms
    );

    // MBON → recall: linear projection.
    connect mbon -> recall : dense : fixed(weight=0.5);

    // Lateral inhibition in the antennal lobe — sharpens odor identity.
    inhibit kc : lateral(radius=5, strength=0.3);
}

// A behavioral system call — wraps the circuit as a queryable API.
syscall memorize(odor: Tensor[256]) -> Handle {
    inject odor into AssociativeMemory.odor;
    wait until AssociativeMemory.recall stabilizes;
    return AMS.store(odor, AssociativeMemory.recall);
}
```

## Status

| Feature                        | Status      |
|--------------------------------|-------------|
| Tokenizer + Lexer              | ✅ v0.1.0    |
| Parser (full AST)              | ✅ v0.1.0    |
| NIR bytecode emitter           | ✅ v0.1.0    |
| Connectome .h5 loader          | 🚧 v0.2.0    |
| SynapseLang → Loihi backend    | 🚧 v0.3.0    |
| SynapseLang → FPGA backend     | 🚧 v0.3.0    |

## Usage

```bash
# Compile a .syn file to NIR bytecode
python -m synapselang.cli compile examples/associative_memory/circuit.syn -o out.nir

# Inspect a connectome .h5 file
python -m synapselang.cli inspect data/connectome/drosophila-mini.h5

# Start an interactive SynapseLang shell (connects to running kernel)
python -m synapselang.shell --host=127.0.0.1 --port=8080
```

## Architecture

```
.syn source file
       │
       ▼
   ┌────────┐
   │  Lexer │  ── tokens
   └────┬───┘
        │
       ▼
   ┌────────┐
   │ Parser │  ── AST (typed, validated by pydantic)
   └────┬───┘
        │
       ▼
   ┌────────────┐
   │ Lowering   │  ── builds the Neuron/Synapse graph
   └────┬───────┘
        │
       ▼
   ┌────────────┐
   │ NIR Emitter│  ── produces .nir bytecode (msgpack)
   └────────────┘
```

See `synapselang/` for the source.
