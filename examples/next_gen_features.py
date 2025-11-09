"""Examples demonstrating next-generation profiling features."""

import time
import numpy as np
import pandas as pd

from data_profiler import (
    DataProfiler,
    ProfileComparator,
    CustomPattern,
    CustomPatternDetector,
    PatternLibrary,
    MultiTableAnalyzer,
    HTMLReportGenerator,
    LineageTracker,
    OperationType,
    MLRecommendationsEngine,
)


def example_drift_detection():
    """Demonstrate profile comparison and drift detection."""
    print("=" * 70)
    print("Example: Profile Comparison & Drift Detection")
    print("=" * 70)

    # Create baseline data
    np.random.seed(42)
    baseline_df = pd.DataFrame({
        "id": range(1000),
        "value": np.random.normal(100, 15, 1000),
        "category": np.random.choice(["A", "B", "C"], 1000),
        "status": np.random.choice(["active", "inactive"], 1000, p=[0.8, 0.2]),
    })

    # Profile baseline
    profiler = DataProfiler()
    baseline_profile = profiler.profile(baseline_df)

    print(f"\nBaseline profile generated at {baseline_profile.profile_timestamp}")
    print(f"Rows: {baseline_profile.row_count}, Columns: {baseline_profile.column_count}")

    # Simulate passage of time
    time.sleep(1)

    # Create "current" data with drift
    current_df = pd.DataFrame({
        "id": range(1000),
        "value": np.random.normal(110, 20, 1000),  # Mean shifted, variance increased
        "category": np.random.choice(["A", "B", "C", "D"], 1000),  # New category added
        "status": np.random.choice(["active", "inactive"], 1000, p=[0.6, 0.4]),  # Distribution changed
    })

    # Add some nulls (quality degradation)
    current_df.loc[current_df.index % 10 == 0, "value"] = None

    # Profile current data
    current_profile = profiler.profile(current_df)

    print(f"\nCurrent profile generated at {current_profile.profile_timestamp}")

    # Compare profiles
    drift = ProfileComparator.compare(baseline_profile, current_profile)

    print(f"\n{'DRIFT ANALYSIS':-^70}")
    print(f"Overall Drift Score: {drift.overall_drift_score:.3f}")
    print(f"Drift Severity: {drift.drift_severity.upper()}")
    print(f"Columns with Drift: {drift.columns_with_drift}/{drift.columns_analyzed}")
    print(f"Time Elapsed: {drift.time_elapsed_days:.2f} days")

    # Show detailed drift report
    print("\n" + ProfileComparator.generate_drift_report(drift))


def example_custom_patterns():
    """Demonstrate custom pattern detection."""
    print("\n\n" + "=" * 70)
    print("Example: Custom Pattern Detection")
    print("=" * 70)

    # Create data with custom business patterns
    df = pd.DataFrame({
        "order_id": [f"ORD-{i:06d}" for i in range(1, 101)],
        "customer_id": [f"CUST-{np.random.randint(10000000, 99999999)}" for _ in range(100)],
        "invoice": [f"INV-2024-{i:06d}" for i in range(1, 101)],
        "product_sku": [f"PROD-{i:05d}" for i in range(1, 101)],
        "notes": ["Regular order"] * 100,
    })

    # Use pre-built business patterns
    print("\n📚 Using Pre-built Business Pattern Library:")
    business_patterns = CustomPatternDetector.create_business_patterns()
    print(f"Loaded {len(business_patterns.patterns)} business patterns")

    for col in df.columns:
        detected = CustomPatternDetector.detect_patterns(
            df[col],
            business_patterns.patterns,
            sample_size=100
        )
        if detected:
            print(f"\n  {col}:")
            for pattern_name, count in detected.items():
                print(f"    ✓ {pattern_name}: {count} matches")

    # Create custom patterns
    print("\n\n🎯 Creating Custom Patterns:")
    custom_library = PatternLibrary(
        name="Custom Patterns",
        description="Organization-specific patterns"
    )

    # Add a custom employee ID pattern
    custom_library.add_pattern(CustomPattern(
        name="employee_id",
        regex=r"^EMP-\d{5}$",
        description="Employee ID: EMP-XXXXX",
        category="hr",
        examples=["EMP-12345", "EMP-99999"]
    ))

    # Validate pattern
    test_values = ["EMP-12345", "EMP-ABCDE", "12345", "EMP-123"]
    validation_results = CustomPatternDetector.validate_pattern(
        custom_library.patterns[0],
        test_values
    )

    print("\nPattern Validation Results:")
    for value, matches in validation_results.items():
        icon = "✓" if matches else "✗"
        print(f"  {icon} '{value}': {'Match' if matches else 'No match'}")


