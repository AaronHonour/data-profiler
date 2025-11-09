"""Time series analysis for datetime columns."""

from typing import Optional

import numpy as np
import pandas as pd

from data_profiler.models.profile import TimeSeriesAnalysis


class TimeSeriesAnalyzer:
    """Analyze time series patterns in datetime data."""

    @staticmethod
    def analyze(series: pd.Series) -> Optional[TimeSeriesAnalysis]:
        """
        Analyze datetime series for time series patterns.

        Args:
            series: Pandas series with datetime data

        Returns:
            TimeSeriesAnalysis object or None
        """
        # Drop nulls
        clean_data = series.dropna()

        if len(clean_data) < 2:
            return None

        # Ensure datetime type
        if not pd.api.types.is_datetime64_any_dtype(clean_data):
            try:
                clean_data = pd.to_datetime(clean_data)
            except Exception:
                return None

        # Sort for time series analysis
        sorted_data = clean_data.sort_values()

        # Detect gaps
        has_gaps, gap_stats = TimeSeriesAnalyzer._detect_gaps(sorted_data)

        # Infer frequency
        is_regular, frequency = TimeSeriesAnalyzer._infer_frequency(sorted_data)

        return TimeSeriesAnalysis(
            has_gaps=has_gaps,
            gap_count=gap_stats.get("count"),
            avg_gap_days=gap_stats.get("avg_days"),
            max_gap_days=gap_stats.get("max_days"),
            is_regular_frequency=is_regular,
            inferred_frequency=frequency,
        )

    @staticmethod
    def _detect_gaps(sorted_series: pd.Series) -> tuple[bool, dict]:
        """
        Detect gaps in time series.

        Args:
            sorted_series: Sorted datetime series

        Returns:
            Tuple of (has_gaps, gap_statistics)
        """
        # Calculate differences
        diffs = sorted_series.diff()[1:]  # Skip first NaT

        if len(diffs) == 0:
            return False, {}

        # Convert to days
        diff_days = diffs.dt.total_seconds() / 86400

        # Find median difference
        median_diff = diff_days.median()

        # Gaps are differences significantly larger than median (2x threshold)
        threshold = median_diff * 2 if median_diff > 0 else 1

        gaps = diff_days[diff_days > threshold]

        has_gaps = len(gaps) > 0

        gap_stats = {}
        if has_gaps:
            gap_stats["count"] = int(len(gaps))
            gap_stats["avg_days"] = float(gaps.mean())
            gap_stats["max_days"] = float(gaps.max())

        return has_gaps, gap_stats

    @staticmethod
    def _infer_frequency(sorted_series: pd.Series) -> tuple[bool, Optional[str]]:
        """
        Infer the frequency of a time series.

        Args:
            sorted_series: Sorted datetime series

        Returns:
            Tuple of (is_regular, frequency_string)
        """
        # Calculate differences
        diffs = sorted_series.diff()[1:]

        if len(diffs) == 0:
            return False, None

        # Convert to seconds
        diff_seconds = diffs.dt.total_seconds()

        # Check if differences are consistent (coefficient of variation < 0.1)
        cv = diff_seconds.std() / diff_seconds.mean() if diff_seconds.mean() > 0 else float("inf")

        is_regular = cv < 0.1

        if not is_regular:
            return False, None

        # Infer frequency based on median difference
        median_seconds = diff_seconds.median()

        # Common frequencies
        if abs(median_seconds - 1) < 0.5:  # ~1 second
            return True, "S"  # Second
        elif abs(median_seconds - 60) < 10:  # ~1 minute
            return True, "T"  # Minute
        elif abs(median_seconds - 3600) < 300:  # ~1 hour
            return True, "H"  # Hour
        elif abs(median_seconds - 86400) < 3600:  # ~1 day
            return True, "D"  # Day
        elif abs(median_seconds - 604800) < 86400:  # ~1 week
            return True, "W"  # Week
        elif abs(median_seconds - 2592000) < 259200:  # ~1 month (30 days)
            return True, "M"  # Month
        elif abs(median_seconds - 31536000) < 2592000:  # ~1 year
            return True, "Y"  # Year
        else:
            # Custom frequency
            return True, f"{int(median_seconds)}S"
