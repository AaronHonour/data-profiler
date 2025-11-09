"""Tests for the main DataProfiler class."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from data_profiler.core.profiler import DataProfiler
from data_profiler.models.config import ProfileConfig
from data_profiler.models.profile import ColumnType


class TestDataProfiler:
    """Tests for DataProfiler."""

    def test_profile_dataframe(self, sample_dataframe: pd.DataFrame) -> None:
        """Test profiling a DataFrame."""
        profiler = DataProfiler()
        profile = profiler.profile(sample_dataframe)

        assert profile is not None
        assert profile.row_count == len(sample_dataframe)
        assert profile.column_count == len(sample_dataframe.columns)
        assert len(profile.columns) == len(sample_dataframe.columns)
        assert profile.profiling_duration_seconds > 0

    def test_profile_csv_file(self, sample_dataframe: pd.DataFrame) -> None:
        """Test profiling a CSV file."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            csv_path = f.name
            sample_dataframe.to_csv(f, index=False)

        try:
            profiler = DataProfiler()
            profile = profiler.profile(csv_path)

            assert profile is not None
            assert profile.row_count == len(sample_dataframe)
            assert profile.column_count == len(sample_dataframe.columns)
        finally:
            Path(csv_path).unlink()

    def test_profile_parquet_file(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test profiling a Parquet file."""
        with tempfile.NamedTemporaryFile(
            suffix=".parquet", delete=False
        ) as f:
            parquet_path = f.name

        try:
            sample_dataframe.to_parquet(parquet_path)
            profiler = DataProfiler()
            profile = profiler.profile(parquet_path)

            assert profile is not None
            assert profile.row_count == len(sample_dataframe)
        finally:
            Path(parquet_path).unlink()

    def test_profile_with_sampling(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test profiling with sampling."""
        config = ProfileConfig(sample_size=100)
        profiler = DataProfiler(config=config)
        profile = profiler.profile(sample_dataframe)

        assert profile is not None
        # Original row count should be reported, not sampled
        assert profile.row_count == len(sample_dataframe)

    def test_profile_parallel_processing(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test parallel processing."""
        config = ProfileConfig(parallel=True)
        profiler = DataProfiler(config=config)
        profile = profiler.profile(sample_dataframe)

        assert profile is not None
        assert len(profile.columns) == len(sample_dataframe.columns)

    def test_profile_sequential_processing(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test sequential processing."""
        config = ProfileConfig(parallel=False)
        profiler = DataProfiler(config=config)
        profile = profiler.profile(sample_dataframe)

        assert profile is not None
        assert len(profile.columns) == len(sample_dataframe.columns)

    def test_column_type_inference(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test column type inference."""
        profiler = DataProfiler()
        profile = profiler.profile(sample_dataframe)

        # Find columns by name and check types
        column_types = {col.name: col.type for col in profile.columns}

        assert column_types["id"] == ColumnType.NUMERIC
        assert column_types["value"] == ColumnType.NUMERIC
        assert column_types["category"] == ColumnType.CATEGORICAL
        assert column_types["date"] == ColumnType.DATETIME
        assert column_types["flag"] == ColumnType.BOOLEAN

    def test_correlation_matrix(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test correlation matrix computation."""
        config = ProfileConfig(compute_correlations=True)
        profiler = DataProfiler(config=config)
        profile = profiler.profile(sample_dataframe)

        assert profile.correlation_matrix is not None
        assert len(profile.correlation_matrix.columns) > 0
        assert len(profile.correlation_matrix.matrix) > 0

    def test_duplicate_rows(self) -> None:
        """Test duplicate row detection."""
        df = pd.DataFrame(
            {
                "a": [1, 2, 3, 1, 2],
                "b": ["x", "y", "z", "x", "y"],
            }
        )
        profiler = DataProfiler()
        profile = profiler.profile(df)

        assert profile.duplicate_rows == 2  # Two duplicate rows

    def test_data_quality_metrics(
        self, sample_dataframe_with_nulls: pd.DataFrame
    ) -> None:
        """Test data quality metrics."""
        profiler = DataProfiler()
        profile = profiler.profile(sample_dataframe_with_nulls)

        # Check that quality metrics are computed
        for col_profile in profile.columns:
            assert col_profile.quality is not None
            assert col_profile.quality.completeness >= 0
            assert col_profile.quality.completeness <= 100

    def test_type_summary(self, sample_dataframe: pd.DataFrame) -> None:
        """Test type summary generation."""
        profiler = DataProfiler()
        profile = profiler.profile(sample_dataframe)

        assert profile.type_summary is not None
        assert len(profile.type_summary) > 0
        assert sum(profile.type_summary.values()) == profile.column_count

    def test_memory_usage(self, sample_dataframe: pd.DataFrame) -> None:
        """Test memory usage calculation."""
        profiler = DataProfiler()
        profile = profiler.profile(sample_dataframe)

        assert profile.memory_bytes > 0
        for col_profile in profile.columns:
            assert col_profile.memory_bytes > 0
