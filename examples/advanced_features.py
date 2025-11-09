"""Examples demonstrating advanced profiling features."""

import numpy as np
import pandas as pd

from data_profiler import DataProfiler, ProfileConfig, SchemaInferenceEngine


def example_advanced_statistics():
    """Demonstrate advanced statistical analysis."""
    print("=" * 70)
    print("Example: Advanced Statistical Analysis")
    print("=" * 70)

    # Create data with different distributions
    np.random.seed(42)
    df = pd.DataFrame(
        {
            "normal_dist": np.random.normal(100, 15, 1000),
            "skewed_dist": np.random.exponential(50, 1000),
            "bimodal": np.concatenate(
                [np.random.normal(50, 10, 500), np.random.normal(150, 10, 500)]
            ),
        }
    )

    # Enable advanced statistics
    config = ProfileConfig(advanced_stats=True)
    profiler = DataProfiler(config=config)
    profile = profiler.profile(df)

    print(f"\nProfiled {profile.row_count:,} rows in {profile.profiling_duration_seconds:.3f}s")

    for col in profile.columns:
        if col.numeric_stats:
            print(f"\n{col.name}:")
            print(f"  Mean: {col.numeric_stats.mean:.2f}")
            print(f"  Std: {col.numeric_stats.std:.2f}")

            if col.numeric_stats.is_bimodal:
                print(f"  ⚠️  Bimodal distribution detected!")
                print(f"  Bimodality coefficient: {col.numeric_stats.bimodality_coefficient:.3f}")

            if col.numeric_stats.normality_tests:
                tests = col.numeric_stats.normality_tests.tests
                if "shapiro_wilk" in tests:
                    is_normal = tests["shapiro_wilk"].get("is_normal", False)
                    p_value = tests["shapiro_wilk"].get("p_value", 0)
                    print(f"  Normality: {'Normal' if is_normal else 'Non-normal'} (p={p_value:.4f})")

            if col.numeric_stats.distribution_fits:
                print("  Best fitting distributions:")
                for i, fit in enumerate(col.numeric_stats.distribution_fits[:2], 1):
                    print(f"    {i}. {fit.distribution} (AIC={fit.aic:.2f})")


def example_pii_detection():
    """Demonstrate PII detection."""
    print("\n\n" + "=" * 70)
    print("Example: PII Detection")
    print("=" * 70)

    # Create data with PII
    df = pd.DataFrame(
        {
            "name": ["John Doe", "Jane Smith", "Bob Johnson"],
            "email": ["john@example.com", "jane@example.com", "bob@example.com"],
            "phone": ["+1-555-123-4567", "+1-555-987-6543", "+1-555-555-5555"],
            "notes": ["Regular customer", "VIP member", "New signup"],
        }
    )

    # Enable PII detection
    config = ProfileConfig(detect_pii=True)
    profiler = DataProfiler(config=config)
    profile = profiler.profile(df)

    print(f"\nPII Risk Assessment:")
    for col in profile.columns:
        if col.text_stats and col.text_stats.pii_risk_level:
            risk = col.text_stats.pii_risk_level
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢", "none": "⚪"}.get(risk, "⚪")
            print(f"  {icon} {col.name}: {risk.upper()} risk")

            if col.text_stats.patterns:
                print(f"     Patterns detected: {list(col.text_stats.patterns.keys())}")


def example_schema_inference():
    """Demonstrate schema inference and DDL generation."""
    print("\n\n" + "=" * 70)
    print("Example: Schema Inference & DDL Generation")
    print("=" * 70)

    # Create sample data
    np.random.seed(42)
    df = pd.DataFrame(
        {
            "user_id": range(1, 101),
            "username": [f"user{i}" for i in range(1, 101)],
            "age": np.random.randint(18, 65, 100),
            "balance": np.random.uniform(0, 10000, 100),
            "signup_date": pd.date_range("2023-01-01", periods=100, freq="D"),
            "is_active": np.random.choice([True, False], 100),
        }
    )

    # Enable schema inference
    config = ProfileConfig(infer_schema=True)
    profiler = DataProfiler(config=config)
    profile = profiler.profile(df)

    if profile.schema:
        print("\nInferred Schema:")
        print(f"  Primary Key Candidates: {profile.schema.primary_key_candidates}")
        print(f"  Recommended Indexes: {profile.schema.indexes_recommended}")

        print("\nColumn Definitions:")
        for col in profile.schema.columns:
            nullable = "NULL" if col["nullable"] else "NOT NULL"
            unique = "UNIQUE" if col.get("unique") else ""
            print(f"  {col['name']}: {col['type']} {nullable} {unique}")

        # Generate DDL
        ddl = SchemaInferenceEngine.generate_ddl(profile.schema, "users")
        print("\nGenerated DDL:")
        print(ddl)


def example_recommendations():
    """Demonstrate recommendations engine."""
    print("\n\n" + "=" * 70)
    print("Example: Data Quality Recommendations")
    print("=" * 70)

    # Create data with quality issues
    np.random.seed(42)
    df = pd.DataFrame(
        {
            "complete_col": range(100),
            "mostly_null": [i if i % 10 == 0 else None for i in range(100)],
            "has_duplicates": [i % 5 for i in range(100)],
            "outliers": np.concatenate([np.random.normal(100, 10, 95), [1000, 2000, 3000, 4000, 5000]]),
        }
    )

    config = ProfileConfig(generate_recommendations=True)
    profiler = DataProfiler(config=config)
    profile = profiler.profile(df)

    print(f"\nGenerated {len(profile.recommendations)} recommendations:\n")

    for rec in profile.recommendations:
        severity_icon = {"critical": "🔴", "warning": "🟡", "info": "ℹ️"}.get(rec.severity, "ℹ️")
        print(f"{severity_icon} [{rec.severity.upper()}] {rec.title}")
        print(f"   {rec.description}")
        if rec.suggestion:
            print(f"   💡 {rec.suggestion}")
        print()


def example_time_series_analysis():
    """Demonstrate time series analysis."""
    print("\n\n" + "=" * 70)
    print("Example: Time Series Analysis")
    print("=" * 70)

    # Create time series with gaps
    dates = []
    current_date = pd.Timestamp("2023-01-01")
    for i in range(100):
        dates.append(current_date)
        # Add gap every 20 records
        if i % 20 == 19:
            current_date += pd.Timedelta(days=10)
        else:
            current_date += pd.Timedelta(days=1)

    df = pd.DataFrame({"event_date": dates, "value": range(100)})

    config = ProfileConfig(time_series_analysis=True)
    profiler = DataProfiler(config=config)
    profile = profiler.profile(df)

    for col in profile.columns:
        if col.datetime_stats and col.datetime_stats.time_series:
            ts = col.datetime_stats.time_series
            print(f"\nTime Series Analysis for '{col.name}':")
            print(f"  Has gaps: {ts.has_gaps}")
            if ts.has_gaps:
                print(f"  Gap count: {ts.gap_count}")
                print(f"  Average gap: {ts.avg_gap_days:.1f} days")
                print(f"  Maximum gap: {ts.max_gap_days:.1f} days")
            print(f"  Regular frequency: {ts.is_regular_frequency}")
            if ts.inferred_frequency:
                print(f"  Inferred frequency: {ts.inferred_frequency}")


if __name__ == "__main__":
    example_advanced_statistics()
    example_pii_detection()
    example_schema_inference()
    example_recommendations()
    example_time_series_analysis()

    print("\n" + "=" * 70)
    print("All advanced examples completed!")
    print("=" * 70)
