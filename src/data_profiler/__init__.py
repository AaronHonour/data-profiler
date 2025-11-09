"""
High-Performance Data Profiler

A production-grade data profiling library designed for exceptional speed and accuracy.
Built with modern Python, leveraging vectorized operations and optimized algorithms.
"""

__version__ = "0.2.0"

from data_profiler.core.profiler import DataProfiler
from data_profiler.core.schema_inference import SchemaInferenceEngine
from data_profiler.models.config import ProfileConfig
from data_profiler.models.profile import ColumnProfile, DataProfile, Recommendation

__all__ = [
    "DataProfiler",
    "DataProfile",
    "ColumnProfile",
    "ProfileConfig",
    "Recommendation",
    "SchemaInferenceEngine",
]
