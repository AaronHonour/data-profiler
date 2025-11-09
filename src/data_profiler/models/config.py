"""Configuration models for the profiler."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProfileConfig(BaseModel):
    """Configuration for data profiling operations."""

    # Performance settings
    sample_size: Optional[int] = Field(
        None,
        description="Maximum number of rows to sample for profiling. None means use all data.",
        gt=0,
    )
    parallel: bool = Field(
        True, description="Enable parallel processing for column-level profiling"
    )
    max_workers: Optional[int] = Field(
        None, description="Maximum number of worker threads. None uses CPU count."
    )

    # Statistical settings
    compute_correlations: bool = Field(
        True, description="Compute correlation matrix for numeric columns"
    )
    compute_percentiles: bool = Field(
        True, description="Compute percentile statistics (25th, 50th, 75th, 95th, 99th)"
    )
    histogram_bins: int = Field(
        50, description="Number of bins for histogram generation", gt=0, le=1000
    )

    # Cardinality estimation
    cardinality_threshold: int = Field(
        1000,
        description="Threshold for switching to HyperLogLog cardinality estimation",
        gt=0,
    )

    # Data quality
    detect_outliers: bool = Field(True, description="Detect outliers using IQR method")
    outlier_threshold: float = Field(
        1.5, description="IQR multiplier for outlier detection", gt=0
    )

    # Text analysis
    max_string_length_sample: int = Field(
        1000, description="Number of strings to sample for length analysis", gt=0
    )
    detect_patterns: bool = Field(
        True, description="Detect common patterns in text fields (email, URL, etc.)"
    )

    # Memory optimization
    chunk_size: int = Field(
        100_000,
        description="Process data in chunks of this size for large datasets",
        gt=0,
    )

    model_config = ConfigDict(frozen=False, extra="forbid")
