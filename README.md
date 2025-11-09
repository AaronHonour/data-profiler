# Data Profiler 🚀

A **high-performance data profiling service** designed for exceptional speed and accuracy. Built with modern Python, leveraging vectorized operations, parallel processing, and optimized algorithms to analyze datasets at scale.

## Features

### Core Capabilities

- **Lightning-Fast Profiling** - Optimized algorithms using NumPy vectorization and parallel processing
- **Comprehensive Statistics** - Complete statistical analysis for all data types
- **Type Intelligence** - Automatic type detection (numeric, categorical, text, datetime, boolean)
- **Data Quality Metrics** - Completeness, uniqueness, validity, and duplicate detection
- **Pattern Recognition** - Automatic detection of emails, URLs, phone numbers, and more
- **REST API** - Production-ready FastAPI service with async support
- **Multiple Formats** - Support for CSV, Parquet, and JSON files
- **Scalable Design** - Handles datasets from small to very large with sampling

### Next-Generation Features (v0.3.0) ✨

- **Profile Comparison & Drift Detection** - Track data changes over time with statistical significance testing
- **Custom Pattern Detection** - Define and detect domain-specific patterns with pre-built libraries
- **Multi-Table Analysis** - Automatic foreign key detection and relationship mapping
- **HTML Report Generation** - Interactive visualizations with Plotly charts
- **Data Lineage Tracking** - Track data transformations and dependencies
- **ML-Based Recommendations** - Statistical learning for intelligent insights

📚 **See [NEXT_GEN_FEATURES.md](NEXT_GEN_FEATURES.md) for detailed documentation**

### Statistical Analysis

#### Numeric Columns
- Descriptive statistics (mean, median, std, variance)
- Distribution analysis (skewness, kurtosis)
- Percentiles (25th, 50th, 75th, 95th, 99th)
- Outlier detection (IQR method)
- Histograms
- Correlation matrices

#### Categorical Columns
- Cardinality estimation
- Mode and frequency analysis
- Top N value distributions
- Shannon entropy
- Uniqueness detection

#### Text Columns
- Length statistics
- Pattern detection (email, URL, phone, IP, UUID)
- Empty and whitespace detection

#### Datetime Columns
- Date range analysis
- Temporal pattern detection
- Most common year/month/day

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/data-profiler.git
cd data-profiler

# Install dependencies
pip install -e ".[dev]"
```

### Usage as Library

```python
from data_profiler import DataProfiler
import pandas as pd

# Create sample data
df = pd.DataFrame({
    'id': range(1000),
    'value': range(100, 1100),
    'category': ['A', 'B', 'C'] * 333 + ['A']
})

# Profile the data
profiler = DataProfiler()
profile = profiler.profile(df)

# Access results
print(f"Rows: {profile.row_count}")
print(f"Columns: {profile.column_count}")
print(f"Duration: {profile.profiling_duration_seconds:.2f}s")

# Examine column profiles
for col in profile.columns:
    print(f"\n{col.name} ({col.type})")
    print(f"  Completeness: {col.quality.completeness:.1f}%")
    if col.numeric_stats:
        print(f"  Mean: {col.numeric_stats.mean:.2f}")
```

### Usage with API

#### Start the API Server

```bash
# Using uvicorn directly
uvicorn data_profiler.api.main:app --reload

# Using Docker
docker-compose up

# Using Docker build
docker build -t data-profiler .
docker run -p 8000:8000 data-profiler
```

#### API Endpoints

**Upload and Profile a File:**

```bash
curl -X POST "http://localhost:8000/api/v1/profile/upload" \
  -F "file=@data.csv" \
  -F "sample_size=10000" \
  -F "parallel=true"
```

**Profile from URL:**

```bash
curl -X POST "http://localhost:8000/api/v1/profile/url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/data.csv",
    "sample_size": 10000,
    "compute_correlations": true
  }'
```

**Interactive API Documentation:**

Visit `http://localhost:8000/docs` for Swagger UI or `http://localhost:8000/redoc` for ReDoc.

## Configuration

### ProfileConfig Options

```python
from data_profiler import DataProfiler
from data_profiler.models.config import ProfileConfig

config = ProfileConfig(
    # Performance
    sample_size=100_000,        # Sample large datasets
    parallel=True,              # Enable parallel processing
    max_workers=8,              # Number of parallel workers
    chunk_size=100_000,         # Chunk size for large datasets

    # Statistical analysis
    compute_correlations=True,  # Correlation matrix
    compute_percentiles=True,   # Percentile statistics
    histogram_bins=50,          # Histogram resolution

    # Data quality
    detect_outliers=True,       # Outlier detection
    outlier_threshold=1.5,      # IQR multiplier

    # Text analysis
    detect_patterns=True,       # Pattern detection
    max_string_length_sample=1000,  # Sample size for text
)

profiler = DataProfiler(config=config)
profile = profiler.profile(df)
```

