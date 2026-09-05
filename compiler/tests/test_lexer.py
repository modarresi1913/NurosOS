"""Unit tests for the SynapseLang lexer."""

from synapselang.lexer import Lexer, TokenType


def test_simple_neuron_declaration():
    """The lexer should tokenize a basic `neuron` declaration."""
    src = "neuron kc[4096] : LIF(tau_m=18ms, theta=-55mV);"
    tokens = list(Lexer(src).tokens())
    types = [t.type for t in tokens]
    assert TokenType.NEURON in types
    assert TokenType.IDENT in types
    assert TokenType.LIF in types
    assert TokenType.UNIT in types
    assert tokens[-1].type == TokenType.EOF


def test_unit_suffixes():
    """Unit-suffixed literals should be tokenized as UNIT, not FLOAT/INT."""
    src = "tau_m=18ms theta=-55mV"
    tokens = [t for t in Lexer(src).tokens() if t.type == TokenType.UNIT]
    assert len(tokens) == 2
    assert tokens[0].value == "18ms"
    assert tokens[1].value == "-55mV"


def test_comments_are_skipped():
    """Comments should be ignored by the lexer (like introns in DNA)."""
    src = "// this is a comment\nneuron kc[10];"
    tokens = list(Lexer(src).tokens())
    # The first non-EOF token should be NEURON, not a comment.
    assert tokens[0].type == TokenType.NEURON


def test_arrow_operator():
    """The `->` operator should be tokenized as a single ARROW token."""
    src = "connect a -> b : dense : fixed(weight=0.5);"
    tokens = list(Lexer(src).tokens())
    arrow_tokens = [t for t in tokens if t.type == TokenType.ARROW]
    assert len(arrow_tokens) == 1


def test_keywords_recognized():
    """All SynapseLang keywords should be tokenized as their keyword type."""
    src = "circuit input output neuron connect inhibit syscall"
    tokens = [t.type for t in Lexer(src).tokens()]
    assert TokenType.CIRCUIT in tokens
    assert TokenType.INPUT in tokens
    assert TokenType.OUTPUT in tokens
    assert TokenType.INHIBIT in tokens
    assert TokenType.SYSCALL in tokens


def test_line_and_column_tracking():
    """The lexer should track line and column for error messages."""
    src = "neuron kc[10];\nneuron pn[20];"
    tokens = list(Lexer(src).tokens())
    # First `neuron` is on line 1.
    assert tokens[0].line == 1
    assert tokens[0].col == 1
    # Second `neuron` is on line 2.
    second_neuron = [t for t in tokens if t.type == TokenType.NEURON][1]
    assert second_neuron.line == 2
