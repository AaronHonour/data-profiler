"""Datetime data analyzer."""

from datetime import datetime
from typing import Optional

import pandas as pd

from data_profiler.models.config import ProfileConfig
from data_profiler.models.profile import DatetimeStats


class DatetimeAnalyzer:
    """High-performance analyzer for datetime columns."""

    @staticmethod
    def analyze(
        series: pd.Series, config: ProfileConfig
    ) -> Optional[DatetimeStats]:
        """
        Analyze datetime data with temporal statistics.

        Args:
            series: Pandas series with datetime data
            config: Profiling configuration

        Returns:
            DatetimeStats object with computed statistics
        """
        # Drop nulls
        clean_data = series.dropna()

        if len(clean_data) == 0:
            return None

        # Ensure datetime type
        if not pd.api.types.is_datetime64_any_dtype(clean_data):
            try:
                clean_data = pd.to_datetime(clean_data)
            except Exception:
                return None

        # Min and max dates
        min_date = clean_data.min()
        max_date = clean_data.max()

        # Convert to Python datetime for serialization
        min_date_py = min_date.to_pydatetime() if pd.notna(min_date) else None
        max_date_py = max_date.to_pydatetime() if pd.notna(max_date) else None

        # Date range in days
        date_range_days = None
        if pd.notna(min_date) and pd.notna(max_date):
            date_range_days = float((max_date - min_date).total_seconds() / 86400)

        # Extract components for frequency analysis
        years = clean_data.dt.year
        months = clean_data.dt.month
        days_of_week = clean_data.dt.dayofweek

        # Most common temporal components
        most_common_year = None
        most_common_month = None
        most_common_day_of_week = None

        if len(years) > 0:
            most_common_year = int(years.mode().iloc[0]) if len(years.mode()) > 0 else None

        if len(months) > 0:
            most_common_month = int(months.mode().iloc[0]) if len(months.mode()) > 0 else None

        if len(days_of_week) > 0:
            most_common_day_of_week = (
                int(days_of_week.mode().iloc[0]) if len(days_of_week.mode()) > 0 else None
            )

        return DatetimeStats(
            min_date=min_date_py,
            max_date=max_date_py,
            date_range_days=date_range_days,
            most_common_year=most_common_year,
            most_common_month=most_common_month,
            most_common_day_of_week=most_common_day_of_week,
        )
