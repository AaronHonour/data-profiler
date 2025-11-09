"""Comprehensive benchmarking suite for the data profiler."""

import platform
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import psutil

from data_profiler import DataProfiler
from data_profiler.models.config import ProfileConfig


class BenchmarkRunner:
    """Run comprehensive benchmarks and collect performance metrics."""

    def __init__(self, output_dir: str = "benchmarks/results"):
        """Initialize benchmark runner."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[Dict] = []
        self.system_info = self._collect_system_info()

    def _collect_system_info(self) -> Dict:
        """Collect system information."""
        return {
            "platform": platform.platform(),
            "processor": platform.processor() or platform.machine(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
            "total_ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "timestamp": datetime.now().isoformat(),
        }

    def _create_dataset(
        self, rows: int, num_numeric: int = 5, num_categorical: int = 3, num_text: int = 2
    ) -> pd.DataFrame:
        """Create synthetic dataset for benchmarking."""
        np.random.seed(42)

        data = {}

        # Numeric columns
        for i in range(num_numeric):
            data[f"numeric_{i}"] = np.random.normal(1000, 200, rows)

        # Categorical columns
        for i in range(num_categorical):
            categories = [f"cat_{j}" for j in range(10)]
            data[f"category_{i}"] = np.random.choice(categories, rows)

        # Text columns
        for i in range(num_text):
            data[f"text_{i}"] = [f"text_value_{j % 100}" for j in range(rows)]

        return pd.DataFrame(data)

    def _measure_memory(self) -> float:
        """Get current process memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / (1024**2)

    def benchmark_size_scaling(self) -> None:
        """Benchmark profiling performance at various data sizes."""
        print("\n" + "=" * 70)
        print("BENCHMARK: Size Scaling")
        print("=" * 70)

        sizes = [1_000, 10_000, 50_000, 100_000, 500_000, 1_000_000]

        for size in sizes:
            print(f"\nBenchmarking {size:,} rows...")

            # Create dataset
            df = self._create_dataset(size)

            # Measure memory before
            mem_before = self._measure_memory()

            # Profile with default settings
            profiler = DataProfiler()
            start_time = time.perf_counter()
            profile = profiler.profile(df)
            duration = time.perf_counter() - start_time

            # Measure memory after
            mem_after = self._measure_memory()
            mem_used = mem_after - mem_before

            # Calculate metrics
            throughput = size / duration
            time_per_row_us = (duration / size) * 1_000_000

            result = {
                "benchmark": "size_scaling",
                "rows": size,
                "columns": df.shape[1],
                "cells": size * df.shape[1],
                "duration_seconds": round(duration, 4),
                "throughput_rows_per_sec": int(throughput),
                "time_per_row_microseconds": round(time_per_row_us, 2),
                "memory_used_mb": round(mem_used, 2),
                "dataset_memory_mb": round(df.memory_usage(deep=True).sum() / (1024**2), 2),
                "parallel": True,
            }

            self.results.append(result)

            print(f"  Duration: {duration:.4f}s")
            print(f"  Throughput: {throughput:,.0f} rows/sec")
            print(f"  Memory: {mem_used:.2f} MB")

    def benchmark_width_scaling(self) -> None:
        """Benchmark profiling performance with varying column counts."""
        print("\n" + "=" * 70)
        print("BENCHMARK: Width Scaling (Column Count)")
        print("=" * 70)

        column_counts = [5, 10, 20, 50, 100]
        fixed_rows = 10_000

        for num_cols in column_counts:
            print(f"\nBenchmarking {num_cols} columns...")

            # Create wide dataset
            df = self._create_dataset(fixed_rows, num_numeric=num_cols, num_categorical=0, num_text=0)

            mem_before = self._measure_memory()

            profiler = DataProfiler()
            start_time = time.perf_counter()
            profile = profiler.profile(df)
            duration = time.perf_counter() - start_time

            mem_after = self._measure_memory()
            mem_used = mem_after - mem_before

            throughput = fixed_rows / duration
            time_per_column_ms = (duration / num_cols) * 1000

            result = {
                "benchmark": "width_scaling",
                "rows": fixed_rows,
                "columns": num_cols,
                "cells": fixed_rows * num_cols,
                "duration_seconds": round(duration, 4),
                "throughput_rows_per_sec": int(throughput),
                "time_per_column_milliseconds": round(time_per_column_ms, 2),
                "memory_used_mb": round(mem_used, 2),
                "parallel": True,
            }

            self.results.append(result)

            print(f"  Duration: {duration:.4f}s")
            print(f"  Time per column: {time_per_column_ms:.2f}ms")

    def benchmark_parallel_vs_sequential(self) -> None:
        """Compare parallel vs sequential processing."""
        print("\n" + "=" * 70)
        print("BENCHMARK: Parallel vs Sequential Processing")
        print("=" * 70)

        test_sizes = [10_000, 100_000]
        num_columns = 20

        for size in test_sizes:
            print(f"\nBenchmarking {size:,} rows with {num_columns} columns...")

            df = self._create_dataset(size, num_numeric=num_columns, num_categorical=0, num_text=0)

            # Sequential
            config_seq = ProfileConfig(parallel=False)
            profiler_seq = DataProfiler(config=config_seq)

            start_time = time.perf_counter()
            profile_seq = profiler_seq.profile(df)
            duration_seq = time.perf_counter() - start_time

            # Parallel
            config_par = ProfileConfig(parallel=True)
            profiler_par = DataProfiler(config=config_par)

            start_time = time.perf_counter()
            profile_par = profiler_par.profile(df)
            duration_par = time.perf_counter() - start_time

            speedup = duration_seq / duration_par

            # Record sequential
            self.results.append(
                {
                    "benchmark": "parallel_comparison",
                    "rows": size,
                    "columns": num_columns,
                    "duration_seconds": round(duration_seq, 4),
                    "throughput_rows_per_sec": int(size / duration_seq),
                    "parallel": False,
                }
            )

            # Record parallel
            self.results.append(
                {
                    "benchmark": "parallel_comparison",
                    "rows": size,
                    "columns": num_columns,
                    "duration_seconds": round(duration_par, 4),
                    "throughput_rows_per_sec": int(size / duration_par),
                    "parallel": True,
                    "speedup_vs_sequential": round(speedup, 2),
                }
            )

            print(f"  Sequential: {duration_seq:.4f}s")
            print(f"  Parallel: {duration_par:.4f}s")
            print(f"  Speedup: {speedup:.2f}x")

    def benchmark_data_type_performance(self) -> None:
        """Benchmark different data type compositions."""
        print("\n" + "=" * 70)
        print("BENCHMARK: Data Type Performance")
        print("=" * 70)

        fixed_rows = 50_000
        scenarios = [
            ("numeric_only", 10, 0, 0),
            ("categorical_only", 0, 10, 0),
            ("text_only", 0, 0, 10),
            ("mixed", 5, 3, 2),
        ]

        for scenario_name, num_numeric, num_categorical, num_text in scenarios:
            print(f"\nBenchmarking {scenario_name}...")

            df = self._create_dataset(fixed_rows, num_numeric, num_categorical, num_text)

            profiler = DataProfiler()
            start_time = time.perf_counter()
            profile = profiler.profile(df)
            duration = time.perf_counter() - start_time

            throughput = fixed_rows / duration

            result = {
                "benchmark": "data_type_performance",
                "scenario": scenario_name,
                "rows": fixed_rows,
                "columns": df.shape[1],
                "num_numeric": num_numeric,
                "num_categorical": num_categorical,
                "num_text": num_text,
                "duration_seconds": round(duration, 4),
                "throughput_rows_per_sec": int(throughput),
            }

            self.results.append(result)

            print(f"  Duration: {duration:.4f}s")
            print(f"  Throughput: {throughput:,.0f} rows/sec")

    def benchmark_sampling_impact(self) -> None:
        """Benchmark impact of sampling on large datasets."""
        print("\n" + "=" * 70)
        print("BENCHMARK: Sampling Impact")
        print("=" * 70)

        large_dataset_size = 1_000_000
        sample_sizes = [None, 100_000, 50_000, 10_000]

        print(f"\nCreating large dataset ({large_dataset_size:,} rows)...")
        df = self._create_dataset(large_dataset_size)

        for sample_size in sample_sizes:
            sample_label = "full" if sample_size is None else f"{sample_size:,}"
            print(f"\nBenchmarking with sample_size={sample_label}...")

            config = ProfileConfig(sample_size=sample_size)
            profiler = DataProfiler(config=config)

            start_time = time.perf_counter()
            profile = profiler.profile(df)
            duration = time.perf_counter() - start_time

            actual_profiled = sample_size if sample_size else large_dataset_size
            throughput = large_dataset_size / duration

            result = {
                "benchmark": "sampling_impact",
                "total_rows": large_dataset_size,
                "sample_size": sample_size or large_dataset_size,
                "duration_seconds": round(duration, 4),
                "throughput_rows_per_sec": int(throughput),
                "speedup_vs_full": None,
            }

            self.results.append(result)

            print(f"  Duration: {duration:.4f}s")
            print(f"  Throughput: {throughput:,.0f} rows/sec")

        # Calculate speedups
        full_duration = next(r["duration_seconds"] for r in self.results if r["benchmark"] == "sampling_impact" and r["sample_size"] == large_dataset_size)
        for result in self.results:
            if result["benchmark"] == "sampling_impact" and result["sample_size"] != large_dataset_size:
                result["speedup_vs_full"] = round(full_duration / result["duration_seconds"], 2)

    def run_all_benchmarks(self) -> None:
        """Run all benchmark suites."""
        print("\n" + "=" * 70)
        print("DATA PROFILER PERFORMANCE BENCHMARKS")
        print("=" * 70)
        print(f"\nSystem Information:")
        print(f"  Platform: {self.system_info['platform']}")
        print(f"  Processor: {self.system_info['processor']}")
        print(f"  Python: {self.system_info['python_version']}")
        print(f"  CPU Cores: {self.system_info['physical_cores']} physical, {self.system_info['cpu_count']} logical")
        print(f"  RAM: {self.system_info['total_ram_gb']} GB")

        start_time = time.time()

        # Run all benchmarks
        self.benchmark_size_scaling()
        self.benchmark_width_scaling()
        self.benchmark_parallel_vs_sequential()
        self.benchmark_data_type_performance()
        self.benchmark_sampling_impact()

        total_time = time.time() - start_time

        print("\n" + "=" * 70)
        print(f"All benchmarks completed in {total_time:.2f} seconds")
        print("=" * 70)

    def save_results(self) -> None:
        """Save benchmark results to CSV and JSON."""
        results_df = pd.DataFrame(self.results)

        # Save CSV
        csv_path = self.output_dir / "benchmark_results.csv"
        results_df.to_csv(csv_path, index=False)
        print(f"\nResults saved to: {csv_path}")

        # Save JSON with system info
        import json

        json_path = self.output_dir / "benchmark_results.json"
        with open(json_path, "w") as f:
            json.dump(
                {"system_info": self.system_info, "results": self.results},
                f,
                indent=2,
            )
        print(f"Results saved to: {json_path}")


def main():
    """Run benchmarks and save results."""
    runner = BenchmarkRunner()
    runner.run_all_benchmarks()
    runner.save_results()


if __name__ == "__main__":
    main()