def example_multi_table_analysis():
    """Demonstrate multi-table relationship detection."""
    print("\n\n" + "=" * 70)
    print("Example: Multi-Table Analysis & Relationship Detection")
    print("=" * 70)

    # Create related tables
    np.random.seed(42)

    # Users table
    users = pd.DataFrame({
        "id": range(1, 11),
        "username": [f"user{i}" for i in range(1, 11)],
        "email": [f"user{i}@example.com" for i in range(1, 11)],
        "created_at": pd.date_range("2023-01-01", periods=10, freq="D"),
    })

    # Orders table (many-to-one with users)
    orders = pd.DataFrame({
        "order_id": range(1, 51),
        "user_id": np.random.choice(range(1, 11), 50),
        "total": np.random.uniform(10, 500, 50),
        "order_date": pd.date_range("2023-01-15", periods=50, freq="12H"),
    })

    # Products table
    products = pd.DataFrame({
        "product_id": range(1, 21),
        "name": [f"Product {i}" for i in range(1, 21)],
        "price": np.random.uniform(10, 200, 20),
        "category": np.random.choice(["Electronics", "Clothing", "Food"], 20),
    })

    # Order items table (many-to-many bridge)
    order_items = pd.DataFrame({
        "id": range(1, 101),
        "order_id": np.random.choice(range(1, 51), 100),
        "product_id": np.random.choice(range(1, 21), 100),
        "quantity": np.random.randint(1, 5, 100),
    })

    # Analyze relationships
    tables = {
        "users": users,
        "orders": orders,
        "products": products,
        "order_items": order_items,
    }

    print("\n🔍 Analyzing relationships between tables...")
    analyzer = MultiTableAnalyzer()
    schema = analyzer.analyze_relationships(tables, min_confidence=0.7)

    print(f"\nTables analyzed: {len(schema.tables)}")
    print(f"Relationships found: {len(schema.relationships)}")
    print(f"Foreign keys detected: {len(schema.foreign_keys)}")

    # Show primary key candidates
    print(f"\n{'PRIMARY KEYS':-^70}")
    for table, pks in schema.primary_keys.items():
        if pks:
            print(f"{table}: {', '.join(pks)}")

    # Show foreign key relationships
    print(f"\n{'FOREIGN KEY RELATIONSHIPS':-^70}")
    for fk in schema.foreign_keys:
        if fk.is_valid:
            icon = "✓"
            status = "VALID"
        else:
            icon = "?"
            status = "CANDIDATE"

        print(f"\n{icon} {status}: {fk.source_table}.{fk.source_column} → {fk.target_table}.{fk.target_column}")
        print(f"  Type: {fk.relationship_type}")
        print(f"  Match: {fk.match_percentage:.1f}%")
        print(f"  Confidence: {fk.confidence_score:.2f}")

    # Generate relationship diagram
    print("\n" + MultiTableAnalyzer.generate_relationship_diagram(schema))


def example_pattern_libraries():
    """Demonstrate pre-built pattern libraries."""
    print("\n\n" + "=" * 70)
    print("Example: Pre-built Pattern Libraries")
    print("=" * 70)

    # Medical patterns
    print("\n🏥 Medical/Healthcare Patterns:")
    medical_lib = CustomPatternDetector.create_medical_patterns()
    print(f"Loaded {len(medical_lib.patterns)} medical patterns:")
    for pattern in medical_lib.patterns:
        print(f"  • {pattern.name}: {pattern.description}")
        if pattern.examples:
            print(f"    Example: {pattern.examples[0]}")

    # Financial patterns
    print("\n💰 Financial Patterns:")
    financial_lib = CustomPatternDetector.create_financial_patterns()
    print(f"Loaded {len(financial_lib.patterns)} financial patterns:")
    for pattern in financial_lib.patterns:
        print(f"  • {pattern.name}: {pattern.description}")
        if pattern.examples:
            print(f"    Example: {pattern.examples[0]}")

    # Test with sample data
    print("\n\nTesting Financial Patterns:")
    financial_data = pd.DataFrame({
        "account": ["ACC-12345678", "ACC-987654321", "ACC-11111111"],
        "routing": ["123456789", "987654321", "111222333"],
        "transaction": [
            "TXN-A1B2C3D4E5F6G7H8",
            "TXN-1234567890ABCDEF",
            "TXN-FEDCBA0987654321"
        ],
    })

    for col in financial_data.columns:
        detected = CustomPatternDetector.detect_patterns(
            financial_data[col],
            financial_lib.patterns,
            sample_size=10
        )
        if detected:
            print(f"\n  {col}:")
            for pattern_name, count in detected.items():
                print(f"    ✓ {pattern_name}: {count} matches")


