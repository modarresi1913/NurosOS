"""NurosOS Benchmark Suite.

Measures:
    - Latency: tick-to-tick cycle time per organism level
    - Memory: memory growth, retrieval latency, decay effectiveness
    - Epistemic: transition validation throughput
    - Homeostatic: regulation convergence speed
    - Developmental: stage progression time
    - Safety: authorization throughput, override latency
"""

import time
import statistics
from dataclasses import dataclass, field
from typing import Any, Callable

from nuros.epistemic import EpistemicKernel, EpistemicLabel
from nuros.memory import MemoryContract, MemoryType
from nuros.homeostasis import HomeostasisKernel
from nuros.safety import SafetyKernel, Permission
from nuros.organism import Organism, OrganismConfig
from nuros.development import DevelopmentEngine
from nuros.values import ValuesContract
from nuros.imagination import ImaginationEngine


@dataclass
class BenchmarkResult:
    name: str
    iterations: int
    total_time: float
    mean_time: float
    std_time: float
    min_time: float
    max_time: float
    ops_per_second: float
    details: dict[str, Any] = field(default_factory=dict)


def benchmark(func: Callable, iterations: int = 1000, **kwargs) -> BenchmarkResult:
    """Run a benchmark function multiple times and collect statistics."""
    times = []
    result = None
    for _ in range(iterations):
        start = time.perf_counter()
        result = func(**kwargs)
        times.append(time.perf_counter() - start)
    
    total = sum(times)
    mean = statistics.mean(times)
    std = statistics.stdev(times) if len(times) > 1 else 0.0
    
    return BenchmarkResult(
        name=func.__name__,
        iterations=iterations,
        total_time=total,
        mean_time=mean,
        std_time=std,
        min_time=min(times),
        max_time=max(times),
        ops_per_second=iterations / total,
        details=result if isinstance(result, dict) else {},
    )


def bench_epistemic_observe(iterations: int = 10000) -> BenchmarkResult:
    """Benchmark epistemic observation creation."""
    ek = EpistemicKernel()
    return benchmark(lambda: ek.observe({"sensor": 1.0}), iterations=iterations)


def bench_epistemic_validate_transition(iterations: int = 10000) -> BenchmarkResult:
    """Benchmark epistemic transition validation."""
    ek = EpistemicKernel()
    rep = ek.observe({"data": 42})
    return benchmark(lambda: ek.validate_transition(EpistemicLabel.OBSERVED, EpistemicLabel.INFERRED), iterations=iterations)


def bench_memory_remember(iterations: int = 5000) -> BenchmarkResult:
    """Benchmark memory storage."""
    mem = MemoryContract()
    i = [0]
    def store():
        i[0] += 1
        return mem.remember(f"memory entry {i[0]}", importance=0.5)
    return benchmark(store, iterations=iterations)


def bench_memory_retrieve(iterations: int = 5000) -> BenchmarkResult:
    """Benchmark memory retrieval."""
    mem = MemoryContract()
    for j in range(100):
        mem.remember(f"entry {j}", importance=0.5)
    return benchmark(lambda: mem.retrieve(limit=10), iterations=iterations)


def bench_homeostasis_tick(iterations: int = 10000) -> BenchmarkResult:
    """Benchmark homeostatic regulation cycle."""
    hk = HomeostasisKernel()
    return benchmark(lambda: hk.tick(), iterations=iterations)


def bench_safety_authorize(iterations: int = 10000) -> BenchmarkResult:
    """Benchmark safety authorization."""
    sk = SafetyKernel()
    entity = "bench"
    sk.grant_permission(entity, Permission.OBSERVE)
    return benchmark(lambda: sk.authorize(entity, Permission.OBSERVE), iterations=iterations)


def bench_organism_tick(iterations: int = 1000) -> BenchmarkResult:
    """Benchmark organism tick cycle."""
    org = Organism(OrganismConfig(name="bench"))
    org.birth()
    return benchmark(lambda: org.tick(), iterations=iterations)


def bench_values_evaluation(iterations: int = 10000) -> BenchmarkResult:
    """Benchmark values contract evaluation."""
    vc = ValuesContract()
    return benchmark(lambda: vc.evaluate_action("explore", {}), iterations=iterations)


def bench_imagination_hypothesize(iterations: int = 1000) -> BenchmarkResult:
    """Benchmark imagination hypothesis generation."""
    ie = ImaginationEngine()
    return benchmark(lambda: ie.hypothesize({"state": "ok"}, ["a", "b"]), iterations=iterations)


def run_all_benchmarks(iterations: int = 5000) -> dict[str, BenchmarkResult]:
    """Run the full benchmark suite."""
    results = {}
    
    print("Running NurosOS Benchmark Suite...")
    print("=" * 60)
    
    benchmarks = [
        ("epistemic_observe", bench_epistemic_observe),
        ("epistemic_validate", bench_epistemic_validate_transition),
        ("memory_remember", bench_memory_remember),
        ("memory_retrieve", bench_memory_retrieve),
        ("homeostasis_tick", bench_homeostasis_tick),
        ("safety_authorize", bench_safety_authorize),
        ("organism_tick", bench_organism_tick),
        ("values_evaluation", bench_values_evaluation),
        ("imagination_hypothesize", bench_imagination_hypothesize),
    ]
    
    for name, func in benchmarks:
        print(f"  Benchmarking {name}...", end=" ", flush=True)
        result = func(iterations=min(iterations, 5000))
        results[name] = result
        print(f"{result.ops_per_second:.0f} ops/s")
    
    print("=" * 60)
    print("Benchmark suite complete.")
    
    return results


if __name__ == "__main__":
    results = run_all_benchmarks()
    print("\nDetailed Results:")
    for name, result in results.items():
        print(f"\n  {name}:")
        print(f"    Mean: {result.mean_time*1e6:.1f} µs")
        print(f"    Std:  {result.std_time*1e6:.1f} µs")
        print(f"    Ops/s: {result.ops_per_second:.0f}")
