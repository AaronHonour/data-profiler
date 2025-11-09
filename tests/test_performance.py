"""Performance benchmarks for the profiler."""

import numpy as np
import pandas as pd
import pytest

from data_profiler.core.profiler import DataProfiler
from data_profiler.models.config import ProfileConfig


class TestPerformanceBenchmarks:
    """Performance benchmarks."""

    @pytest.mark.benchmark
    def test_benchmark_small_dataset(self, benchmark) -> None:
        """Benchmark profiling a small dataset (1K rows)."""
        np.random.seed(42)
        df = pd.DataFrame(
            {
                "id": range(1000),
                "value": np.random.normal(100, 15, 1000),
                "category": np.random.choice(["A", "B", "C", "D"], 1000),
            }
        )

        profiler = DataProfiler()
        result = benchmark(profiler.profile, df)

        assert result.row_count == 1000

    @pytest.mark.benchmark
    def test_benchmark_medium_dataset(self, benchmark) -> None:
        """Benchmark profiling a medium dataset (100K rows)."""
        np.random.seed(42)
        df = pd.DataFrame(
            {
                "id": range(100_000),
                "value1": np.random.normal(100, 15, 100_000),
                "value2": np.random.uniform(0, 1000, 100_000),
                "category": np.random.choice(["A", "B", "C", "D"], 100_000),
            }
        )

        profiler = DataProfiler()
        result = benchmark(profiler.profile, df)

        assert result.row_count == 100_000

    @pytest.mark.benchmark
    def test_benchmark_parallel_vs_sequential(self) -> None:
        """Compare parallel vs sequential processing."""
        np.random.seed(42)
        df = pd.DataFrame(
            {
                f"col_{i}": np.random.normal(100, 15, 10_000)
                for i in range(20)
            }
        )

        # Sequential
        config_seq = ProfileConfig(parallel=False)
        profiler_seq = DataProfiler(config=config_seq)
        profile_seq = profiler_seq.profile(df)

        # Parallel
        config_par = ProfileConfig(parallel=True)
        profiler_par = DataProfiler(config=config_par)
        profile_par = profiler_par.profile(df)

        # Both should produce same results
        assert profile_seq.row_count == profile_par.row_count
        assert profile_seq.column_count == profile_par.column_count

        # Log performance comparison
        print(
            f"\nSequential: {profile_seq.profiling_duration_seconds:.3f}s"
        )
        print(f"Parallel: {profile_par.profiling_duration_seconds:.3f}s")
        print(
            f"Speedup: {profile_seq.profiling_duration_seconds / profile_par.profiling_duration_seconds:.2f}x"
        )

    @pytest.mark.benchmark
    def test_benchmark_wide_dataset(self, benchmark) -> None:
        """Benchmark profiling a wide dataset (many columns)."""
        np.random.seed(42)
        df = pd.DataFrame(
            {f"col_{i}": np.random.random(1000) for i in range(100)}
        )

        profiler = DataProfiler()
        result = benchmark(profiler.profile, df)

        assert result.column_count == 100

    @pytest.mark.benchmark
    def test_benchmark_high_cardinality(self, benchmark) -> None:
        """Benchmark profiling high-cardinality categorical columns."""
        np.random.seed(42)
        df = pd.DataFrame(
            {
                "id": range(10_000),
                "high_cardinality": [f"value_{i}" for i in range(10_000)],
            }
        )

        profiler = DataProfiler()
        result = benchmark(profiler.profile, df)

        assert result.row_count == 10_000
