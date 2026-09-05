"""Unit tests for the NIR code generator."""

import json

from synapselang.parser import Parser
from synapselang.codegen import NirEmitter


def test_compile_simple_circuit_to_json():
    """The codegen should produce valid JSON for a simple circuit."""
    src = """
    circuit Test {
        input x[10];
        output y[5];
        neuron n[100] : LIF(tau_m=18ms, theta=-55mV);
        connect x -> n : dense : hebbian(lr=0.01);
    }
    """
    ast = Parser(src).parse()
    nir = NirEmitter().emit(ast)
    data = json.loads(nir.to_json())
    assert data["version"] == "0.1.0"
    assert len(data["circuits"]) == 1
    c = data["circuits"][0]
    assert c["name"] == "Test"
    assert len(c["neurons"]) == 1
    assert c["neurons"][0]["params"]["tau_m"] == 18.0
    assert c["neurons"][0]["params"]["theta"] == -55.0


def test_compile_to_msgpack_round_trip():
    """The codegen should produce msgpack that can be re-parsed."""
    import msgpack

    src = """
    circuit Test {
        input x[10];
        neuron n[100] : LIF();
        connect x -> n : sparse(density=0.05) : hebbian(lr=0.01);
    }
    """
    ast = Parser(src).parse()
    nir = NirEmitter().emit(ast)
    packed = nir.to_msgpack()
    unpacked = msgpack.unpackb(packed, raw=False)
    assert unpacked["version"] == "0.1.0"
    assert unpacked["circuits"][0]["name"] == "Test"


def test_unit_validation_in_codegen():
    """The codegen should reject parameters with wrong units.

    A time constant must be in `ms`, a voltage must be in `mV`. This
    mimics biological scale-checking — a neuron with `tau_m=18mV` would
    be nonsense.
    """
    src = """
    circuit Test {
        input x[10];
        neuron n[100] : LIF(tau_m=18mV);
    }
    """
    ast = Parser(src).parse()
    emitter = NirEmitter()
    try:
        emitter.emit(ast)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "ms" in str(e)
