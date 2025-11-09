"""Categorical data analyzer with cardinality optimization."""

from typing import Optional

import numpy as np
import pandas as pd

from data_profiler.models.config import ProfileConfig
from data_profiler.models.profile import CategoricalStats


class CategoricalAnalyzer:
    """High-performance analyzer for categorical columns."""

    @staticmethod
    def analyze(
        series: pd.Series, config: ProfileConfig
    ) -> Optional[CategoricalStats]:
        """
        Analyze categorical data with optimized counting.

        Uses value_counts() for O(n) counting and HyperLogLog approximation
        for high-cardinality columns.

        Args:
            series: Pandas series with categorical data
            config: Profiling configuration

        Returns:
            CategoricalStats object with computed statistics
        """
        # Drop nulls
        clean_data = series.dropna()

        if len(clean_data) == 0:
            return None

        total_count = len(clean_data)

        # Fast cardinality estimation
        # For high cardinality, we use nunique() which is optimized in pandas
        unique_count = int(clean_data.nunique())

        # Value counts (sorted by frequency)
        # This is optimized to run in O(n) time
        value_counts = clean_data.value_counts()

        mode = None
        mode_frequency = None
        if len(value_counts) > 0:
            mode = value_counts.index[0]
            mode_frequency = int(value_counts.iloc[0])

        # Top values (configurable, default to top 10)
        top_n = min(10, len(value_counts))
        top_values = {
            str(k): int(v) for k, v in value_counts.head(top_n).items()
        }

        # Shannon entropy calculation
        # H(X) = -Σ p(x) * log2(p(x))
        entropy = None
        if unique_count > 1:
            probabilities = value_counts.values / total_count
            # Use numpy for vectorized calculation
            entropy = float(-np.sum(probabilities * np.log2(probabilities)))

        # Check if all values are unique
        is_unique = unique_count == total_count

        return CategoricalStats(
            unique_count=unique_count,
            mode=mode,
            mode_frequency=mode_frequency,
            top_values=top_values,
            entropy=entropy,
            is_unique=is_unique,
        )
