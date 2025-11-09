"""Profile result models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ColumnType(str, Enum):
    """Column data type classification."""

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXT = "text"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


class StatisticalTests(BaseModel):
    """Results from statistical tests."""

    tests: Dict[str, Any] = Field(
        default_factory=dict, description="Statistical test results"
    )


class DistributionFit(BaseModel):
    """Distribution fitting results."""

    distribution: str = Field(description="Distribution name")
    parameters: Dict[str, float] = Field(description="Distribution parameters")
    ks_statistic: float = Field(description="Kolmogorov-Smirnov statistic")
    p_value: float = Field(description="P-value for goodness of fit")
    aic: float = Field(description="Akaike Information Criterion")


class NumericStats(BaseModel):
    """Statistics for numeric columns."""

    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    variance: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    q25: Optional[float] = None
    q75: Optional[float] = None
    q95: Optional[float] = None
    q99: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None
    sum: Optional[float] = None
    range: Optional[float] = None
    iqr: Optional[float] = None
    coefficient_of_variation: Optional[float] = None
    outlier_count: Optional[int] = None
    histogram: Optional[Dict[str, List[float]]] = Field(
        None, description="Histogram bins and frequencies"
    )
    # Advanced statistics
    is_bimodal: Optional[bool] = None
    bimodality_coefficient: Optional[float] = None
    normality_tests: Optional[StatisticalTests] = None
    distribution_fits: Optional[List[DistributionFit]] = None
    variance_stability: Optional[Dict[str, Any]] = None


class CategoricalStats(BaseModel):
    """Statistics for categorical columns."""

    unique_count: int
    mode: Optional[Any] = None
    mode_frequency: Optional[int] = None
    top_values: Dict[str, int] = Field(
        default_factory=dict, description="Top N most frequent values"
    )
    entropy: Optional[float] = Field(None, description="Shannon entropy")
    is_unique: bool = Field(False, description="All values are unique")


class TextStats(BaseModel):
    """Statistics for text columns."""

    avg_length: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    empty_count: int = 0
    whitespace_count: int = 0
    patterns: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detected patterns (email, url, phone, etc.)",
    )
    pii_risk_level: Optional[str] = Field(
        None, description="PII risk level: high, medium, low, none"
    )


class TimeSeriesAnalysis(BaseModel):
    """Time series specific analysis."""

    has_gaps: bool = Field(False, description="Dataset has time gaps")
    gap_count: Optional[int] = None
    avg_gap_days: Optional[float] = None
    max_gap_days: Optional[float] = None
    is_regular_frequency: Optional[bool] = None
    inferred_frequency: Optional[str] = None


class DatetimeStats(BaseModel):
    """Statistics for datetime columns."""

    min_date: Optional[datetime] = None
    max_date: Optional[datetime] = None
    date_range_days: Optional[float] = None
    most_common_year: Optional[int] = None
    most_common_month: Optional[int] = None
    most_common_day_of_week: Optional[int] = None
    time_series: Optional[TimeSeriesAnalysis] = None


class DataQualityMetrics(BaseModel):
    """Data quality metrics for a column."""

    null_count: int = 0
    null_percentage: float = 0.0
    duplicate_count: int = 0
    duplicate_percentage: float = 0.0
    completeness: float = Field(100.0, description="Percentage of non-null values")
    uniqueness: float = Field(0.0, description="Percentage of unique values")
    validity: float = Field(
        100.0, description="Percentage of valid values (type-specific)"
    )


class ColumnProfile(BaseModel):
    """Complete profile for a single column."""

    name: str
    type: ColumnType
    inferred_dtype: str = Field(description="Pandas/NumPy dtype")
    row_count: int
    quality: DataQualityMetrics

    # Type-specific statistics
    numeric_stats: Optional[NumericStats] = None
    categorical_stats: Optional[CategoricalStats] = None
    text_stats: Optional[TextStats] = None
    datetime_stats: Optional[DatetimeStats] = None

    # Memory usage
    memory_bytes: int = Field(description="Approximate memory usage in bytes")

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class CorrelationMatrix(BaseModel):
    """Correlation matrix for numeric columns."""

    columns: List[str]
    matrix: List[List[float]]
    method: str = Field("pearson", description="Correlation method used")


class Recommendation(BaseModel):
    """Data quality or optimization recommendation."""

    severity: str = Field(description="Severity: critical, warning, info")
    category: str = Field(description="Category: data_quality, performance, schema, etc.")
    column: Optional[str] = Field(None, description="Related column (if applicable)")
    title: str = Field(description="Short title")
    description: str = Field(description="Detailed description")
    suggestion: Optional[str] = Field(None, description="Suggested action")


class SchemaInference(BaseModel):
    """Inferred schema for database creation."""

    columns: List[Dict[str, Any]] = Field(description="Column definitions")
    primary_key_candidates: List[str] = Field(
        default_factory=list, description="Potential primary key columns"
    )
    indexes_recommended: List[str] = Field(
        default_factory=list, description="Columns recommended for indexing"
    )


class DataProfile(BaseModel):
    """Complete profile for a dataset."""

    # Dataset metadata
    row_count: int
    column_count: int
    memory_bytes: int
    profile_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Column profiles
    columns: List[ColumnProfile]

    # Dataset-level statistics
    duplicate_rows: int = 0
    duplicate_row_percentage: float = 0.0
    correlation_matrix: Optional[CorrelationMatrix] = None

    # Summary by type
    type_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of columns by type",
    )

    # Advanced features
    recommendations: List[Recommendation] = Field(
        default_factory=list, description="Data quality and optimization recommendations"
    )
    inferred_schema: Optional[SchemaInference] = None

    # Performance metrics
    profiling_duration_seconds: float = Field(
        description="Time taken to generate profile"
    )

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )
