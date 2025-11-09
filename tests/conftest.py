"""Pytest configuration and fixtures."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_numeric_data() -> pd.Series:
    """Create sample numeric data for testing."""
    np.random.seed(42)
    return pd.Series(np.random.normal(100, 15, 1000), name="test_numeric")


@pytest.fixture
def sample_categorical_data() -> pd.Series:
    """Create sample categorical data for testing."""
    return pd.Series(
        ["A", "B", "C", "A", "B", "C", "A", "D"] * 125, name="test_categorical"
    )


@pytest.fixture
def sample_text_data() -> pd.Series:
    """Create sample text data for testing."""
    return pd.Series(
        [
            "hello world",
            "test@example.com",
            "https://example.com",
            "+1-234-567-8900",
            "some longer text that exceeds normal length",
        ]
        * 200,
        name="test_text",
    )


@pytest.fixture
def sample_datetime_data() -> pd.Series:
    """Create sample datetime data for testing."""
    return pd.Series(
        pd.date_range("2020-01-01", periods=1000, freq="D"), name="test_datetime"
    )


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Create a comprehensive sample DataFrame for testing."""
    np.random.seed(42)
    return pd.DataFrame(
        {
            "id": range(1000),
            "value": np.random.normal(100, 15, 1000),
            "category": np.random.choice(["A", "B", "C", "D"], 1000),
            "date": pd.date_range("2020-01-01", periods=1000, freq="D"),
            "text": [f"text_{i}" for i in range(1000)],
            "flag": np.random.choice([True, False], 1000),
        }
    )


@pytest.fixture
def sample_dataframe_with_nulls() -> pd.DataFrame:
    """Create sample DataFrame with null values."""
    np.random.seed(42)
    df = pd.DataFrame(
        {
            "col1": np.random.normal(100, 15, 100),
            "col2": np.random.choice(["A", "B", "C", None], 100),
            "col3": [f"text_{i}" if i % 5 != 0 else None for i in range(100)],
        }
    )
    return df
