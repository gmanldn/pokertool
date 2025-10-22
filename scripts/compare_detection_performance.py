#!/usr/bin/env python3
"""
Detection Performance Comparison Script

Benchmarks and compares detection performance across different code versions,
configurations, or algorithms. Provides statistical analysis and regression detection.

Usage:
    # Run current version benchmark
    python scripts/compare_detection_performance.py --run --output baseline.json

    # Compare against baseline
    python scripts/compare_detection_performance.py --run --compare baseline.json

    # Compare two saved benchmarks
    python scripts/compare_detection_performance.py --compare baseline.json --compare-with optimized.json

    # Run with custom iterations
    python scripts/compare_detection_performance.py --run --iterations 100

Author: PokerTool Team
Created: 2025-10-22
"""

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import traceback

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from pokertool.performance_telemetry import PerformanceTelemetry
except ImportError:
    print("Warning: Could not import PerformanceTelemetry, using mock implementation")
    PerformanceTelemetry = None


@dataclass
class BenchmarkResult:
    """Single benchmark result"""
    name: str
    iterations: int
    total_time: float
    mean_time: float
    median_time: float
    min_time: float
    max_time: float
    p95_time: float
    p99_time: float
    std_dev: float
    ops_per_second: float
    timestamp: str


@dataclass
class ComparisonResult:
    """Comparison between two benchmarks"""
    benchmark_name: str
    baseline_mean: float
    current_mean: float
    difference_ms: float
    difference_pct: float
    is_regression: bool
    is_improvement: bool
    statistical_significance: str


