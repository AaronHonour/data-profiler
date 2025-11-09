"""Text data analyzer with pattern detection."""

import re
from typing import Optional

import pandas as pd

from data_profiler.core.pattern_detector import PatternDetector
from data_profiler.models.config import ProfileConfig
from data_profiler.models.profile import TextStats


class TextAnalyzer:
    """High-performance analyzer for text columns."""

    # Compiled regex patterns for common formats (compiled once for performance)
    PATTERNS = {
        "email": re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        ),
        "url": re.compile(
            r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?$"
        ),
        "phone": re.compile(
            r"^[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}$"
        ),
        "ipv4": re.compile(
            r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
        ),
        "uuid": re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        ),
    }

    @staticmethod
    def analyze(
        series: pd.Series, config: ProfileConfig
    ) -> Optional[TextStats]:
        """
        Analyze text data with length statistics and pattern detection.

        Uses vectorized string operations for performance.

        Args:
            series: Pandas series with text data
            config: Profiling configuration

        Returns:
            TextStats object with computed statistics
        """
        # Convert to string type if not already
        str_series = series.astype(str)

        # Count empty and whitespace-only strings
        empty_count = int((str_series == "").sum())
        whitespace_count = int(str_series.str.isspace().sum())

        # Drop nulls and empty strings for length analysis
        clean_data = series.dropna()
        if len(clean_data) == 0:
            return TextStats(
                empty_count=empty_count,
                whitespace_count=whitespace_count,
            )

        # Convert to string
        clean_str = clean_data.astype(str)

        # Vectorized length calculation
        lengths = clean_str.str.len()
        avg_length = float(lengths.mean())
        min_length = int(lengths.min())
        max_length = int(lengths.max())

        # Pattern detection (sample for performance)
        patterns = {}
        pii_risk = None

        if config.detect_patterns:
            if config.detect_pii:
                # Use enhanced pattern detector with PII detection
                patterns = PatternDetector.detect_all_patterns(
                    series, config.max_string_length_sample
                )
                pii_risk = PatternDetector.detect_pii_risk(patterns)
            else:
                # Use basic pattern detection
                sample_size = min(
                    config.max_string_length_sample, len(clean_str)
                )
                sample = clean_str.sample(n=sample_size, random_state=42)

                for pattern_name, pattern_regex in TextAnalyzer.PATTERNS.items():
                    # Vectorized pattern matching
                    matches = sample.str.match(pattern_regex, na=False)
                    match_count = int(matches.sum())
                    if match_count > 0:
                        # Extrapolate to full dataset
                        estimated_count = int(
                            (match_count / sample_size) * len(clean_str)
                        )
                        patterns[pattern_name] = estimated_count

        return TextStats(
            avg_length=avg_length,
            min_length=min_length,
            max_length=max_length,
            empty_count=empty_count,
            whitespace_count=whitespace_count,
            patterns=patterns,
            pii_risk_level=pii_risk,
        )
