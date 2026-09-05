"""Unit tests for the SynapseLang parser."""

from synapselang.parser import Parser
from synapselang.ast_nodes import (
    DenseSpec,
    HebbianSpec,
    InhibitDecl,
    LifModelSpec,
    SparseSpec,
    StdpSpec,
    UnitValue,
)


def test_parse_simple_circuit():
    """The parser should handle a minimal circuit declaration."""
    src = """
    circuit Test {
        input x[10];
        output y[5];
        neuron n[100] : LIF();
        connect x -> n : dense : hebbian(lr=0.01);
    }
    """
    ast = Parser(src).parse()
    assert len(ast.circuits) == 1
    c = ast.circuits[0]
    assert c.name == "Test"
    assert len(c.ports) == 2
    assert len(c.neurons) == 1
    assert len(c.connections) == 1


def test_parse_lif_params_with_units():
    """The parser should correctly parse unit-suffixed parameters."""
    src = """
    circuit Test {
        input x[10];
        neuron n[100] : LIF(tau_m=18ms, theta=-55mV);
    }
    """
    ast = Parser(src).parse()
    neuron = ast.circuits[0].neurons[0]
    assert isinstance(neuron.model, LifModelSpec)
    params = neuron.model.params
    assert params.tau_m == UnitValue(18.0, "ms")
    assert params.theta == UnitValue(-55.0, "mV")


def test_parse_sparse_connect():
    """The parser should handle `sparse(density=...)` connectivity."""
    src = """
    circuit Test {
        input x[10];
        neuron n[100] : LIF();
        connect x -> n : sparse(density=0.05) : hebbian(lr=0.01);
    }
    """
    ast = Parser(src).parse()
    conn = ast.circuits[0].connections[0]
    assert isinstance(conn.pattern, SparseSpec)
    assert conn.pattern.density == 0.05
    assert isinstance(conn.plasticity, HebbianSpec)


def test_parse_inhibit():
    """The parser should handle `inhibit` (lateral inhibition) declarations."""
    src = """
    circuit Test {
        input x[10];
        neuron n[100] : LIF();
        inhibit n : lateral(radius=5, strength=0.3);
    }
    """
    ast = Parser(src).parse()
    inh = ast.circuits[0].inhibitions[0]
    assert isinstance(inh, InhibitDecl)
    assert inh.target == "n"
    assert inh.radius == 5
    assert inh.strength == 0.3


def test_parse_stdp_plasticity():
    """The parser should handle STDP with named parameters."""
    src = """
    circuit Test {
        input x[10];
        neuron pre[10] : LIF();
        neuron post[10] : LIF();
        connect pre -> post : dense : stdp(eta_plus=0.01, eta_minus=0.01);
    }
    """
    ast = Parser(src).parse()
    conn = ast.circuits[0].connections[0]
    assert isinstance(conn.plasticity, StdpSpec)
    assert conn.plasticity.eta_plus == 0.01
    assert conn.plasticity.eta_minus == 0.01


def test_parse_syscall():
    """The parser should handle syscall declarations."""
    src = """
    syscall memorize(odor: Tensor[256]) -> Handle {
        inject odor into Memory.odor;
        wait until Memory.recall stabilizes;
        return AMS.store(odor, Memory.recall);
    }
    """
    ast = Parser(src).parse()
    assert len(ast.syscalls) == 1
    s = ast.syscalls[0]
    assert s.name == "memorize"
    assert s.params == [("odor", "Tensor[256]")]
    assert s.return_type == "Handle"
    assert len(s.body) == 3


def test_parse_multiple_circuits():
    """The parser should handle a module with multiple circuits."""
    src = """
    circuit A {
        input x[10];
        neuron n[100] : LIF();
    }
    circuit B {
        input y[20];
        neuron m[200] : LIF();
    }
    """
    ast = Parser(src).parse()
    assert len(ast.circuits) == 2
    assert ast.circuits[0].name == "A"
    assert ast.circuits[1].name == "B"
