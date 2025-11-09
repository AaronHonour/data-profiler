"""Basic usage examples for the data profiler."""

import numpy as np
import pandas as pd

from data_profiler import DataProfiler
from data_profiler.models.config import ProfileConfig


def example_basic_profiling():
    """Basic profiling example."""
    print("=" * 60)
    print("Example 1: Basic Profiling")
    print("=" * 60)

    # Create sample data
    df = pd.DataFrame(
        {
            "id": range(1000),
            "revenue": np.random.normal(1000, 200, 1000),
            "category": np.random.choice(["Electronics", "Clothing", "Food"], 1000),
            "date": pd.date_range("2023-01-01", periods=1000, freq="D"),
            "is_premium": np.random.choice([True, False], 1000),
        }
    )

    # Profile the data
    profiler = DataProfiler()
    profile = profiler.profile(df)

    # Print summary
    print(f"\nDataset Summary:")
    print(f"  Rows: {profile.row_count:,}")
    print(f"  Columns: {profile.column_count}")
    print(f"  Memory: {profile.memory_bytes / 1024:.1f} KB")
    print(f"  Profiling Time: {profile.profiling_duration_seconds:.3f}s")
    print(f"\nColumn Types: {profile.type_summary}")

    # Print column details
    print("\nColumn Details:")
    for col in profile.columns:
        print(f"\n  {col.name} ({col.type.value})")
        print(f"    Completeness: {col.quality.completeness:.1f}%")
        print(f"    Uniqueness: {col.quality.uniqueness:.1f}%")

        if col.numeric_stats:
            print(f"    Mean: {col.numeric_stats.mean:.2f}")
            print(f"    Std: {col.numeric_stats.std:.2f}")
            print(f"    Range: [{col.numeric_stats.min:.2f}, {col.numeric_stats.max:.2f}]")

        if col.categorical_stats:
            print(f"    Unique Values: {col.categorical_stats.unique_count}")
            print(f"    Mode: {col.categorical_stats.mode}")


def example_with_configuration():
    """Example with custom configuration."""
    print("\n\n" + "=" * 60)
    print("Example 2: Custom Configuration")
    print("=" * 60)

    # Create larger dataset
    df = pd.DataFrame(
        {
            "value1": np.random.random(100_000),
            "value2": np.random.normal(0, 1, 100_000),
            "text": [f"item_{i}" for i in range(100_000)],
        }
    )

    # Custom configuration
    config = ProfileConfig(
        sample_size=10_000,  # Sample for faster profiling
        parallel=True,  # Enable parallel processing
        compute_correlations=True,
        detect_outliers=True,
        histogram_bins=30,
    )

    profiler = DataProfiler(config=config)
    profile = profiler.profile(df)

    print(f"\nProfiled {profile.row_count:,} rows in {profile.profiling_duration_seconds:.3f}s")
    print(f"Throughput: {profile.row_count / profile.profiling_duration_seconds:,.0f} rows/s")

    if profile.correlation_matrix:
        print(f"\nCorrelation Matrix:")
        print(f"  Columns: {profile.correlation_matrix.columns}")


def example_data_quality():
    """Example focusing on data quality metrics."""
    print("\n\n" + "=" * 60)
    print("Example 3: Data Quality Analysis")
    print("=" * 60)

    # Create data with quality issues
    df = pd.DataFrame(
        {
            "complete": range(100),
            "has_nulls": [i if i % 5 != 0 else None for i in range(100)],
            "many_nulls": [i if i % 2 == 0 else None for i in range(100)],
            "duplicates": [i % 10 for i in range(100)],
            "unique": range(100),
        }
    )

    profiler = DataProfiler()
    profile = profiler.profile(df)

    print(f"\nData Quality Report:")
    print(f"  Total Rows: {profile.row_count}")
    print(f"  Duplicate Rows: {profile.duplicate_rows} ({profile.duplicate_row_percentage:.1f}%)")

    print("\n  Column Quality:")
    for col in profile.columns:
        print(f"\n    {col.name}:")
        print(f"      Completeness: {col.quality.completeness:.1f}%")
        print(f"      Uniqueness: {col.quality.uniqueness:.1f}%")
        print(f"      Null Count: {col.quality.null_count}")


if __name__ == "__main__":
    example_basic_profiling()
    example_with_configuration()
    example_data_quality()

    print("\n\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
