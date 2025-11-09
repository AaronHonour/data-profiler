"""
High-Performance Data Profiler

A production-grade data profiling library designed for exceptional speed and accuracy.
Built with modern Python, leveraging vectorized operations and optimized algorithms.
"""

__version__ = "0.1.0"

from data_profiler.core.profiler import DataProfiler
from data_profiler.models.profile import DataProfile, ColumnProfile

__all__ = ["DataProfiler", "DataProfile", "ColumnProfile"]