def example_html_reports():
    """Demonstrate HTML report generation with visualizations."""
    print("\n\n" + "=" * 70)
    print("Example: HTML Report Generation")
    print("=" * 70)

    # Create sample data
    np.random.seed(42)
    df = pd.DataFrame({
        "customer_id": range(1, 101),
        "age": np.random.randint(18, 75, 100),
        "balance": np.random.uniform(0, 50000, 100),
        "credit_score": np.random.randint(300, 850, 100),
        "account_type": np.random.choice(["Savings", "Checking", "Premium"], 100),
        "is_active": np.random.choice([True, False], 100, p=[0.85, 0.15]),
        "signup_date": pd.date_range("2023-01-01", periods=100, freq="3D"),
    })

    # Profile the data
    print("\n📊 Profiling data...")
    profiler = DataProfiler()
    profile = profiler.profile(df)

    # Generate HTML report
    print("\n📝 Generating HTML report...")
    html_path = "reports/profile_report.html"
    HTMLReportGenerator.generate_profile_report(
        profile,
        output_path=html_path,
        title="Customer Data Profile Report"
    )
    print(f"✓ Profile report saved to: {html_path}")

    # Create baseline and current for drift report
    print("\n📊 Creating drift comparison...")
    baseline_df = df.copy()

    # Simulate drift: shift age distribution, change account types
    current_df = df.copy()
    current_df["age"] = current_df["age"] + np.random.normal(5, 2, 100)
    current_df["account_type"] = np.random.choice(
        ["Savings", "Checking", "Premium", "Business"], 100
    )
    current_df.loc[current_df.index % 5 == 0, "balance"] = None  # Add some nulls

    # Profile both
    baseline_profile = profiler.profile(baseline_df)
    time.sleep(1)  # Simulate time passage
    current_profile = profiler.profile(current_df)

    # Compare
    drift = ProfileComparator.compare(baseline_profile, current_profile)

    # Generate drift HTML report
    print("\n📝 Generating drift report...")
    drift_path = "reports/drift_report.html"
    HTMLReportGenerator.generate_drift_report(
        drift,
        baseline_profile,
        current_profile,
        output_path=drift_path,
        title="Customer Data Drift Analysis"
    )
    print(f"✓ Drift report saved to: {drift_path}")

    print("\n✨ HTML reports generated successfully!")
    print(f"   • Profile Report: {html_path}")
    print(f"   • Drift Report: {drift_path}")


def example_data_lineage():
    """Demonstrate data lineage tracking."""
    print("\n\n" + "=" * 70)
    print("Example: Data Lineage Tracking")
    print("=" * 70)

    # Initialize tracker
    tracker = LineageTracker()

    # Register source dataset
    print("\n📂 Registering data sources...")
    raw_data_id = tracker.register_source(
        name="raw_customer_data",
        source_type="file",
        location="/data/customers.csv",
        format="csv",
        row_count=10000,
        column_count=15,
        metadata={"uploaded_by": "data_team", "version": "1.0"}
    )
    print(f"✓ Registered: raw_customer_data ({raw_data_id[:8]}...)")

    # Register transformations
    print("\n🔄 Tracking transformations...")

    # Transformation 1: Data cleaning
    cleaned_id = tracker.register_transformation(
        name="Remove duplicates and null values",
        input_ids=[raw_data_id],
        output_name="cleaned_customer_data",
        operation_type=OperationType.CLEANING,
        parameters={"remove_duplicates": True, "drop_nulls": True},
        row_count=9500,
        column_count=15,
        metrics={"rows_removed": 500, "duplicates": 300, "nulls": 200}
    )
    print(f"✓ Cleaned data ({cleaned_id[:8]}...)")

    # Transformation 2: Feature engineering
    enriched_id = tracker.register_transformation(
        name="Add derived features",
        input_ids=[cleaned_id],
        output_name="enriched_customer_data",
        operation_type=OperationType.TRANSFORM,
        parameters={"new_features": ["age_group", "customer_lifetime_value", "churn_risk"]},
        row_count=9500,
        column_count=18,
        metrics={"features_added": 3}
    )
    print(f"✓ Enriched data ({enriched_id[:8]}...)")

    # Register another source for joining
    product_data_id = tracker.register_source(
        name="product_catalog",
        source_type="database",
        location="postgresql://localhost/products",
        format="table",
        row_count=500,
        column_count=8
    )
    print(f"✓ Registered: product_catalog ({product_data_id[:8]}...)")

    # Transformation 3: Join datasets
    final_id = tracker.register_transformation(
        name="Join customer and product data",
        input_ids=[enriched_id, product_data_id],
        output_name="customer_product_analysis",
        operation_type=OperationType.TRANSFORM,
        parameters={"join_type": "left", "join_on": "product_id"},
        row_count=12000,
        column_count=24,
        metrics={"join_matches": 12000, "unmatched": 0}
    )
    print(f"✓ Joined data ({final_id[:8]}...)")

    # Register profiling
    print("\n📊 Registering profiling operation...")
    tracker.register_profile(
        dataset_id=final_id,
        profile_results={
            "quality_score": 95.5,
            "completeness": 98.2,
            "issues_found": 3
        }
    )
    print("✓ Profiling tracked")

    # Show lineage summary
    print(f"\n{'LINEAGE SUMMARY':-^70}")
    summary = tracker.get_lineage_summary(final_id)
    print(f"Dataset: {summary['dataset']['name']}")
    print(f"  Rows: {summary['dataset']['row_count']:,}")
    print(f"  Columns: {summary['dataset']['column_count']}")
    print(f"  Upstream datasets: {summary['upstream_count']}")
    print(f"  Operations: {summary['operations_count']}")

    # Get upstream lineage
    print(f"\n{'UPSTREAM LINEAGE':-^70}")
    upstream = tracker.get_upstream_datasets(final_id)
    for dataset in upstream:
        if dataset.dataset_id != final_id:
            source_info = f" [from {dataset.source.source_type}]" if dataset.source else ""
            print(f"  ← {dataset.name}{source_info}")

    # Generate full lineage diagram
    print("\n" + tracker.generate_lineage_diagram(final_id))

    # Export lineage
    lineage_export = tracker.export_lineage()
    print(f"\n✓ Lineage graph exported ({len(lineage_export['datasets'])} datasets, {len(lineage_export['operations'])} operations)")


