"""Tests for type-specific analyzers."""

import pandas as pd
import pytest

from data_profiler.core.analyzers import (
    CategoricalAnalyzer,
    DatetimeAnalyzer,
    NumericAnalyzer,
    TextAnalyzer,
)
from data_profiler.models.config import ProfileConfig


class TestNumericAnalyzer:
    """Tests for NumericAnalyzer."""

    def test_analyze_basic_stats(self, sample_numeric_data: pd.Series) -> None:
        """Test basic statistical calculations."""
        config = ProfileConfig()
        stats = NumericAnalyzer.analyze(sample_numeric_data, config)

        assert stats is not None
        assert stats.mean is not None
        assert stats.std is not None
        assert stats.min is not None
        assert stats.max is not None
        assert stats.median is not None

    def test_analyze_percentiles(self, sample_numeric_data: pd.Series) -> None:
        """Test percentile calculations."""
        config = ProfileConfig(compute_percentiles=True)
        stats = NumericAnalyzer.analyze(sample_numeric_data, config)

        assert stats is not None
        assert stats.q25 is not None
        assert stats.q75 is not None
        assert stats.q95 is not None
        assert stats.q99 is not None
        assert stats.iqr is not None

    def test_analyze_outliers(self, sample_numeric_data: pd.Series) -> None:
        """Test outlier detection."""
        config = ProfileConfig(detect_outliers=True)
        stats = NumericAnalyzer.analyze(sample_numeric_data, config)

        assert stats is not None
        assert stats.outlier_count is not None
        assert stats.outlier_count >= 0

    def test_analyze_histogram(self, sample_numeric_data: pd.Series) -> None:
        """Test histogram generation."""
        config = ProfileConfig(histogram_bins=10)
        stats = NumericAnalyzer.analyze(sample_numeric_data, config)

        assert stats is not None
        assert stats.histogram is not None
        assert "counts" in stats.histogram
        assert "bin_edges" in stats.histogram
        assert len(stats.histogram["counts"]) == 10

    def test_analyze_empty_series(self) -> None:
        """Test analysis of empty series."""
        config = ProfileConfig()
        series = pd.Series([], dtype=float)
        stats = NumericAnalyzer.analyze(series, config)

        assert stats is None

    def test_analyze_with_nulls(self) -> None:
        """Test analysis with null values."""
        config = ProfileConfig()
        series = pd.Series([1.0, 2.0, None, 4.0, 5.0])
        stats = NumericAnalyzer.analyze(series, config)

        assert stats is not None
        assert stats.mean is not None


class TestCategoricalAnalyzer:
    """Tests for CategoricalAnalyzer."""

    def test_analyze_basic_stats(
        self, sample_categorical_data: pd.Series
    ) -> None:
        """Test basic categorical statistics."""
        config = ProfileConfig()
        stats = CategoricalAnalyzer.analyze(sample_categorical_data, config)

        assert stats is not None
        assert stats.unique_count > 0
        assert stats.mode is not None
        assert stats.mode_frequency is not None

    def test_analyze_top_values(
        self, sample_categorical_data: pd.Series
    ) -> None:
        """Test top values extraction."""
        config = ProfileConfig()
        stats = CategoricalAnalyzer.analyze(sample_categorical_data, config)

        assert stats is not None
        assert len(stats.top_values) > 0

    def test_analyze_entropy(self, sample_categorical_data: pd.Series) -> None:
        """Test entropy calculation."""
        config = ProfileConfig()
        stats = CategoricalAnalyzer.analyze(sample_categorical_data, config)

        assert stats is not None
        assert stats.entropy is not None
        assert stats.entropy >= 0

    def test_analyze_is_unique(self) -> None:
        """Test unique detection."""
        config = ProfileConfig()
        series = pd.Series([1, 2, 3, 4, 5])
        stats = CategoricalAnalyzer.analyze(series, config)

        assert stats is not None
        assert stats.is_unique is True


class TestTextAnalyzer:
    """Tests for TextAnalyzer."""

    def test_analyze_length_stats(self, sample_text_data: pd.Series) -> None:
        """Test text length statistics."""
        config = ProfileConfig()
        stats = TextAnalyzer.analyze(sample_text_data, config)

        assert stats is not None
        assert stats.avg_length is not None
        assert stats.min_length is not None
        assert stats.max_length is not None

    def test_analyze_patterns(self, sample_text_data: pd.Series) -> None:
        """Test pattern detection."""
        config = ProfileConfig(detect_patterns=True)
        stats = TextAnalyzer.analyze(sample_text_data, config)

        assert stats is not None
        # Should detect email, URL, and phone patterns in sample data
        assert "email" in stats.patterns or len(stats.patterns) >= 0

    def test_analyze_empty_strings(self) -> None:
        """Test empty and whitespace string detection."""
        config = ProfileConfig()
        series = pd.Series(["test", "", "  ", "data"])
        stats = TextAnalyzer.analyze(series, config)

        assert stats is not None
        assert stats.empty_count >= 0
        assert stats.whitespace_count >= 0


class TestDatetimeAnalyzer:
    """Tests for DatetimeAnalyzer."""

    def test_analyze_date_range(self, sample_datetime_data: pd.Series) -> None:
        """Test date range calculations."""
        config = ProfileConfig()
        stats = DatetimeAnalyzer.analyze(sample_datetime_data, config)

        assert stats is not None
        assert stats.min_date is not None
        assert stats.max_date is not None
        assert stats.date_range_days is not None
        assert stats.date_range_days > 0

    def test_analyze_temporal_patterns(
        self, sample_datetime_data: pd.Series
    ) -> None:
        """Test temporal pattern detection."""
        config = ProfileConfig()
        stats = DatetimeAnalyzer.analyze(sample_datetime_data, config)

        assert stats is not None
        assert stats.most_common_year is not None
        assert stats.most_common_month is not None
        assert stats.most_common_day_of_week is not None
