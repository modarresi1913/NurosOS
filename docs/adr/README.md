# ADR Index — Architectural Decision Records

This directory records every architectural decision made in NurosOS.
ADRs are immutable once merged — if a decision is reversed, write a
new ADR that supersedes the old one.

## Index

| ADR     | Title                                       | Status      |
|---------|---------------------------------------------|-------------|
| 0001    | NurosOS has no filesystem                   | Accepted    |
| 0002    | Rust over C++ for the kernel                | Accepted    |
| 0003    | SPP sparsity threshold is 5%                | Accepted    |
| 0004    | AMS replaces VFS                            | Accepted    |
| 0005    | Loihi integration plan                      | Proposed    |

## Format

Each ADR is a single Markdown file named `NNNN-title.md` where `NNNN`
is a zero-padded sequence number. The body follows this template:

```markdown
# ADR NNNN: Title

## Status
Proposed | Accepted | Rejected | Superseded by ADR NNNN

## Context
(Why is this decision being made? What is the problem?)

## Decision
(What is the change we are making?)

## Consequences
(What are the trade-offs? What becomes easier/harder?)
```
