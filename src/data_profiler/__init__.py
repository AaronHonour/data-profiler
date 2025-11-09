"""
High-Performance Data Profiler

A production-grade data profiling library designed for exceptional speed and accuracy.
Built with modern Python, leveraging vectorized operations and optimized algorithms.
"""

__version__ = "0.3.0"

from data_profiler.core.custom_patterns import (
    CustomPattern,
    CustomPatternDetector,
    PatternLibrary,
)
from data_profiler.core.drift_detection import (
    DatasetDrift,
    ProfileComparator,
)
from data_profiler.core.html_report import HTMLReportGenerator
from data_profiler.core.lineage import (
    LineageTracker,
    DataSource,
    DataOperation,
    DatasetNode,
    LineageGraph,
    OperationType,
)
from data_profiler.core.multi_table import (
    MultiTableAnalyzer,
    DatasetSchema,
    ForeignKeyCandidate,
)
from data_profiler.core.ml_recommendations import MLRecommendationsEngine
from data_profiler.core.profiler import DataProfiler
from data_profiler.core.recommendations import RecommendationsEngine
from data_profiler.core.schema_inference import SchemaInferenceEngine
from data_profiler.models.config import ProfileConfig
from data_profiler.models.profile import ColumnProfile, DataProfile, Recommendation

__all__ = [
    # Core profiling
    "DataProfiler",
    "DataProfile",
    "ColumnProfile",
    "ProfileConfig",
    # Schema & recommendations
    "Recommendation",
    "RecommendationsEngine",
    "MLRecommendationsEngine",
    "SchemaInferenceEngine",
    # Drift detection
    "ProfileComparator",
    "DatasetDrift",
    # Custom patterns
    "CustomPattern",
    "CustomPatternDetector",
    "PatternLibrary",
    # Multi-table analysis
    "MultiTableAnalyzer",
    "DatasetSchema",
    "ForeignKeyCandidate",
    # HTML reporting
    "HTMLReportGenerator",
    # Lineage tracking
    "LineageTracker",
    "DataSource",
    "DataOperation",
    "DatasetNode",
    "LineageGraph",
    "OperationType",
]
