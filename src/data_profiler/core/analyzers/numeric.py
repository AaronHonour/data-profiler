"""Numeric data analyzer with optimized statistical computations."""

from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats  # type: ignore

from data_profiler.models.config import ProfileConfig
from data_profiler.models.profile import NumericStats


class NumericAnalyzer:
    """High-performance analyzer for numeric columns."""

    @staticmethod
    def analyze(
        series: pd.Series, config: ProfileConfig
    ) -> Optional[NumericStats]:
        """
        Analyze numeric data with vectorized operations for maximum performance.

        Uses optimized NumPy/Pandas operations to compute all statistics
        in a single pass where possible.

        Args:
            series: Pandas series with numeric data
            config: Profiling configuration

        Returns:
            NumericStats object with computed statistics
        """
        # Drop nulls for statistical computation
        clean_data = series.dropna()

        if len(clean_data) == 0:
            return None

        # Convert to numpy for faster computation
        values = clean_data.to_numpy(dtype=np.float64)

        # Compute basic statistics in vectorized manner
        mean_val = float(np.mean(values))
        std_val = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
        var_val = float(np.var(values, ddof=1)) if len(values) > 1 else 0.0
        min_val = float(np.min(values))
        max_val = float(np.max(values))
        sum_val = float(np.sum(values))
        range_val = max_val - min_val

        # Compute percentiles in a single call
        percentiles = None
        q25 = q75 = q95 = q99 = median = None
        iqr = None

        if config.compute_percentiles:
            percentiles = np.percentile(
                values, [25, 50, 75, 95, 99], method="linear"
            )
            q25, median, q75, q95, q99 = map(float, percentiles)
            iqr = q75 - q25

        # Higher-order moments
        skewness = None
        kurtosis = None
        if len(values) > 2:
            skewness = float(stats.skew(values))
            kurtosis = float(stats.kurtosis(values))

        # Coefficient of variation
        cv = None
        if mean_val != 0:
            cv = std_val / abs(mean_val)

        # Outlier detection using IQR method (if enabled)
        outlier_count = None
        if config.detect_outliers and iqr is not None and q25 is not None and q75 is not None:
            lower_bound = q25 - config.outlier_threshold * iqr
            upper_bound = q75 + config.outlier_threshold * iqr
            outlier_count = int(
                np.sum((values < lower_bound) | (values > upper_bound))
            )

        # Histogram generation (optimized with numpy)
        histogram = None
        if config.histogram_bins > 0:
            counts, bin_edges = np.histogram(values, bins=config.histogram_bins)
            histogram = {
                "counts": counts.tolist(),
                "bin_edges": bin_edges.tolist(),
            }

        return NumericStats(
            mean=mean_val,
            median=median,
            std=std_val,
            variance=var_val,
            min=min_val,
            max=max_val,
            q25=q25,
            q75=q75,
            q95=q95,
            q99=q99,
            skewness=skewness,
            kurtosis=kurtosis,
            sum=sum_val,
            range=range_val,
            iqr=iqr,
            coefficient_of_variation=cv,
            outlier_count=outlier_count,
            histogram=histogram,
        )