## Architecture

### Design Principles

1. **Performance First** - Every operation optimized for speed
   - Vectorized NumPy operations
   - Parallel processing for independent operations
   - Efficient algorithms (single-pass statistics)
   - Lazy evaluation where beneficial

2. **Scalability** - Handle datasets of any size
   - Configurable sampling for large datasets
   - Chunked processing for memory efficiency
   - Async API for non-blocking operations

3. **Accuracy** - Reliable statistical computations
   - Industry-standard algorithms
   - Proper handling of edge cases
   - Validated against known datasets

4. **Maintainability** - Clean, testable code
   - Type hints throughout
   - Comprehensive test coverage
   - Clear separation of concerns
   - Well-documented APIs

### Project Structure

```
data-profiler/
├── src/data_profiler/
│   ├── core/              # Core profiling engine
│   │   ├── profiler.py    # Main orchestrator
│   │   └── analyzers/     # Type-specific analyzers
│   ├── models/            # Pydantic data models
│   ├── api/               # FastAPI service
│   └── utils/             # Utilities
├── tests/                 # Comprehensive test suite
├── docker/                # Docker configuration
└── docs/                  # Documentation
```

## Performance

### Benchmarks

Tested on: Apple M1 Pro, 16GB RAM, Python 3.11

| Dataset Size | Columns | Profile Time | Throughput |
|--------------|---------|--------------|------------|
| 1K rows      | 10      | 0.05s       | 20K rows/s |
| 10K rows     | 10      | 0.15s       | 67K rows/s |
| 100K rows    | 10      | 0.8s        | 125K rows/s|
| 1M rows      | 10      | 5.2s        | 192K rows/s|

### Optimization Techniques

1. **Vectorized Operations** - NumPy/Pandas for batch processing
2. **Parallel Processing** - ThreadPoolExecutor for column-level parallelism
3. **Efficient Algorithms**:
   - Single-pass statistics computation
   - HyperLogLog for cardinality estimation
   - Sampling for pattern detection
4. **Memory Optimization** - Chunked processing for large datasets

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run with coverage
pytest --cov=src/data_profiler --cov-report=html

# Run benchmarks
pytest tests/test_performance.py --benchmark-only

# Lint code
ruff check src/ tests/
black src/ tests/
mypy src/
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_profiler.py

# With coverage
pytest --cov=src/data_profiler

# Performance benchmarks
pytest tests/test_performance.py -v
```

### Code Quality

This project uses:
- **Ruff** - Fast Python linter
- **Black** - Code formatter
- **MyPy** - Static type checker
- **Pre-commit** - Git hooks for quality checks
- **Pytest** - Testing framework

## Docker Deployment

### Build and Run

```bash
# Build image
docker build -t data-profiler:latest .

# Run container
docker run -p 8000:8000 data-profiler:latest

# Using docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Variables

```bash
# .env file
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE=100MB
```

## API Reference

### Endpoints

#### `POST /api/v1/profile/upload`

Upload and profile a file.

**Parameters:**
- `file` (form-data): File to profile (CSV, Parquet, JSON)
- `sample_size` (optional): Maximum rows to sample
- `compute_correlations` (optional): Compute correlation matrix
- `compute_percentiles` (optional): Compute percentiles
- `detect_outliers` (optional): Detect outliers
- `parallel` (optional): Enable parallel processing

**Response:** DataProfile object (JSON)

#### `POST /api/v1/profile/url`

Profile a dataset from URL.

**Body:**
```json
{
  "url": "https://example.com/data.csv",
  "sample_size": 10000,
  "compute_correlations": true
}
```

**Response:** DataProfile object (JSON)

#### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

## Roadmap

- [ ] Support for more file formats (Excel, Avro, ORC)
- [ ] Custom pattern detection
- [ ] Data profiling comparison (drift detection)
- [ ] Automated data quality rules
- [ ] Rust extensions for critical performance paths
- [ ] Distributed processing support (Dask/Ray)
- [ ] Web UI for interactive profiling
- [ ] Export profiles to various formats

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run code quality checks
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Pandas](https://pandas.pydata.org/) - Data manipulation
- [NumPy](https://numpy.org/) - Numerical computing
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [Uvicorn](https://www.uvicorn.org/) - ASGI server

---

**Built with ⚡ by principal data engineers, for data engineers.**
