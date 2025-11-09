"""Main data profiler orchestrator."""

import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd

from data_profiler.core.analyzers import (
    CategoricalAnalyzer,
    DatetimeAnalyzer,
    NumericAnalyzer,
    TextAnalyzer,
)
from data_profiler.models.config import ProfileConfig
from data_profiler.models.profile import (
    ColumnProfile,
    ColumnType,
    CorrelationMatrix,
    DataProfile,
    DataQualityMetrics,
)


class DataProfiler:
    """
    High-performance data profiler.

    Designed for exceptional speed using:
    - Vectorized operations
    - Parallel processing
    - Efficient algorithms
    - Minimal memory allocation
    """

    def __init__(self, config: Optional[ProfileConfig] = None):
        """
        Initialize the profiler.

        Args:
            config: Optional profiling configuration. Uses defaults if not provided.
        """
        self.config = config or ProfileConfig()

    def profile(
        self,
        data: Union[pd.DataFrame, str],
        **kwargs: Dict,
    ) -> DataProfile:
        """
        Profile a dataset and return comprehensive statistics.

        Args:
            data: DataFrame or path to CSV/Parquet file
            **kwargs: Additional arguments to pass to pandas read functions

        Returns:
            DataProfile object with complete profiling results
        """
        start_time = time.perf_counter()

        # Load data if path is provided
        df = self._load_data(data, **kwargs)

        # Apply sampling if configured
        df_sample = self._apply_sampling(df)

        # Profile each column in parallel
        column_profiles = self._profile_columns(df_sample)

        # Compute dataset-level statistics
        duplicate_rows = self._count_duplicate_rows(df_sample)
        duplicate_row_pct = (duplicate_rows / len(df_sample) * 100) if len(df_sample) > 0 else 0.0

        # Correlation matrix for numeric columns
        correlation_matrix = None
        if self.config.compute_correlations:
            correlation_matrix = self._compute_correlations(df_sample)

        # Type summary
        type_summary = self._compute_type_summary(column_profiles)

        # Memory usage
        memory_bytes = int(df.memory_usage(deep=True).sum())

        # Compute profiling duration
        duration = time.perf_counter() - start_time

        return DataProfile(
            row_count=len(df),
            column_count=len(df.columns),
            memory_bytes=memory_bytes,
            columns=column_profiles,
            duplicate_rows=duplicate_rows,
            duplicate_row_percentage=duplicate_row_pct,
            correlation_matrix=correlation_matrix,
            type_summary=type_summary,
            profiling_duration_seconds=duration,
        )

    def _load_data(
        self, data: Union[pd.DataFrame, str], **kwargs: Dict
    ) -> pd.DataFrame:
        """Load data from various sources."""
        if isinstance(data, pd.DataFrame):
            return data

        # Infer file type from extension
        if data.endswith(".csv"):
            return pd.read_csv(data, **kwargs)
        elif data.endswith(".parquet"):
            return pd.read_parquet(data, **kwargs)
        elif data.endswith(".json"):
            return pd.read_json(data, **kwargs)
        else:
            # Try CSV as default
            return pd.read_csv(data, **kwargs)

    def _apply_sampling(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply sampling if dataset is large."""
        if self.config.sample_size and len(df) > self.config.sample_size:
            return df.sample(n=self.config.sample_size, random_state=42)
        return df

    def _profile_columns(self, df: pd.DataFrame) -> List[ColumnProfile]:
        """Profile all columns, optionally in parallel."""
        if self.config.parallel:
            return self._profile_columns_parallel(df)
        else:
            return [self._profile_column(df, col) for col in df.columns]

    def _profile_columns_parallel(
        self, df: pd.DataFrame
    ) -> List[ColumnProfile]:
        """Profile columns in parallel using ThreadPoolExecutor."""
        max_workers = self.config.max_workers or None
        column_profiles = [None] * len(df.columns)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all column profiling tasks
            future_to_idx = {
                executor.submit(self._profile_column, df, col): idx
                for idx, col in enumerate(df.columns)
            }

            # Collect results as they complete
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                column_profiles[idx] = future.result()

        return column_profiles  # type: ignore

    def _profile_column(
        self, df: pd.DataFrame, column_name: str
    ) -> ColumnProfile:
        """Profile a single column."""
        series = df[column_name]

        # Infer column type
        col_type = self._infer_column_type(series)

        # Compute data quality metrics
        quality = self._compute_quality_metrics(series)

        # Type-specific analysis
        numeric_stats = None
        categorical_stats = None
        text_stats = None
        datetime_stats = None

        if col_type == ColumnType.NUMERIC:
            numeric_stats = NumericAnalyzer.analyze(series, self.config)
            # Also compute categorical stats for low-cardinality numeric columns
            if numeric_stats and series.nunique() <= 20:
                categorical_stats = CategoricalAnalyzer.analyze(
                    series, self.config
                )
        elif col_type == ColumnType.CATEGORICAL:
            categorical_stats = CategoricalAnalyzer.analyze(
                series, self.config
            )
        elif col_type == ColumnType.TEXT:
            text_stats = TextAnalyzer.analyze(series, self.config)
            categorical_stats = CategoricalAnalyzer.analyze(
                series, self.config
            )
        elif col_type == ColumnType.DATETIME:
            datetime_stats = DatetimeAnalyzer.analyze(series, self.config)
        elif col_type == ColumnType.BOOLEAN:
            categorical_stats = CategoricalAnalyzer.analyze(
                series, self.config
            )

        # Memory usage
        memory_bytes = int(series.memory_usage(deep=True))

        return ColumnProfile(
            name=column_name,
            type=col_type,
            inferred_dtype=str(series.dtype),
            row_count=len(series),
            quality=quality,
            numeric_stats=numeric_stats,
            categorical_stats=categorical_stats,
            text_stats=text_stats,
            datetime_stats=datetime_stats,
            memory_bytes=memory_bytes,
        )

    def _infer_column_type(self, series: pd.Series) -> ColumnType:
        """
        Infer the semantic type of a column.

        Uses pandas dtype and statistical analysis for intelligent type detection.
        """
        dtype = series.dtype

        # Boolean
        if pd.api.types.is_bool_dtype(dtype):
            return ColumnType.BOOLEAN

        # Numeric
        if pd.api.types.is_numeric_dtype(dtype):
            return ColumnType.NUMERIC

        # Datetime
        if pd.api.types.is_datetime64_any_dtype(dtype):
            return ColumnType.DATETIME

        # Try to infer datetime from object type
        if dtype == object:
            # Sample non-null values
            sample = series.dropna().head(100)
            if len(sample) == 0:
                return ColumnType.UNKNOWN

            # Try parsing as datetime
            try:
                pd.to_datetime(sample)
                return ColumnType.DATETIME
            except Exception:
                pass

            # Check if it's text (long strings) or categorical (short, repetitive)
            str_sample = sample.astype(str)
            avg_length = str_sample.str.len().mean()
            unique_ratio = series.nunique() / len(series)

            # Heuristics for text vs categorical
            if avg_length > 50 or unique_ratio > 0.5:
                return ColumnType.TEXT
            else:
                return ColumnType.CATEGORICAL

        # Default to categorical
        return ColumnType.CATEGORICAL

    def _compute_quality_metrics(
        self, series: pd.Series
    ) -> DataQualityMetrics:
        """Compute data quality metrics for a column."""
        total_count = len(series)
        null_count = int(series.isna().sum())
        null_pct = (null_count / total_count * 100) if total_count > 0 else 0.0

        # Duplicates
        duplicate_count = int(total_count - series.nunique())
        duplicate_pct = (
            (duplicate_count / total_count * 100) if total_count > 0 else 0.0
        )

        # Completeness
        completeness = 100.0 - null_pct

        # Uniqueness
        uniqueness = (
            (series.nunique() / total_count * 100) if total_count > 0 else 0.0
        )

        return DataQualityMetrics(
            null_count=null_count,
            null_percentage=null_pct,
            duplicate_count=duplicate_count,
            duplicate_percentage=duplicate_pct,
            completeness=completeness,
            uniqueness=uniqueness,
        )

    def _count_duplicate_rows(self, df: pd.DataFrame) -> int:
        """Count duplicate rows in the dataset."""
        return int(df.duplicated().sum())

    def _compute_correlations(
        self, df: pd.DataFrame
    ) -> Optional[CorrelationMatrix]:
        """Compute correlation matrix for numeric columns."""
        # Select only numeric columns
        numeric_df = df.select_dtypes(include=[np.number])

        if numeric_df.shape[1] < 2:
            return None

        # Compute Pearson correlation
        corr_matrix = numeric_df.corr(method="pearson")

        # Convert to serializable format
        columns = corr_matrix.columns.tolist()
        matrix = corr_matrix.values.tolist()

        return CorrelationMatrix(
            columns=columns, matrix=matrix, method="pearson"
        )

    def _compute_type_summary(
        self, column_profiles: List[ColumnProfile]
    ) -> Dict[str, int]:
        """Compute count of columns by type."""
        type_counts = Counter(profile.type.value for profile in column_profiles)
        return dict(type_counts)
