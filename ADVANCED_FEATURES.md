# Advanced Profiling Features

This document provides a comprehensive guide to the advanced profiling capabilities introduced in v0.2.0.

## Table of Contents

- [Advanced Statistical Analysis](#advanced-statistical-analysis)
- [Enhanced Pattern Detection & PII](#enhanced-pattern-detection--pii)
- [Time Series Analysis](#time-series-analysis)
- [Schema Inference & DDL Generation](#schema-inference--ddl-generation)
- [Recommendations Engine](#recommendations-engine)
- [Configuration Reference](#configuration-reference)
- [Examples](#examples)

---

## Advanced Statistical Analysis

### Overview

Comprehensive statistical testing and distribution analysis for numeric columns.

### Features

#### Normality Tests
- **Shapiro-Wilk Test**: Best for sample sizes < 5000
- **Anderson-Darling Test**: Tests for various distributions
- **Kolmogorov-Smirnov Test**: General goodness-of-fit test

#### Distribution Fitting
Automatically fits multiple distributions and ranks by goodness-of-fit:
- Normal (Gaussian)
- Log-normal
- Exponential
- Gamma
- Beta

Uses AIC (Akaike Information Criterion) for ranking.

#### Bimodality Detection
Detects bimodal distributions using the coefficient of bimodality:
```
b = (skew² + 1) / kurtosis
```
Threshold: b > 0.555 indicates bimodality

#### Variance Stability
Analyzes if variance remains stable across the dataset using rolling windows.

### Usage

```python
from data_profiler import DataProfiler, ProfileConfig

config = ProfileConfig(advanced_stats=True)
profiler = DataProfiler(config=config)
profile = profiler.profile(df)

for col in profile.columns:
    if col.numeric_stats:
        # Check normality
        if col.numeric_stats.normality_tests:
            tests = col.numeric_stats.normality_tests.tests
            if "shapiro_wilk" in tests:
                print(f"Normal: {tests['shapiro_wilk']['is_normal']}")

        # Check bimodality
        if col.numeric_stats.is_bimodal:
            print(f"Bimodal distribution detected!")

        # Best-fit distributions
        if col.numeric_stats.distribution_fits:
            best_fit = col.numeric_stats.distribution_fits[0]
            print(f"Best fit: {best_fit.distribution}")
```

### Performance Notes

- Statistical tests only run when `advanced_stats=True`
- Large datasets (>5000 values) are sampled for distribution fitting
- Minimum sample sizes enforced for reliable results

---

## Enhanced Pattern Detection & PII

### Overview

Advanced pattern recognition with special focus on detecting personally identifiable information (PII) and sensitive data.

### Supported Patterns

#### Contact Information
- **Email**: RFC-compliant email addresses
- **Phone Numbers**: US and international formats
- **Postal Codes**: US ZIP codes, UK postcodes

#### Network
- **IPv4**: Standard IPv4 addresses
- **IPv6**: Full IPv6 addresses
- **MAC Address**: Hardware addresses
- **Domain Names**: Valid domain names
- **URLs**: HTTP/HTTPS URLs

#### Identifiers
- **UUID**: RFC 4122 UUIDs
- **MD5**: MD5 hashes
- **SHA-1**: SHA-1 hashes
- **SHA-256**: SHA-256 hashes

#### Financial
- **Credit Cards**: Visa, MasterCard, AmEx, Discover (with Luhn validation)
- **SSN**: US Social Security Numbers (with format validation)
- **IBAN**: International Bank Account Numbers
- **SWIFT/BIC**: Bank identifiers

#### Other
- **Hex Colors**: CSS hex color codes
- **Semantic Versioning**: SemVer strings

### PII Risk Levels

- **High**: SSN, credit cards
- **Medium**: Email, phone numbers
- **Low**: Other potentially identifiable patterns
- **None**: No PII detected

### Usage

```python
config = ProfileConfig(detect_pii=True)
profiler = DataProfiler(config=config)
profile = profiler.profile(df)

for col in profile.columns:
    if col.text_stats and col.text_stats.pii_risk_level:
        risk = col.text_stats.pii_risk_level
        print(f"{col.name}: {risk} PII risk")

        if col.text_stats.patterns:
            print(f"  Patterns: {col.text_stats.patterns}")
```

### Security Considerations

- Enable `detect_pii=True` to scan for sensitive data
- Review high and medium risk columns for compliance
- Consider encryption, access controls, and data masking
- Ensure GDPR/CCPA compliance for PII-containing datasets

---

## Time Series Analysis

### Overview

Specialized analysis for datetime columns to detect gaps, infer frequency, and identify temporal patterns.

### Features

#### Gap Detection
- Identifies irregularities in time series data
- Calculates gap statistics (count, average, maximum)
- Uses adaptive thresholds based on median difference

#### Frequency Inference
- Automatically detects regular intervals
- Supports: seconds, minutes, hours, days, weeks, months, years
- Validates frequency regularity using coefficient of variation

#### Temporal Patterns
- Most common year, month, day of week
- Date range analysis
- Consistency checks

### Usage

```python
config = ProfileConfig(time_series_analysis=True)
profiler = DataProfiler(config=config)
profile = profiler.profile(df)

for col in profile.columns:
    if col.datetime_stats and col.datetime_stats.time_series:
        ts = col.datetime_stats.time_series

        if ts.has_gaps:
            print(f"Gaps detected: {ts.gap_count}")
            print(f"Max gap: {ts.max_gap_days} days")

        if ts.is_regular_frequency:
            print(f"Frequency: {ts.inferred_frequency}")
```

### Use Cases

- Data quality validation
- Missing data detection
- Frequency analysis
- Irregular time series identification

---

## Schema Inference & DDL Generation

### Overview

Intelligently infer database schemas and generate SQL DDL statements from profiled data.

### Features

#### Smart Type Mapping
Maps Python/Pandas types to optimal SQL types:
- **Integers**: SMALLINT, INTEGER, BIGINT (based on range)
- **Decimals**: DECIMAL, NUMERIC
- **Text**: VARCHAR(n), TEXT (based on length)
- **Dates**: TIMESTAMP
- **Booleans**: BOOLEAN

#### Primary Key Detection
Identifies columns suitable for primary keys:
- 100% unique
- 100% complete (no nulls)
- Automatically suggested

#### Index Recommendations
Suggests indexes for:
- High cardinality columns (>50% unique)
- High completeness columns (>90%)
- Frequently filtered columns

#### DDL Generation
Generates complete CREATE TABLE statements with:
- Column definitions
- NULL/NOT NULL constraints
- UNIQUE constraints
- Primary key
- Recommended indexes

### Usage

```python
from data_profiler import SchemaInferenceEngine

config = ProfileConfig(infer_schema=True)
profiler = DataProfiler(config=config)
profile = profiler.profile(df)

if profile.inferred_schema:
    print(f"Primary keys: {profile.inferred_schema.primary_key_candidates}")
    print(f"Indexes: {profile.inferred_schema.indexes_recommended}")

    # Generate DDL
    ddl = SchemaInferenceEngine.generate_ddl(profile.inferred_schema, "my_table")
    print(ddl)
```

### Example Output

```sql
CREATE TABLE my_table (
    user_id INTEGER NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    age SMALLINT NULL,
    balance DECIMAL NULL,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id)
);

-- Recommended indexes
CREATE INDEX idx_my_table_email ON my_table(email);
CREATE INDEX idx_my_table_username ON my_table(username);
```

---

## Recommendations Engine

### Overview

Automated data quality and optimization recommendations based on profiling results.

### Recommendation Categories

#### Data Quality
- High null percentages
- Duplicate rows
- Outliers
- Low uniqueness in text columns

#### Performance
- Large datasets
- Categorical encoding opportunities
- Large text columns
- High cardinality categoricals

#### Security
- PII detection alerts
- Sensitive data warnings

#### Schema
- Data type optimizations
- Indexing suggestions
- Non-normal distributions

### Severity Levels

- **Critical**: Immediate attention required (e.g., high PII risk, >80% nulls)
- **Warning**: Should be addressed (e.g., >50% nulls, performance issues)
- **Info**: Informational suggestions (e.g., optimization opportunities)

### Usage

```python
config = ProfileConfig(generate_recommendations=True)  # Default: True
profiler = DataProfiler(config=config)
profile = profiler.profile(df)

for rec in profile.recommendations:
    print(f"[{rec.severity}] {rec.title}")
    print(f"  {rec.description}")
    if rec.suggestion:
        print(f"  Suggestion: {rec.suggestion}")
```

### Example Recommendations

```
🔴 [CRITICAL] PII detected in column 'ssn'
   Column contains potentially sensitive personal information
   Suggestion: Ensure encryption and compliance with data privacy regulations

🟡 [WARNING] High null percentage in column 'phone'
   65.3% of values are null
   Suggestion: Consider imputing missing values or investigating data collection

ℹ️ [INFO] Categorical encoding opportunity: 'status'
   Column has only 4 unique values (0.8% of dataset)
   Suggestion: Consider using categorical encoding to save memory
```

---

## Configuration Reference

### ProfileConfig Parameters

```python
class ProfileConfig:
    # Performance settings
    sample_size: Optional[int] = None              # Sample for large datasets
    parallel: bool = True                           # Parallel column processing
    max_workers: Optional[int] = None              # Thread pool size

    # Statistical settings
    compute_correlations: bool = True              # Correlation matrix
    compute_percentiles: bool = True               # Percentile statistics
    histogram_bins: int = 50                       # Histogram resolution

    # Data quality
    detect_outliers: bool = True                   # IQR outlier detection
    outlier_threshold: float = 1.5                 # IQR multiplier

    # Text analysis
    max_string_length_sample: int = 1000           # Pattern detection sample size
    detect_patterns: bool = True                   # Basic pattern detection

    # Advanced features (NEW in v0.2.0)
    advanced_stats: bool = False                   # Normality tests, distribution fitting
    detect_pii: bool = False                       # PII and sensitive data detection
    time_series_analysis: bool = False             # Time series gap/frequency analysis
    generate_recommendations: bool = True          # Recommendations engine
    infer_schema: bool = False                     # Schema inference and DDL

    # Memory optimization
    chunk_size: int = 100_000                      # Chunk size for large datasets
```

### Performance Impact

| Feature | Performance Impact | When to Enable |
|---------|-------------------|----------------|
| `advanced_stats` | Low (uses sampling) | Numeric data analysis |
| `detect_pii` | Low-Medium | Security audits |
| `time_series_analysis` | Low | Datetime columns |
| `generate_recommendations` | Minimal | Always (default: True) |
| `infer_schema` | Minimal | Database design |

---

## Examples

See `examples/advanced_features.py` for comprehensive examples demonstrating:

1. **Advanced Statistical Analysis**
   - Normality testing
   - Bimodality detection
   - Distribution fitting

2. **PII Detection**
   - Risk assessment
   - Pattern identification
   - Security recommendations

3. **Schema Inference**
   - Primary key detection
   - Index recommendations
   - DDL generation

4. **Recommendations**
   - Data quality issues
   - Optimization opportunities
   - Security alerts

5. **Time Series Analysis**
   - Gap detection
   - Frequency inference
   - Temporal patterns

Run the examples:
```bash
python examples/advanced_features.py
```

---

## Best Practices

### 1. Enable Features Selectively

Only enable advanced features when needed to maintain optimal performance:

```python
# For general profiling
config = ProfileConfig()

# For security audit
config = ProfileConfig(detect_pii=True)

# For database design
config = ProfileConfig(infer_schema=True)

# For deep statistical analysis
config = ProfileConfig(advanced_stats=True)
```

### 2. Use Sampling for Large Datasets

Combine sampling with advanced features for large datasets:

```python
config = ProfileConfig(
    sample_size=100_000,
    advanced_stats=True,
    detect_pii=True
)
```

### 3. Review Recommendations

Always review critical and warning recommendations:

```python
critical_recs = [r for r in profile.recommendations if r.severity == "critical"]
for rec in critical_recs:
    # Handle critical issues
    handle_critical_recommendation(rec)
```

### 4. Secure PII Data

When PII is detected:
- Encrypt at rest and in transit
- Implement access controls
- Consider anonymization/pseudonymization
- Ensure regulatory compliance (GDPR, CCPA, etc.)

### 5. Act on Schema Recommendations

Use inferred schemas as a starting point:
- Review primary key suggestions
- Validate index recommendations
- Adjust types for specific database systems
- Add business constraints

---

## Backward Compatibility

All advanced features are **fully backward compatible**:

- Default configuration unchanged
- All new features opt-in via config
- Existing code works without modification
- No breaking changes to APIs

Upgrade safely from v0.1.0 to v0.2.0 with zero code changes!

---

## Performance Characteristics

### Advanced Statistics
- **Time Complexity**: O(n log n) for sorting in tests
- **Space Complexity**: O(n) for sampled data
- **Sampling**: Automatic for distributions >5000 values

### PII Detection
- **Time Complexity**: O(n) with sampling
- **Space Complexity**: O(1) for patterns
- **Sampling**: Default 1000 values with extrapolation

### Time Series
- **Time Complexity**: O(n log n) for sorting
- **Space Complexity**: O(n) for sorted series
- **No Sampling**: Needs full series for accurate gap detection

### Schema Inference
- **Time Complexity**: O(m) where m = number of columns
- **Space Complexity**: O(m)
- **No Additional Data Access**: Uses profile results

### Recommendations
- **Time Complexity**: O(m) where m = number of columns
- **Space Complexity**: O(m)
- **No Additional Data Access**: Uses profile results

---

## Future Enhancements

Planned for future releases:

- **Profile Comparison**: Drift detection between profiling runs
- **HTML Report Generation**: Interactive reports with visualizations
- **Custom Pattern Detection**: User-defined regex patterns
- **Advanced Recommendations**: ML-based suggestions
- **Multi-table Analysis**: Foreign key detection, relationship mapping
- **Data Lineage**: Track data flow and transformations

---

For questions, issues, or feature requests, please open an issue on GitHub.
