# =============================================================================
# NurosOS — Top-level Makefile
# -----------------------------------------------------------------------------
# This Makefile orchestrates the build of the three-layer stack:
#   1. Kernel  (Rust, cargo)
#   2. SynapseLang compiler  (Python, pip)
#   3. HAL + core algorithms  (Rust workspace)
#
# It also provides bootstrap (downloads the mini-connectome dataset),
# test, benchmark, and CLI shim targets.
# =============================================================================

SHELL := /bin/bash

# ---- Configuration ----------------------------------------------------------
PROJECT_ROOT := $(shell pwd)
RUST_TOOLCHAIN ?= 1.75
PYTHON_VERSION ?= 3.10

# Mini-connectome dataset (125M synapses, ~2GB compressed).
# This mirrors the open FlyWire release v2.0 (2026).
CONNECTOME_URL  ?= https://data.nurosos.org/datasets/flywire-mini-v2.h5
CONNECTOME_SHA  ?= sha256:a3f1c4e8b9d2e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1
CONNECTOME_DEST ?= $(PROJECT_ROOT)/data/connectome/drosophila-mini.h5

# Build profile: "debug" | "release"
PROFILE ?= debug
CARGO_PROFILE := $(if $(filter release,$(PROFILE)),--release,)

# Output binaries
KERNEL_BIN := $(PROJECT_ROOT)/kernel/target/$(PROFILE)/nuros-kernel
CLI_BIN    := $(PROJECT_ROOT)/nuros-cli

# Python env
VENV       := $(PROJECT_ROOT)/.venv
PYTHON     := $(VENV)/bin/python
PIP        := $(VENV)/bin/pip

