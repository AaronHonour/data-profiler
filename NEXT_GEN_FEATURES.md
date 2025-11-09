# Next-Generation Features

This document describes the advanced features added to the Data Profiler in version 0.3.0.

## Table of Contents

- [Profile Comparison & Drift Detection](#profile-comparison--drift-detection)
- [Custom Pattern Detection](#custom-pattern-detection)
- [Multi-Table Analysis](#multi-table-analysis)
- [HTML Report Generation](#html-report-generation)
- [Data Lineage Tracking](#data-lineage-tracking)
- [ML-Based Recommendations](#ml-based-recommendations)

---

## Profile Comparison & Drift Detection

Detect data drift by comparing profiles over time to identify changes in distributions, quality, and schema.

### Features

- **Statistical Drift Detection**: Compare distributions, means, medians, and other statistics
- **Quality Drift**: Track changes in completeness, uniqueness, and null percentages
- **Schema Changes**: Detect added/removed columns and type changes
- **Severity Classification**: Automatically classify drift as critical, high, medium, low, or none
- **Detailed Reports**: Generate human-readable drift analysis reports

### Usage

```python
from data_profiler import DataProfiler, ProfileComparator
import pandas as pd
import time

# Profile baseline data
profiler = DataProfiler()
baseline_df = pd.DataFrame({
    'value': np.random.normal(100, 15, 1000),
    'category': np.random.choice(['A', 'B', 'C'], 1000)
})
baseline_profile = profiler.profile(baseline_df)

# Simulate time passage
time.sleep(1)

# Profile current data (with drift)
current_df = pd.DataFrame({
    'value': np.random.normal(110, 20, 1000),  # Mean shifted, variance increased
    'category': np.random.choice(['A', 'B', 'C', 'D'], 1000)  # New category
})
current_profile = profiler.profile(current_df)

# Compare profiles
drift = ProfileComparator.compare(baseline_profile, current_profile)

print(f"Overall Drift Score: {drift.overall_drift_score:.3f}")
print(f"Drift Severity: {drift.drift_severity}")
print(f"Columns with Drift: {drift.columns_with_drift}/{drift.columns_analyzed}")

# Generate detailed report
report = ProfileComparator.generate_drift_report(drift)
print(report)
```

### Drift Metrics

- **Overall Drift Score** (0-1): Aggregate measure of dataset change
- **Column Drift Scores**: Individual scores for each column
- **Type Changes**: Detected schema modifications
- **Distribution Changes**: Statistical significance of distribution shifts

### Severity Levels

- **Critical** (≥0.8): Major changes requiring immediate attention
- **High** (0.6-0.8): Significant drift, review recommended
- **Medium** (0.4-0.6): Moderate drift, monitor closely
- **Low** (0.2-0.4): Minor drift, normal variation
- **None** (<0.2): Negligible drift

---

## Custom Pattern Detection

Define and detect custom data patterns using user-defined regex patterns.

### Features

- **Custom Patterns**: Define regex patterns for domain-specific data
- **Pattern Libraries**: Pre-built pattern collections for common domains
- **Pattern Validation**: Test patterns against sample data
- **Business Patterns**: Order numbers, customer IDs, SKUs, VINs, ISBNs
- **Medical Patterns**: NPI, ICD-10, MRN, NDC codes
- **Financial Patterns**: Account numbers, routing numbers, CUSIP, transaction IDs

### Usage

#### Using Pre-built Pattern Libraries

```python
from data_profiler import CustomPatternDetector
import pandas as pd

# Load business patterns
business_patterns = CustomPatternDetector.create_business_patterns()
print(f"Loaded {len(business_patterns.patterns)} patterns")

# Detect patterns in data
df = pd.DataFrame({
    'order_id': [f"ORD-{i:06d}" for i in range(1, 101)],
    'invoice': [f"INV-2024-{i:06d}" for i in range(1, 101)]
})

for col in df.columns:
    detected = CustomPatternDetector.detect_patterns(
        df[col],
        business_patterns.patterns
    )
    print(f"\n{col}:")
    for pattern_name, count in detected.items():
        print(f"  ✓ {pattern_name}: {count} matches")
```

#### Creating Custom Patterns

```python
from data_profiler import CustomPattern, PatternLibrary, CustomPatternDetector

# Create custom pattern library
library = PatternLibrary(
    name="Company Patterns",
    description="Organization-specific patterns"
)

# Add employee ID pattern
library.add_pattern(CustomPattern(
    name="employee_id",
    regex=r"^EMP-\d{5}$",
    description="Employee ID: EMP-XXXXX",
    category="hr",
    examples=["EMP-12345", "EMP-99999"]
))

# Validate pattern
test_values = ["EMP-12345", "EMP-ABCDE", "12345"]
results = CustomPatternDetector.validate_pattern(
    library.patterns[0],
    test_values
)

for value, matches in results.items():
    print(f"{value}: {'✓' if matches else '✗'}")
```

### Available Pattern Libraries

#### Business Patterns (10 patterns)
- Order numbers
- Customer IDs
- Product SKUs
- Invoice numbers
- Tracking numbers
- VINs
- ISBNs
- License plates
- Passport numbers
- Batch numbers

#### Medical Patterns (4 patterns)
- NPI (National Provider Identifier)
- ICD-10 codes
- MRN (Medical Record Number)
- NDC (National Drug Code)

#### Financial Patterns (4 patterns)
- Account numbers
- Routing numbers
- CUSIP
- Transaction IDs

---

## Multi-Table Analysis

Automatically detect relationships, foreign keys, and primary keys across multiple tables.

### Features

- **Foreign Key Detection**: Identify FK relationships with confidence scoring
- **Relationship Types**: Classify as one-to-one, one-to-many, many-to-many
- **Primary Key Detection**: Find unique & complete column candidates
- **Naming Convention Detection**: Recognize patterns like `user_id → id`
- **Relationship Diagrams**: Generate ASCII visualizations

### Usage

```python
from data_profiler import MultiTableAnalyzer
import pandas as pd
import numpy as np

# Create related tables
np.random.seed(42)

users = pd.DataFrame({
    'id': range(1, 11),
    'username': [f'user{i}' for i in range(1, 11)],
    'email': [f'user{i}@example.com' for i in range(1, 11)]
})

orders = pd.DataFrame({
    'order_id': range(1, 51),
    'user_id': np.random.choice(range(1, 11), 50),
    'total': np.random.uniform(10, 500, 50)
})

products = pd.DataFrame({
    'product_id': range(1, 21),
    'name': [f'Product {i}' for i in range(1, 21)],
    'price': np.random.uniform(10, 200, 20)
})

# Analyze relationships
tables = {
    'users': users,
    'orders': orders,
    'products': products
}

analyzer = MultiTableAnalyzer()
schema = analyzer.analyze_relationships(tables, min_confidence=0.7)

print(f"Tables: {len(schema.tables)}")
print(f"Relationships: {len(schema.relationships)}")
print(f"Foreign Keys: {len(schema.foreign_keys)}")

# Display primary keys
print("\nPrimary Keys:")
for table, pks in schema.primary_keys.items():
    if pks:
        print(f"  {table}: {', '.join(pks)}")

# Display foreign keys
print("\nForeign Keys:")
for fk in schema.foreign_keys:
    print(f"  {fk.source_table}.{fk.source_column} → {fk.target_table}.{fk.target_column}")
    print(f"    Type: {fk.relationship_type}, Confidence: {fk.confidence_score:.2f}")

# Generate diagram
diagram = MultiTableAnalyzer.generate_relationship_diagram(schema)
print(diagram)
```

### Foreign Key Detection

The analyzer uses multiple signals to detect foreign keys:

1. **Column Name Matching**: Common columns across tables
2. **Naming Conventions**:
   - `table_name_id` → `id`
   - `table_name_col` → `col`
   - `FK_table_col` → `col`
3. **Value Overlap**: Percentage of source values found in target
4. **Relationship Type**: Analysis of duplicate patterns

### Confidence Scoring

Confidence scores (0-1) combine:
- **Match Percentage** (60% weight): Overlap of values
- **Relationship Type** (10-20% weight): Appropriate FK pattern
- **Naming Conventions** (10-20% weight): Standard naming patterns

---

## HTML Report Generation

Generate interactive HTML reports with visualizations using Plotly.

### Features

- **Interactive Visualizations**: Plotly charts for distributions, correlations
- **Profile Reports**: Comprehensive dataset overview
- **Drift Reports**: Visual drift analysis and comparison
- **Quality Dashboards**: Heatmaps and metrics
- **Responsive Design**: Modern, mobile-friendly UI

### Usage

#### Generate Profile Report

```python
from data_profiler import DataProfiler, HTMLReportGenerator
import pandas as pd
import numpy as np

# Create and profile data
df = pd.DataFrame({
    'customer_id': range(1, 101),
    'age': np.random.randint(18, 75, 100),
    'balance': np.random.uniform(0, 50000, 100),
    'credit_score': np.random.randint(300, 850, 100)
})

profiler = DataProfiler()
profile = profiler.profile(df)

# Generate HTML report
html = HTMLReportGenerator.generate_profile_report(
    profile,
    output_path='reports/profile.html',
    title='Customer Data Profile'
)

print(f"Report saved to: reports/profile.html")
print(f"Size: {len(html):,} bytes")
```

#### Generate Drift Report

```python
from data_profiler import ProfileComparator, HTMLReportGenerator

# Profile baseline and current data
baseline_profile = profiler.profile(baseline_df)
current_profile = profiler.profile(current_df)

# Compare
drift = ProfileComparator.compare(baseline_profile, current_profile)

# Generate drift HTML report
HTMLReportGenerator.generate_drift_report(
    drift,
    baseline_profile,
    current_profile,
    output_path='reports/drift.html',
    title='Data Drift Analysis'
)
```

### Report Sections

**Profile Reports:**
- Overview metrics (rows, columns, memory, time)
- Data quality heatmap
- Column-specific visualizations
- Correlation matrix
- Recommendations

**Drift Reports:**
- Overall drift gauge
- Drift summary statistics
- Column-level drift scores
- Visual comparisons

---

## Data Lineage Tracking

Track data transformations, dependencies, and flow across operations.

### Features

- **Source Tracking**: Register data sources (files, databases, APIs)
- **Operation Recording**: Track transformations, profiling, validation
- **Dependency Graphs**: Build lineage graphs with upstream/downstream tracking
- **Metadata Storage**: Capture operation parameters and metrics
- **Lineage Diagrams**: Visualize data flow

### Usage

```python
from data_profiler import LineageTracker, OperationType

# Initialize tracker
tracker = LineageTracker()

# Register source
raw_id = tracker.register_source(
    name='raw_customer_data',
    source_type='file',
    location='/data/customers.csv',
    format='csv',
    row_count=10000,
    column_count=15,
    metadata={'version': '1.0'}
)

# Track transformation
cleaned_id = tracker.register_transformation(
    name='Remove duplicates and nulls',
    input_ids=[raw_id],
    output_name='cleaned_customer_data',
    operation_type=OperationType.CLEANING,
    row_count=9500,
    column_count=15,
    metrics={'rows_removed': 500}
)

# Track another transformation
enriched_id = tracker.register_transformation(
    name='Add derived features',
    input_ids=[cleaned_id],
    output_name='enriched_customer_data',
    operation_type=OperationType.TRANSFORM,
    row_count=9500,
    column_count=18,
    parameters={'features': ['age_group', 'ltv', 'churn_risk']}
)

# Get lineage summary
summary = tracker.get_lineage_summary(enriched_id)
print(f"Dataset: {summary['dataset']['name']}")
print(f"Upstream datasets: {summary['upstream_count']}")
print(f"Operations: {summary['operations_count']}")

# Get upstream datasets
upstream = tracker.get_upstream_datasets(enriched_id)
for dataset in upstream:
    print(f"  ← {dataset.name}")

# Generate lineage diagram
diagram = tracker.generate_lineage_diagram(enriched_id)
print(diagram)

# Export lineage
lineage_data = tracker.export_lineage()
# Save to file or database
```

### Operation Types

- **SOURCE**: Data source (file, database, API)
- **TRANSFORM**: Transformation (filter, aggregate, join)
- **PROFILE**: Profiling operation
- **EXPORT**: Export to file/database
- **VALIDATION**: Data validation
- **CLEANING**: Data cleaning

### Lineage Graph Structure

```
DatasetNode:
- dataset_id, name
- row_count, column_count
- source, created_at
- tags, metadata

DataOperation:
- operation_id, operation_type
- name, timestamp
- input_ids, output_id
- parameters, metrics

LineageGraph:
- datasets: Dict[str, DatasetNode]
- operations: List[DataOperation]
```

---

## ML-Based Recommendations

Advanced recommendations using statistical learning and pattern recognition.

### Features

- **Statistical Anomaly Detection**: Identify unusual patterns
- **Distribution Analysis**: Detect skewness, kurtosis, heavy tails
- **Correlation Analysis**: Find redundant and inverse relationships
- **Type Consistency**: Detect misclassified data types
- **Entropy Analysis**: Identify concentrated or uniform distributions
- **Confidence Scores**: Each recommendation includes confidence level

### Usage

```python
from data_profiler import DataProfiler, MLRecommendationsEngine
import pandas as pd
import numpy as np

# Create data with statistical patterns
df = pd.DataFrame({
    # Highly skewed
    'revenue': np.random.exponential(1000, 500),
    # Highly correlated
    'price': np.random.uniform(10, 100, 500),
    'price_with_tax': lambda x: x['price'] * 1.08,
    # Low variance (should be categorical)
    'status': np.random.choice([1, 2, 3], 500, p=[0.7, 0.2, 0.1]),
    # Low entropy
    'category': np.random.choice(['A', 'B'], 500, p=[0.95, 0.05])
})

df['price_with_tax'] = df['price'] * 1.08

# Profile and generate ML recommendations
profiler = DataProfiler()
profile = profiler.profile(df)

recommendations = MLRecommendationsEngine.generate_recommendations(
    profile,
    confidence_threshold=0.7  # Only show high-confidence recommendations
)

print(f"Generated {len(recommendations)} recommendations\n")

for rec in recommendations:
    print(f"[{rec.severity.upper()}] {rec.title}")
    if rec.column:
        print(f"  Column: {rec.column}")
    print(f"  {rec.description}")
    print(f"  💡 {rec.suggestion}")
    print()
```

### Recommendation Types

**Distribution-Based:**
- High skewness detection (suggests transformations)
- Heavy-tailed distributions (outlier warnings)
- Non-normal distributions (transformation suggestions)

**Correlation-Based:**
- High positive correlation (redundancy detection)
- Strong inverse correlation (relationship validation)

**Type Consistency:**
- Low-variance numeric → categorical
- Sequential categorical → numeric
- High-cardinality categorical → identifier

**Pattern-Based:**
- Benford's Law violations (data quality issues)
- Low entropy (concentrated distributions)
- Uniform distributions (unusual patterns)
- Round null percentages (artificial nulls)

### Confidence Scoring

All ML recommendations include confidence scores (0-1) based on:
- Statistical significance of detected patterns
- Magnitude of deviation from expected
- Consistency across multiple indicators

---

## Example Applications

### Complete Workflow

```python
from data_profiler import (
    DataProfiler,
    ProfileComparator,
    CustomPatternDetector,
    MultiTableAnalyzer,
    HTMLReportGenerator,
    LineageTracker,
    MLRecommendationsEngine,
    OperationType
)
import pandas as pd
import numpy as np

# 1. Track lineage
tracker = LineageTracker()
source_id = tracker.register_source(
    'raw_data', 'file', 'data.csv', row_count=1000
)

# 2. Profile initial data
profiler = DataProfiler()
baseline_profile = profiler.profile(raw_df)

# 3. Detect custom patterns
business_patterns = CustomPatternDetector.create_business_patterns()
patterns = CustomPatternDetector.detect_patterns(
    raw_df['order_id'],
    business_patterns.patterns
)

# 4. Get ML recommendations
ml_recs = MLRecommendationsEngine.generate_recommendations(baseline_profile)

# 5. Generate HTML report
HTMLReportGenerator.generate_profile_report(
    baseline_profile,
    'reports/initial_profile.html'
)

# 6. After transformations, track drift
current_profile = profiler.profile(transformed_df)
drift = ProfileComparator.compare(baseline_profile, current_profile)

# 7. Generate drift report
HTMLReportGenerator.generate_drift_report(
    drift,
    baseline_profile,
    current_profile,
    'reports/drift_analysis.html'
)

# 8. Multi-table analysis
if multiple_tables:
    analyzer = MultiTableAnalyzer()
    schema = analyzer.analyze_relationships(tables)
```

---

## Performance Considerations

All next-generation features are designed for performance:

- **Drift Detection**: O(n) complexity, scales linearly
- **Custom Patterns**: Compiled regex, vectorized operations
- **Multi-Table Analysis**: Optimized set operations, sampling for large tables
- **HTML Generation**: Lazy rendering, CDN-hosted libraries
- **Lineage Tracking**: In-memory graph, O(1) lookups
- **ML Recommendations**: Statistical methods, no model training overhead

---

## API Integration

All features are available via REST API:

```bash
# Profile with recommendations
POST /api/v1/profile/upload
{
  "file": <upload>,
  "config": {
    "generate_recommendations": true,
    "detect_pii": true
  }
}

# Custom pattern detection (future)
POST /api/v1/patterns/detect
{
  "data": {...},
  "patterns": [...]
}
```

---

## See Also

- [README.md](README.md) - Main documentation
- [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) - v0.2.0 features
- [examples/next_gen_features.py](examples/next_gen_features.py) - Complete examples
