"""SynapseLang parser — converts a token stream into a typed AST.

Biological correspondence
-------------------------
The parser is the equivalent of **translation** in molecular biology:
the stream of codons (tokens) is read three at a time and converted
into a sequence of amino acids (AST nodes) that fold into a functional
protein (circuit). Just as the ribosome recognizes start/stop codons,
the parser recognizes keywords (`circuit`, `neuron`, `connect`) as
delimiters of structural units.

Errors at this stage correspond to **nonsense mutations** — syntactic
changes that produce non-functional output. They are caught here so
that downstream stages (lowering, codegen) can assume well-formed input.
"""

from __future__ import annotations

from synapselang.ast_nodes import (
    CircuitDecl,
    ConnectDecl,
    ConnectionSpec,
    DenseSpec,
    DopamineSpec,
    Expr,
    FixedSpec,
    HebbianSpec,
    InhibitDecl,
    LifParams,
    LifModelSpec,
    NeuronDecl,
    NeuronModelSpec,
    NirModule,
    PortDecl,
    SparseSpec,
    Statement,
    StdpSpec,
    SyscallDecl,
    UnitValue,
)
from synapselang.lexer import Lexer, Token, TokenType


class ParseError(Exception):
    """Raised when the parser encounters a syntactic error."""


class Parser:
    """A recursive-descent parser for SynapseLang.

    Grammar (simplified):

        module       := (circuit | syscall)*
        circuit      := 'circuit' IDENT '{' (port | neuron | connect | inhibit)* '}'
        port         := ('input' | 'output') IDENT '[' INT ']' ';'
        neuron       := 'neuron' IDENT '[' INT ']' ':' model ';'
        model        := 'LIF' '(' param (',' param)* ')'
        param        := IDENT '=' value
        connect      := 'connect' IDENT '->' IDENT ':' pattern ':' plasticity ';'
        pattern      := 'sparse' '(' 'density' '=' FLOAT ')' | 'dense'
        plasticity   := 'hebbian' '(' 'lr' '=' FLOAT ')'
                      | 'stdp' '(' param (',' param)* ')'
                      | 'fixed' '(' 'weight' '=' FLOAT ')'
        inhibit      := 'inhibit' IDENT ':' 'lateral' '(' 'radius' '=' INT ',' 'strength' '=' FLOAT ')' ';'
        syscall      := 'syscall' IDENT '(' params ')' '->' type '{' stmt* '}'
    """

    def __init__(self, source: str) -> None:
        self.tokens = list(Lexer(source).tokens())
        self.pos = 0

    # ------------------------------------------------------------------
    # Token helpers
    # ------------------------------------------------------------------

    @property
    def current(self) -> Token:
        """The current token (EOF if we're past the end)."""
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]

    def peek(self, offset: int = 0) -> Token:
        """Peek `offset` tokens ahead."""
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def advance(self) -> Token:
        """Consume and return the current token."""
        tok = self.current
        self.pos += 1
        return tok

    def expect(self, ttype: TokenType, what: str | None = None) -> Token:
        """Consume the current token, asserting it has the given type."""
        if self.current.type != ttype:
            expected = what or ttype.name
            raise ParseError(
                f"Expected {expected} but got {self.current.type.name} "
                f"({self.current.value!r}) at {self.current.line}:{self.current.col}"
            )
        return self.advance()

    def match(self, *ttypes: TokenType) -> bool:
        """Return True if the current token matches any of `ttypes`."""
        return self.current.type in ttypes

    # ------------------------------------------------------------------
    # Top-level
    # ------------------------------------------------------------------

    def parse(self) -> NirModule:
        """Parse the entire source file into a NirModule."""
        circuits: list[CircuitDecl] = []
        syscalls: list[SyscallDecl] = []

        while not self.match(TokenType.EOF):
            if self.match(TokenType.CIRCUIT):
                circuits.append(self._parse_circuit())
            elif self.match(TokenType.SYSCALL):
                syscalls.append(self._parse_syscall())
            else:
                raise ParseError(
                    f"Expected 'circuit' or 'syscall' but got "
                    f"{self.current.type.name} at {self.current.line}:{self.current.col}"
                )

        return NirModule(circuits=circuits, syscalls=syscalls)

    # ------------------------------------------------------------------
    # Circuit
    # ------------------------------------------------------------------

    def _parse_circuit(self) -> CircuitDecl:
        """Parse a `circuit` declaration."""
        self.expect(TokenType.CIRCUIT)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LBRACE)

        ports: list[PortDecl] = []
        neurons: list[NeuronDecl] = []
        connections: list[ConnectDecl] = []
        inhibitions: list[InhibitDecl] = []

        while not self.match(TokenType.RBRACE):
            if self.match(TokenType.INPUT, TokenType.OUTPUT):
                ports.append(self._parse_port())
            elif self.match(TokenType.NEURON):
                neurons.append(self._parse_neuron())
            elif self.match(TokenType.CONNECT):
                connections.append(self._parse_connect())
            elif self.match(TokenType.INHIBIT):
                inhibitions.append(self._parse_inhibit())
            else:
                raise ParseError(
                    f"Unexpected token {self.current.type.name} "
                    f"({self.current.value!r}) inside circuit at "
                    f"{self.current.line}:{self.current.col}"
                )

        self.expect(TokenType.RBRACE)
        return CircuitDecl(
            name=name,
            ports=ports,
            neurons=neurons,
            connections=connections,
            inhibitions=inhibitions,
        )

    def _parse_port(self) -> PortDecl:
        """Parse an `input`/`output` port."""
        direction_tok = self.advance()
        direction = "input" if direction_tok.type == TokenType.INPUT else "output"
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LBRACKET)
        size = int(self.expect(TokenType.INT).value)
        self.expect(TokenType.RBRACKET)
        self.expect(TokenType.SEMICOLON)
        return PortDecl(direction=direction, name=name, size=size)

    def _parse_neuron(self) -> NeuronDecl:
        """Parse a `neuron` declaration.

        Example:
            neuron kc[4096] : LIF(tau_m=18ms, theta=-55mV);
        """
        self.expect(TokenType.NEURON)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LBRACKET)
        count = int(self.expect(TokenType.INT).value)
        self.expect(TokenType.RBRACKET)
        self.expect(TokenType.COLON)
        model = self._parse_model()
        self.expect(TokenType.SEMICOLON)
        return NeuronDecl(name=name, count=count, model=model)

    def _parse_model(self) -> NeuronModelSpec:
        """Parse a neuron model specification (currently only `LIF`)."""
        if self.match(TokenType.LIF):
            self.advance()
            self.expect(TokenType.LPAREN)
            params = self._parse_lif_params()
            self.expect(TokenType.RPAREN)
            return LifModelSpec(model="LIF", params=params)
        raise ParseError(
            f"Unknown neuron model {self.current.value!r} at "
            f"{self.current.line}:{self.current.col}"
        )

    def _parse_lif_params(self) -> LifParams:
        """Parse the parameter list of an LIF model.

        Example: `tau_m=18ms, tau_s=5.5ms, theta=-55mV`
        """
        params = LifParams()
        # Allow empty parameter list (all defaults).
        if self.match(TokenType.RPAREN):
            return params

        while True:
            key = self.expect(TokenType.IDENT).value
            self.expect(TokenType.EQ)
            value = self._parse_value()

            # Assign to the matching field, validating the unit.
            if not hasattr(params, key):
                raise ParseError(f"Unknown LIF parameter {key!r}")
            setattr(params, key, value)

            if self.match(TokenType.COMMA):
                self.advance()
                continue
            break
        return params

    def _parse_value(self) -> Expr:
        """Parse a single parameter value (int, float, or unit value)."""
        tok = self.current
        if tok.type == TokenType.UNIT:
            self.advance()
            # Split "18ms" → (18.0, "ms").
            text = tok.value
            i = 0
            while i < len(text) and (text[i].isdigit() or text[i] in ".-"):
                i += 1
            value = float(text[:i])
            unit = text[i:]
            return UnitValue(value=value, unit=unit)
        if tok.type == TokenType.FLOAT:
            self.advance()
            return float(tok.value)
        if tok.type == TokenType.INT:
            self.advance()
            return int(tok.value)
        raise ParseError(
            f"Expected a value but got {tok.type.name} at {tok.line}:{tok.col}"
        )

    # ------------------------------------------------------------------
    # Connect
    # ------------------------------------------------------------------

    def _parse_connect(self) -> ConnectDecl:
        """Parse a `connect` declaration.

        Example:
            connect odor -> kc : sparse(density=0.05) : hebbian(lr=0.01);
        """
        self.expect(TokenType.CONNECT)
        source = self.expect(TokenType.IDENT).value
        self.expect(TokenType.ARROW)
        target = self.expect(TokenType.IDENT).value
        self.expect(TokenType.COLON)
        pattern = self._parse_pattern()
        self.expect(TokenType.COLON)
        plasticity = self._parse_plasticity()
        self.expect(TokenType.SEMICOLON)
        return ConnectDecl(
            source=source, target=target, pattern=pattern, plasticity=plasticity
        )

    def _parse_pattern(self) -> ConnectionSpec:
        """Parse a connection pattern (`sparse(density=...)` or `dense`)."""
        if self.match(TokenType.SPARSE):
            self.advance()
            self.expect(TokenType.LPAREN)
            self.expect(TokenType.IDENT)  # must be `density`
            self.expect(TokenType.EQ)
            density = float(self._parse_value())  # type: ignore[arg-type]
            self.expect(TokenType.RPAREN)
            return SparseSpec(density=density)
        if self.match(TokenType.DENSE):
            self.advance()
            return DenseSpec()
        raise ParseError(
            f"Expected 'sparse' or 'dense' but got {self.current.type.name} "
            f"at {self.current.line}:{self.current.col}"
        )

    def _parse_plasticity(self):
        """Parse a plasticity rule (`hebbian(...)`, `stdp(...)`, `fixed(...)`)."""
        if self.match(TokenType.HEBBIAN):
            self.advance()
            self.expect(TokenType.LPAREN)
            lr = 0.01
            if not self.match(TokenType.RPAREN):
                self.expect(TokenType.IDENT)  # `lr` or `learning_rate`
                self.expect(TokenType.EQ)
                lr = float(self._parse_value())  # type: ignore[arg-type]
            self.expect(TokenType.RPAREN)
            return HebbianSpec(learning_rate=lr)
        if self.match(TokenType.STDP):
            self.advance()
            self.expect(TokenType.LPAREN)
            spec = StdpSpec()
            if not self.match(TokenType.RPAREN):
                while True:
                    key = self.expect(TokenType.IDENT).value
                    self.expect(TokenType.EQ)
                    val = self._parse_value()
                    if hasattr(spec, key):
                        setattr(spec, key, val)
                    if self.match(TokenType.COMMA):
                        self.advance()
                        continue
                    break
            self.expect(TokenType.RPAREN)
            return spec
        if self.match(TokenType.FIXED):
            self.advance()
            self.expect(TokenType.LPAREN)
            self.expect(TokenType.IDENT)  # `weight`
            self.expect(TokenType.EQ)
            weight = float(self._parse_value())  # type: ignore[arg-type]
            self.expect(TokenType.RPAREN)
            return FixedSpec(weight=weight)
        raise ParseError(
            f"Expected plasticity rule but got {self.current.type.name} "
            f"at {self.current.line}:{self.current.col}"
        )

    # ------------------------------------------------------------------
    # Inhibit
    # ------------------------------------------------------------------

    def _parse_inhibit(self) -> InhibitDecl:
        """Parse an `inhibit` declaration.

        Example:
            inhibit kc : lateral(radius=5, strength=0.3);

        Biological correspondence
        -------------------------
        This mirrors lateral inhibition in the Drosophila antennal lobe:
        when one projection neuron fires, its GABAergic neighbors suppress
        surrounding neurons, sharpening the odor identity code.
        """
        self.expect(TokenType.INHIBIT)
        target = self.expect(TokenType.IDENT).value
        self.expect(TokenType.COLON)
        # Expect the keyword `lateral`.
        lateral = self.expect(TokenType.IDENT)
        if lateral.value != "lateral":
            raise ParseError(
                f"Expected 'lateral' but got {lateral.value!r} at "
                f"{lateral.line}:{lateral.col}"
            )
        self.expect(TokenType.LPAREN)
        self.expect(TokenType.IDENT)  # `radius`
        self.expect(TokenType.EQ)
        radius = int(self._parse_value())  # type: ignore[arg-type]
        self.expect(TokenType.COMMA)
        self.expect(TokenType.IDENT)  # `strength`
        self.expect(TokenType.EQ)
        strength = float(self._parse_value())  # type: ignore[arg-type]
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
        return InhibitDecl(target=target, radius=radius, strength=strength)

    # ------------------------------------------------------------------
    # Syscall
    # ------------------------------------------------------------------

    def _parse_syscall(self) -> SyscallDecl:
        """Parse a `syscall` declaration.

        Example:
            syscall memorize(odor: Tensor[256]) -> Handle {
                inject odor into AssociativeMemory.odor;
                wait until AssociativeMemory.recall stabilizes;
                return AMS.store(odor, AssociativeMemory.recall);
            }
        """
        self.expect(TokenType.SYSCALL)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LPAREN)
        params: list[tuple[str, str]] = []
        if not self.match(TokenType.RPAREN):
            while True:
                pname = self.expect(TokenType.IDENT).value
                self.expect(TokenType.COLON)
                ptype = self.expect(TokenType.IDENT).value
                # Optional `[N]` suffix for tensor types (e.g., `Tensor[256]`).
                if self.match(TokenType.LBRACKET):
                    self.advance()
                    size = self.expect(TokenType.INT).value
                    self.expect(TokenType.RBRACKET)
                    ptype = f"{ptype}[{size}]"
                params.append((pname, ptype))
                if self.match(TokenType.COMMA):
                    self.advance()
                    continue
                break
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.ARROW)
        return_type = self.expect(TokenType.IDENT).value
        # Optional `[N]` suffix for tensor return types.
        if self.match(TokenType.LBRACKET):
            self.advance()
            size = self.expect(TokenType.INT).value
            self.expect(TokenType.RBRACKET)
            return_type = f"{return_type}[{size}]"
        self.expect(TokenType.LBRACE)

        body: list[Statement] = []
        while not self.match(TokenType.RBRACE):
            body.append(self._parse_statement())
        self.expect(TokenType.RBRACE)
        return SyscallDecl(name=name, params=params, return_type=return_type, body=body)

    def _parse_statement(self) -> Statement:
        """Parse a single statement inside a syscall body."""
        if self.match(TokenType.INJECT):
            self.advance()
            var = self.expect(TokenType.IDENT).value
            self.expect(TokenType.INTO)
            target_circuit = self.expect(TokenType.IDENT).value
            self.expect(TokenType.DOT)
            target_port = self.expect(TokenType.IDENT).value
            self.expect(TokenType.SEMICOLON)
            return Statement(
                kind="inject",
                args={"var": var, "circuit": target_circuit, "port": target_port},
            )
        if self.match(TokenType.WAIT):
            self.advance()
            self.expect(TokenType.UNTIL)
            circuit = self.expect(TokenType.IDENT).value
            self.expect(TokenType.DOT)
            port = self.expect(TokenType.IDENT).value
            self.expect(TokenType.STABILIZES)
            self.expect(TokenType.SEMICOLON)
            return Statement(
                kind="wait_until",
                args={"circuit": circuit, "port": port},
            )
        if self.match(TokenType.RETURN):
            self.advance()
            # The return expression is captured as a raw string for v0.1.0.
            # In v0.2.0 we'll parse a proper expression tree.
            expr_parts: list[str] = []
            while not self.match(TokenType.SEMICOLON):
                expr_parts.append(self.advance().value)
            self.expect(TokenType.SEMICOLON)
            return Statement(kind="return", args={"expr": " ".join(expr_parts)})
        raise ParseError(
            f"Unexpected token {self.current.type.name} in syscall body at "
            f"{self.current.line}:{self.current.col}"
        )
