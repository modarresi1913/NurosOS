# NurosOS Examples

Sample applications built on NurosOS. Each example demonstrates one
cognitive primitive, expressed in SynapseLang and runnable on the
emulated kernel.

| Example                 | What it demonstrates                                      |
|-------------------------|-----------------------------------------------------------|
| `object_tracking/`      | Visual motion detection using the lobula plate circuit.   |
| `associative_memory/`   | Content-addressable memory using the mushroom body.       |

## Running

```bash
# Compile a SynapseLang circuit to NIR bytecode.
./nuros-cli compile examples/associative_memory/circuit.syn -o out.nir

# Start the kernel (in another terminal).
./nuros-cli start --mode=emulation --target=drosophila

# Attach and load the NIR module.
./nuros-cli attach --port=8080
> load out.nir
> stim AssociativeMemory.odor [0.0, 1.0, 0.0, 1.0, ...]
> wait until AssociativeMemory.recall stabilizes
> print AssociativeMemory.recall
```
