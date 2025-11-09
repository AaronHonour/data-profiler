# Benchmarking Suite

This directory contains the benchmarking suite for the data profiler.

## Running Benchmarks

```bash
# Run all benchmarks
python benchmarks/run_benchmarks.py

# Generate report from results
python benchmarks/generate_report.py
```

## Benchmark Categories

1. **Size Scaling** - Tests performance with datasets from 1K to 1M rows
2. **Width Scaling** - Tests performance with varying column counts (5-100 columns)
3. **Parallel vs Sequential** - Compares multi-threaded vs single-threaded execution
4. **Data Type Performance** - Compares profiling speed across different data types
5. **Sampling Impact** - Measures the performance benefit of sampling on large datasets

## Output Files

- `results/benchmark_results.csv` - Raw benchmark data in CSV format
- `results/benchmark_results.json` - Complete results with system info in JSON
- `results/PERFORMANCE_REPORT.md` - Comprehensive markdown report

## Key Findings

See [PERFORMANCE_REPORT.md](results/PERFORMANCE_REPORT.md) for detailed analysis.

### Quick Stats

- **Peak Throughput:** 1.5M rows/second
- **1M Row Dataset:** Profiled in 3.68 seconds
- **Sampling Speedup:** Up to 5.5x faster with 10K sampling
- **Average Time per Column:** ~7.8ms

### Recommendations

- **Small datasets (<100K rows):** No sampling needed, sub-second profiling
- **Medium datasets (100K-1M rows):** Enable parallel processing
- **Large datasets (>1M rows):** Use sampling (10K-100K) for optimal speed