# Colors
COLOR_RESET := \033[0m
COLOR_BOLD  := \033[1m
COLOR_GREEN := \033[32m
COLOR_BLUE  := \033[34m
COLOR_YELL  := \033[33m

# ---- Default target ---------------------------------------------------------
.DEFAULT_GOAL := help

# ---- Phony targets ----------------------------------------------------------
.PHONY: help bootstrap build build-kernel build-compiler build-hal \
        test test-unit test-integration test-fly-benchmark \
        bench clean clean-data fmt lint check install-cli \
        run-emulation attach

# ---- Help -------------------------------------------------------------------
help: ## Show this help
	@echo -e "$(COLOR_BOLD)NurosOS — build targets$(COLOR_RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(COLOR_GREEN)%-22s$(COLOR_RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo -e "  $(COLOR_YELL)Profile:$(COLOR_RESET) $(PROFILE)  $(COLOR_YELL)Connectome:$(COLOR_RESET) $(CONNECTOME_DEST)"

# ---- Bootstrap: download connectome + set up toolchains --------------------
bootstrap: $(CONNECTOME_DEST) $(VENV) ## Install toolchains + download mini-connectome dataset
	@echo -e "$(COLOR_GREEN)[bootstrap]$(COLOR_RESET) Installing Rust toolchain $(RUST_TOOLCHAIN)..."
	@rustup toolchain install $(RUST_TOOLCHAIN) 2>/dev/null || true
	@echo -e "$(COLOR_GREEN)[bootstrap]$(COLOR_RESET) Bootstrapping Rust workspace..."
	@cd kernel  && cargo fetch
	@cd core    && cargo fetch
	@cd hal     && cargo fetch
	@echo -e "$(COLOR_GREEN)[bootstrap]$(COLOR_RESET) Installing SynapseLang compiler..."
	@cd compiler && $(PIP) install -e .
	@echo -e "$(COLOR_GREEN)[bootstrap]$(COLOR_RESET) Done. Try: $(COLOR_BOLD)make run-emulation$(COLOR_RESET)"

$(CONNECTOME_DEST):
	@echo -e "$(COLOR_BLUE)[bootstrap]$(COLOR_RESET) Downloading mini-connectome (~2GB)..."
	@mkdir -p $(dir $(CONNECTOME_DEST))
	@curl -L --progress-bar -o $(CONNECTOME_DEST).tmp $(CONNECTOME_URL)
	@echo "$(CONNECTOME_SHA)  $(CONNECTOME_DEST).tmp" | sha256sum -c -
	@mv $(CONNECTOME_DEST).tmp $(CONNECTOME_DEST)
	@echo -e "$(COLOR_GREEN)[bootstrap]$(COLOR_RESET) Connectome downloaded."

$(VENV):
	@echo -e "$(COLOR_BLUE)[bootstrap]$(COLOR_RESET) Creating Python venv..."
	@python$(PYTHON_VERSION) -m venv $(VENV)
	@$(PIP) install --upgrade pip wheel setuptools

# ---- Build ------------------------------------------------------------------
build: build-kernel build-compiler build-hal install-cli ## Build the entire stack

build-kernel: ## Build the NurosOS kernel (Rust)
	@echo -e "$(COLOR_BLUE)[build]$(COLOR_RESET) kernel/"
	@cd kernel && cargo build $(CARGO_PROFILE)

build-compiler: $(VENV) ## Build the SynapseLang compiler (Python wheel)
	@echo -e "$(COLOR_BLUE)[build]$(COLOR_RESET) compiler/"
	@cd compiler && $(PIP) install -e .

build-hal: ## Build the HAL + core libraries
	@echo -e "$(COLOR_BLUE)[build]$(COLOR_RESET) hal/ + core/"
	@cd hal  && cargo build $(CARGO_PROFILE)
	@cd core && cargo build $(CARGO_PROFILE)

install-cli: ## Install the nuros-cli shim
	@echo -e "$(COLOR_BLUE)[build]$(COLOR_RESET) Installing nuros-cli shim..."
	@cp scripts/nuros-cli $(CLI_BIN)
	@chmod +x $(CLI_BIN)

# ---- Test -------------------------------------------------------------------
test: test-unit test-integration test-fly-benchmark ## Run all tests

test-unit: ## Unit tests
	@echo -e "$(COLOR_BLUE)[test]$(COLOR_RESET) Unit tests..."
	@cd kernel  && cargo test --lib
	@cd core    && cargo test --lib
	@cd hal     && cargo test --lib
	@cd compiler && $(PYTHON) -m pytest tests/

test-integration: ## Integration tests across layers
	@echo -e "$(COLOR_BLUE)[test]$(COLOR_RESET) Integration tests..."
	@cd tests && cargo test

test-fly-benchmark: ## Run the Fly Benchmark behavioral suite
	@echo -e "$(COLOR_BLUE)[test]$(COLOR_RESET) Fly Benchmark suite..."
	@cd tests/fly_benchmark && cargo run --release -- --suite=all
	@$(PYTHON) tests/fly_benchmark/behavioral/score.py --json > tests/fly_benchmark/last_score.json
	@cat tests/fly_benchmark/last_score.json

# ---- Benchmark --------------------------------------------------------------
bench: ## Run performance benchmarks vs. GPU baseline
	@echo -e "$(COLOR_BLUE)[bench]$(COLOR_RESET) Running benchmarks..."
	@cd kernel && cargo bench
	@$(PYTHON) tests/benchmarks/compare_gpu.py --output tests/benchmarks/last_run.json
	@cat tests/benchmarks/last_run.json

# ---- Run --------------------------------------------------------------------
run-emulation: build ## Start NurosOS in software-emulation mode (Drosophila)
	@echo -e "$(COLOR_GREEN)[run]$(COLOR_RESET) Starting NurosOS in emulation mode..."
	@$(CLI_BIN) start --mode=emulation --target=drosophila --connectome=$(CONNECTOME_DEST)

attach: ## Attach to a running NurosOS instance (default port 8080)
	@$(CLI_BIN) attach --port=8080

# ---- Code quality -----------------------------------------------------------
fmt: ## Format all code
	@cd kernel  && cargo fmt
	@cd core    && cargo fmt
	@cd hal     && cargo fmt
	@cd compiler && $(PYTHON) -m ruff format .

lint: ## Lint all code
	@cd kernel  && cargo clippy -- -D warnings
	@cd core    && cargo clippy -- -D warnings
	@cd hal     && cargo clippy -- -D warnings
	@cd compiler && $(PYTHON) -m ruff check .

check: fmt lint ## Format + lint (CI gate)

# ---- Clean ------------------------------------------------------------------
clean: ## Remove build artifacts
	@echo -e "$(COLOR_YELL)[clean]$(COLOR_RESET) Removing build artifacts..."
	@cd kernel  && cargo clean
	@cd core    && cargo clean
	@cd hal     && cargo clean
	@rm -rf compiler/build compiler/*.egg-info
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@rm -f $(CLI_BIN)

clean-data: ## Remove the downloaded connectome dataset
	@echo -e "$(COLOR_YELL)[clean]$(COLOR_RESET) Removing connectome dataset..."
	@rm -rf $(PROJECT_ROOT)/data/
