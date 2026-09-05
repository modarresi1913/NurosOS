"""SynapseLang lexer — tokenizes .syn source files.

Biological correspondence
-------------------------
The lexer is the equivalent of **transcription** in molecular biology:
the raw DNA sequence (source code) is read and converted into a stream
of codons (tokens) that the ribosome (parser) can interpret. Just as
the genetic code is read three bases at a time, the lexer reads source
characters in chunks that form meaningful units (identifiers, numbers,
operators, keywords).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterator


class TokenType(Enum):
    """Enumeration of all SynapseLang token types."""

    # Literals
    IDENT = auto()       # identifier (variable, function name)
    INT = auto()         # integer literal: 42
    FLOAT = auto()       # float literal: 3.14
    UNIT = auto()        # unit-suffixed literal: 18ms, -55mV, 0.05

    # Keywords
    CIRCUIT = auto()     # `circuit`
    INPUT = auto()       # `input`
    OUTPUT = auto()      # `output`
    NEURON = auto()      # `neuron`
    CONNECT = auto()     # `connect`
    INHIBIT = auto()     # `inhibit`
    SYSCALL = auto()     # `syscall`
    LIF = auto()         # `LIF` (the only neuron model in v0.1.0)
    SPARSE = auto()      # `sparse`
    DENSE = auto()       # `dense`
    FIXED = auto()       # `fixed`
    HEBBIAN = auto()     # `hebbian`
    STDP = auto()        # `stdp`
    INTO = auto()        # `into`
    WAIT = auto()        # `wait`
    UNTIL = auto()       # `until`
    STABILIZES = auto()  # `stabilizes`
    RETURN = auto()      # `return`
    INJECT = auto()      # `inject`

    # Operators / punctuation
    ARROW = auto()       # `->`
    COLON = auto()       # `:`
    SEMICOLON = auto()   # `;`
    COMMA = auto()       # `,`
    DOT = auto()         # `.`
    EQ = auto()          # `=`
    LBRACE = auto()      # `{`
    RBRACE = auto()      # `}`
    LBRACKET = auto()    # `[`
    RBRACKET = auto()    # `]`
    LPAREN = auto()      # `(`
    RPAREN = auto()      # `)`

    # Special
    EOF = auto()


# Map of keyword strings to their token types. Anything that's not in
# this map but matches the identifier pattern is treated as IDENT.
_KEYWORDS: dict[str, TokenType] = {
    "circuit": TokenType.CIRCUIT,
    "input": TokenType.INPUT,
    "output": TokenType.OUTPUT,
    "neuron": TokenType.NEURON,
    "connect": TokenType.CONNECT,
    "inhibit": TokenType.INHIBIT,
    "syscall": TokenType.SYSCALL,
    "LIF": TokenType.LIF,
    "sparse": TokenType.SPARSE,
    "dense": TokenType.DENSE,
    "fixed": TokenType.FIXED,
    "hebbian": TokenType.HEBBIAN,
    "stdp": TokenType.STDP,
    "into": TokenType.INTO,
    "wait": TokenType.WAIT,
    "until": TokenType.UNTIL,
    "stabilizes": TokenType.STABILIZES,
    "return": TokenType.RETURN,
    "inject": TokenType.INJECT,
}

# Units recognized in unit-suffixed literals. Mirrors biological
# measurement scales used in electrophysiology.
_UNITS: set[str] = {"ms", "mV", "Hz", "nA", "pA", "uF"}


@dataclass(frozen=True)
class Token:
    """A single token produced by the lexer.

    Attributes:
        type: The token type.
        value: The literal text from the source.
        line: 1-indexed source line (for error messages).
        col:  1-indexed source column (for error messages).
    """

    type: TokenType
    value: str
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.col})"


class LexError(Exception):
    """Raised when the lexer encounters an invalid character."""


class Lexer:
    """Tokenizes SynapseLang source code.

    Usage:
        >>> tokens = list(Lexer("neuron kc[10] : LIF();").tokens())
        >>> tokens[0]
        Token(NEURON, 'neuron', 1:1)
    """

    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1

    def tokens(self) -> Iterator[Token]:
        """Yield tokens one at a time, ending with an EOF token."""
        while self.pos < len(self.source):
            c = self.source[self.pos]

            # Whitespace (mimics the "junk DNA" between genes — skipped).
            if c in " \t\r":
                self._advance()
                continue
            if c == "\n":
                self._advance()
                self.line += 1
                self.col = 1
                continue
            # Comments (mimics introns — non-coding regions).
            if c == "/" and self._peek(1) == "/":
                while self.pos < len(self.source) and self.source[self.pos] != "\n":
                    self._advance()
                continue

            start_line, start_col = self.line, self.col

            # Multi-character operators.
            if c == "-" and self._peek(1) == ">":
                self._advance(); self._advance()
                yield Token(TokenType.ARROW, "->", start_line, start_col)
                continue

            # Single-character punctuation.
            single_char_tokens: dict[str, TokenType] = {
                ":": TokenType.COLON,
                ";": TokenType.SEMICOLON,
                ",": TokenType.COMMA,
                ".": TokenType.DOT,
                "=": TokenType.EQ,
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
                "[": TokenType.LBRACKET,
                "]": TokenType.RBRACKET,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
            }
            if c in single_char_tokens:
                self._advance()
                yield Token(single_char_tokens[c], c, start_line, start_col)
                continue

            # Numbers (int, float, or unit-suffixed).
            # Mimics codon reading: greedy match of digits + optional
            # decimal + optional unit suffix.
            if c.isdigit() or (c == "-" and self._peek(1).isdigit()) or (c == "." and self._peek(1).isdigit()):
                yield from self._lex_number(start_line, start_col)
                continue

            # Identifiers / keywords.
            if c.isalpha() or c == "_":
                yield from self._lex_identifier(start_line, start_col)
                continue

            raise LexError(
                f"Unexpected character {c!r} at {self.line}:{self.col}"
            )

        yield Token(TokenType.EOF, "", self.line, self.col)

    def _lex_identifier(self, start_line: int, start_col: int) -> Iterator[Token]:
        """Lex an identifier or keyword."""
        start = self.pos
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == "_"):
            self._advance()
        text = self.source[start:self.pos]
        tt = _KEYWORDS.get(text, TokenType.IDENT)
        yield Token(tt, text, start_line, start_col)

    def _lex_number(self, start_line: int, start_col: int) -> Iterator[Token]:
        """Lex a numeric literal, possibly with a unit suffix.

        Examples: `42`, `-55`, `3.14`, `18ms`, `-55mV`, `0.05`
        """
        start = self.pos
        if self.source[self.pos] == "-":
            self._advance()
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            self._advance()
        is_float = False
        if self.pos < len(self.source) and self.source[self.pos] == ".":
            is_float = True
            self._advance()
            while self.pos < len(self.source) and self.source[self.pos].isdigit():
                self._advance()

        # Optional unit suffix (e.g., `ms`, `mV`).
        unit_start = self.pos
        while self.pos < len(self.source) and self.source[self.pos].isalpha():
            self._advance()
        unit = self.source[unit_start:self.pos]

        text = self.source[start:self.pos]
        if unit:
            if unit not in _UNITS:
                raise LexError(f"Unknown unit {unit!r} at {start_line}:{start_col}")
            yield Token(TokenType.UNIT, text, start_line, start_col)
        elif is_float:
            yield Token(TokenType.FLOAT, text, start_line, start_col)
        else:
            yield Token(TokenType.INT, text, start_line, start_col)

    def _advance(self) -> None:
        """Advance the position by one character."""
        self.pos += 1
        self.col += 1

    def _peek(self, offset: int) -> str:
        """Peek `offset` characters ahead without consuming."""
        idx = self.pos + offset
        if idx >= len(self.source):
            return ""
        return self.source[idx]