class PerformanceBenchmark:
    """
    Performance benchmarking system for detection operations
    """

    def __init__(self, iterations: int = 50, warmup: int = 5):
        """
        Initialize benchmark

        Args:
            iterations: Number of iterations per benchmark
            warmup: Number of warmup iterations (not measured)
        """
        self.iterations = iterations
        self.warmup = warmup
        self.results: Dict[str, BenchmarkResult] = {}

    def benchmark(self, name: str, func: Callable, *args, **kwargs) -> BenchmarkResult:
        """
        Benchmark a function

        Args:
            name: Benchmark name
            func: Function to benchmark
            *args: Function args
            **kwargs: Function kwargs

        Returns:
            BenchmarkResult
        """
        print(f"Benchmarking: {name} ({self.iterations} iterations)...", end=" ", flush=True)

        # Warmup
        for _ in range(self.warmup):
            try:
                func(*args, **kwargs)
            except Exception:
                pass

        # Measure
        times = []
        for _ in range(self.iterations):
            start = time.perf_counter()
            try:
                func(*args, **kwargs)
            except Exception:
                pass  # Continue even if function fails
            end = time.perf_counter()
            times.append(end - start)

        # Calculate statistics
        total_time = sum(times)
        mean_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0

        # Percentiles
        sorted_times = sorted(times)
        p95_idx = int(len(sorted_times) * 0.95)
        p99_idx = int(len(sorted_times) * 0.99)
        p95_time = sorted_times[p95_idx]
        p99_time = sorted_times[p99_idx]

        # Operations per second
        ops_per_second = 1.0 / mean_time if mean_time > 0 else 0.0

        result = BenchmarkResult(
            name=name,
            iterations=self.iterations,
            total_time=total_time,
            mean_time=mean_time,
            median_time=median_time,
            min_time=min_time,
            max_time=max_time,
            p95_time=p95_time,
            p99_time=p99_time,
            std_dev=std_dev,
            ops_per_second=ops_per_second,
            timestamp=datetime.now().isoformat()
        )

        self.results[name] = result
        print(f"✓ ({mean_time*1000:.2f}ms avg)")
        return result

    def save_results(self, output_path: Path):
        """Save benchmark results to JSON"""
        data = {
            "metadata": {
                "iterations": self.iterations,
                "warmup": self.warmup,
                "timestamp": datetime.now().isoformat()
            },
            "results": {name: asdict(result) for name, result in self.results.items()}
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n✓ Results saved to {output_path}")

    @staticmethod
    def load_results(input_path: Path) -> Dict[str, BenchmarkResult]:
        """Load benchmark results from JSON"""
        with open(input_path, 'r') as f:
            data = json.load(f)

        results = {}
        for name, result_data in data['results'].items():
            results[name] = BenchmarkResult(**result_data)

        return results


class PerformanceComparator:
    """
    Compare performance between two benchmark runs
    """

    # Thresholds
    REGRESSION_THRESHOLD_PCT = 5.0  # 5% slower = regression
    IMPROVEMENT_THRESHOLD_PCT = 5.0  # 5% faster = improvement
    SIGNIFICANCE_THRESHOLD_MS = 1.0  # 1ms minimum for significance

    def compare(
        self,
        baseline: Dict[str, BenchmarkResult],
        current: Dict[str, BenchmarkResult]
    ) -> List[ComparisonResult]:
        """
        Compare two benchmark runs

        Args:
            baseline: Baseline benchmark results
            current: Current benchmark results

        Returns:
            List of comparison results
        """
        comparisons = []

        # Find common benchmarks
        common_names = set(baseline.keys()) & set(current.keys())

        for name in sorted(common_names):
            baseline_result = baseline[name]
            current_result = current[name]

            baseline_mean_ms = baseline_result.mean_time * 1000
            current_mean_ms = current_result.mean_time * 1000

            difference_ms = current_mean_ms - baseline_mean_ms
            difference_pct = (difference_ms / baseline_mean_ms) * 100 if baseline_mean_ms > 0 else 0

            # Determine significance
            is_regression = (
                difference_pct > self.REGRESSION_THRESHOLD_PCT and
                abs(difference_ms) > self.SIGNIFICANCE_THRESHOLD_MS
            )
            is_improvement = (
                difference_pct < -self.IMPROVEMENT_THRESHOLD_PCT and
                abs(difference_ms) > self.SIGNIFICANCE_THRESHOLD_MS
            )

            # Statistical significance
            if abs(difference_ms) < self.SIGNIFICANCE_THRESHOLD_MS:
                significance = "negligible"
            elif abs(difference_pct) < self.REGRESSION_THRESHOLD_PCT:
                significance = "minor"
            else:
                significance = "significant"

            comparison = ComparisonResult(
                benchmark_name=name,
                baseline_mean=baseline_mean_ms,
                current_mean=current_mean_ms,
                difference_ms=difference_ms,
                difference_pct=difference_pct,
                is_regression=is_regression,
                is_improvement=is_improvement,
                statistical_significance=significance
            )

            comparisons.append(comparison)

        return comparisons

    def print_comparison(self, comparisons: List[ComparisonResult]):
        """Print comparison results in human-readable format"""
        print("\n" + "="*80)
        print("PERFORMANCE COMPARISON")
        print("="*80)

        # Summary
        regressions = [c for c in comparisons if c.is_regression]
        improvements = [c for c in comparisons if c.is_improvement]
        neutral = [c for c in comparisons if not c.is_regression and not c.is_improvement]

        print(f"\nSummary:")
        print(f"  Regressions:  {len(regressions)}")
        print(f"  Improvements: {len(improvements)}")
        print(f"  Neutral:      {len(neutral)}")

        # Regressions
        if regressions:
            print("\n⚠️  REGRESSIONS (slower than baseline):")
            print("-" * 80)
            for comp in sorted(regressions, key=lambda c: c.difference_pct, reverse=True):
                print(f"  {comp.benchmark_name}")
                print(f"    Baseline: {comp.baseline_mean:.2f}ms")
                print(f"    Current:  {comp.current_mean:.2f}ms")
                print(f"    Δ: +{comp.difference_ms:.2f}ms ({comp.difference_pct:+.1f}%)")
                print()

        # Improvements
        if improvements:
            print("\n✨ IMPROVEMENTS (faster than baseline):")
            print("-" * 80)
            for comp in sorted(improvements, key=lambda c: c.difference_pct):
                print(f"  {comp.benchmark_name}")
                print(f"    Baseline: {comp.baseline_mean:.2f}ms")
                print(f"    Current:  {comp.current_mean:.2f}ms")
                print(f"    Δ: {comp.difference_ms:.2f}ms ({comp.difference_pct:+.1f}%)")
                print()

        # Neutral (only if verbose)
        # print("\n➖ NEUTRAL (similar performance):")
        # print("-" * 80)
        # for comp in neutral:
        #     print(f"  {comp.benchmark_name}: {comp.current_mean:.2f}ms ({comp.difference_pct:+.1f}%)")

        print("="*80)

        # Exit code based on regressions
        if regressions:
            print(f"\n⚠️  WARNING: {len(regressions)} performance regression(s) detected!")
            return 1
        else:
            print("\n✓ No performance regressions detected")
            return 0


def run_detection_benchmarks(iterations: int = 50) -> PerformanceBenchmark:
    """
    Run standard detection benchmarks

    Args:
        iterations: Number of iterations per benchmark

    Returns:
        PerformanceBenchmark with results
    """
    benchmark = PerformanceBenchmark(iterations=iterations)

    # Mock detection operations for benchmarking
    # In real usage, these would call actual detection functions

    def mock_card_detection():
        """Mock card detection"""
        time.sleep(0.001)  # Simulate 1ms operation
        return ["As", "Kh"]

    def mock_pot_detection():
        """Mock pot detection"""
        time.sleep(0.0005)  # Simulate 0.5ms operation
        return 150.0

    def mock_player_detection():
        """Mock player detection"""
        time.sleep(0.002)  # Simulate 2ms operation
        return ["Player1", "Player2", "Player3"]

    def mock_full_table_scan():
        """Mock full table scan"""
        time.sleep(0.005)  # Simulate 5ms operation
        return {"cards": ["As", "Kh"], "pot": 150.0, "players": 3}

    def mock_event_deduplication():
        """Mock event deduplication check"""
        import hashlib
        import json
        data = {"pot_size": 100, "players": 6}
        json_str = json.dumps(data, sort_keys=True)
        hashlib.sha256(json_str.encode()).hexdigest()

    # Run benchmarks
    benchmark.benchmark("card_detection", mock_card_detection)
    benchmark.benchmark("pot_detection", mock_pot_detection)
    benchmark.benchmark("player_detection", mock_player_detection)
    benchmark.benchmark("full_table_scan", mock_full_table_scan)
    benchmark.benchmark("event_deduplication", mock_event_deduplication)

    return benchmark


def main():
    parser = argparse.ArgumentParser(
        description="Compare detection performance across versions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run benchmark and save results
  %(prog)s --run --output baseline.json

  # Run and compare against baseline
  %(prog)s --run --compare baseline.json

  # Compare two saved benchmarks
  %(prog)s --compare baseline.json --compare-with optimized.json

  # Run with custom iterations
  %(prog)s --run --iterations 100 --output results.json
        """
    )

    parser.add_argument(
        '--run',
        action='store_true',
        help='Run benchmarks'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=50,
        help='Number of iterations per benchmark (default: 50)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output path for benchmark results (JSON)'
    )
    parser.add_argument(
        '--compare',
        type=Path,
        help='Baseline benchmark file to compare against'
    )
    parser.add_argument(
        '--compare-with',
        type=Path,
        help='Second benchmark file (for comparing two saved benchmarks)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.run and not args.compare:
        parser.error("Must specify --run or --compare")

    if args.compare_with and not args.compare:
        parser.error("--compare-with requires --compare")

    try:
        # Run benchmarks
        current_results = None
        if args.run:
            print("Running detection performance benchmarks...")
            print(f"Iterations: {args.iterations}\n")

            benchmark = run_detection_benchmarks(iterations=args.iterations)
            current_results = benchmark.results

            # Save results
            if args.output:
                benchmark.save_results(args.output)

        # Load baseline if comparing
        baseline_results = None
        if args.compare:
            if not args.compare.exists():
                print(f"Error: Baseline file not found: {args.compare}")
                return 1

            print(f"\nLoading baseline: {args.compare}")
            baseline_results = PerformanceBenchmark.load_results(args.compare)

        # Compare
        if baseline_results and current_results:
            # Compare current run against baseline
            comparator = PerformanceComparator()
            comparisons = comparator.compare(baseline_results, current_results)
            exit_code = comparator.print_comparison(comparisons)
            return exit_code

        elif args.compare and args.compare_with:
            # Compare two saved benchmarks
            if not args.compare_with.exists():
                print(f"Error: Comparison file not found: {args.compare_with}")
                return 1

            print(f"Loading comparison: {args.compare_with}")
            current_results = PerformanceBenchmark.load_results(args.compare_with)

            comparator = PerformanceComparator()
            comparisons = comparator.compare(baseline_results, current_results)
            exit_code = comparator.print_comparison(comparisons)
            return exit_code

        return 0

    except Exception as e:
        print(f"\nError: {e}")
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