def example_ml_recommendations():
    """Demonstrate ML-based recommendations engine."""
    print("\n\n" + "=" * 70)
    print("Example: ML-Based Recommendations")
    print("=" * 70)

    # Create data with statistical patterns
    np.random.seed(42)
    df = pd.DataFrame({
        # Highly skewed distribution
        "revenue": np.random.exponential(scale=1000, size=500),
        # Highly correlated columns
        "price": np.random.uniform(10, 100, 500),
        "price_with_tax": lambda x: x["price"] * 1.08,
        # Low variance numeric (should be categorical)
        "status_code": np.random.choice([1, 2, 3], 500, p=[0.7, 0.2, 0.1]),
        # Low entropy categorical
        "category": np.random.choice(["A", "B", "C", "D"], 500, p=[0.85, 0.10, 0.03, 0.02]),
        # Sequential pattern in categorical
        "id_str": [str(i) for i in range(500)],
        # Heavy-tailed distribution
        "outliers": np.concatenate([
            np.random.normal(100, 10, 480),
            np.random.uniform(500, 1000, 20)  # Extreme outliers
        ]),
    })

    df["price_with_tax"] = df["price"] * 1.08

    # Profile the data
    print("\n📊 Profiling data...")
    profiler = DataProfiler()
    profile = profiler.profile(df)

    # Generate ML-based recommendations
    print("\n🤖 Generating ML-based recommendations...")
    ml_recommendations = MLRecommendationsEngine.generate_recommendations(
        profile,
        confidence_threshold=0.7
    )

    print(f"\n✨ Generated {len(ml_recommendations)} ML-based recommendations:\n")

    # Display recommendations grouped by severity
    for severity in ["critical", "warning", "info"]:
        severity_recs = [r for r in ml_recommendations if r.severity == severity]
        if severity_recs:
            icon = {"critical": "🔴", "warning": "🟡", "info": "ℹ️"}[severity]
            print(f"{icon} {severity.upper()} ({len(severity_recs)} recommendations):")
            for rec in severity_recs:
                print(f"\n  • {rec.title}")
                if rec.column:
                    print(f"    Column: {rec.column}")
                print(f"    {rec.description}")
                if rec.suggestion:
                    # Extract confidence from suggestion
                    print(f"    💡 {rec.suggestion}")
            print()


if __name__ == "__main__":
    example_drift_detection()
    example_custom_patterns()
    example_multi_table_analysis()
    example_pattern_libraries()
    example_html_reports()
    example_data_lineage()
    example_ml_recommendations()

    print("\n\n" + "=" * 70)
    print("All next-generation examples completed!")
    print("=" * 70)
