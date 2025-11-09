"""Profile comparison and drift detection."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from data_profiler.models.profile import ColumnProfile, ColumnType, DataProfile


class DriftMetric(BaseModel):
    """Individual drift metric."""

    metric_name: str = Field(description="Name of the metric")
    baseline_value: Optional[float] = None
    current_value: Optional[float] = None
    absolute_change: Optional[float] = None
    relative_change_pct: Optional[float] = None
    drift_score: float = Field(description="Drift score (0-1, higher = more drift)")
    is_significant: bool = Field(description="Whether drift is statistically significant")


class ColumnDrift(BaseModel):
    """Drift analysis for a single column."""

    column_name: str
    drift_detected: bool
    drift_severity: str = Field(description="none, low, medium, high, critical")
    drift_score: float = Field(description="Overall drift score (0-1)")

    # Changes detected
    type_changed: bool = False
    schema_changed: bool = False
    quality_degraded: bool = False
    distribution_shifted: bool = False

    # Detailed metrics
    metrics: List[DriftMetric] = Field(default_factory=list)
    changes: List[str] = Field(default_factory=list, description="Human-readable changes")


class DatasetDrift(BaseModel):
    """Complete drift analysis between two profiles."""

    baseline_timestamp: datetime
    current_timestamp: datetime
    time_elapsed_days: float

    # Overall assessment
    drift_detected: bool
    overall_drift_score: float = Field(description="Overall drift score (0-1)")
    drift_severity: str = Field(description="none, low, medium, high, critical")

    # Column-level drift
    columns_analyzed: int
    columns_with_drift: int
    columns_added: List[str] = Field(default_factory=list)
    columns_removed: List[str] = Field(default_factory=list)
    column_drifts: List[ColumnDrift] = Field(default_factory=list)

    # Dataset-level changes
    row_count_change_pct: float
    memory_change_pct: float
    duplicate_row_change_pct: float

    # Summary
    critical_drifts: int = 0
    high_drifts: int = 0
    medium_drifts: int = 0
    low_drifts: int = 0


class ProfileComparator:
    """Compare data profiles to detect drift over time."""

    # Thresholds for drift detection
    DRIFT_THRESHOLDS = {
        "critical": 0.8,
        "high": 0.6,
        "medium": 0.4,
        "low": 0.2,
    }

    @classmethod
    def compare(
        cls,
        baseline: DataProfile,
        current: DataProfile,
        significance_threshold: float = 0.1,
    ) -> DatasetDrift:
        """
        Compare two data profiles and detect drift.

        Args:
            baseline: Earlier profile (reference)
            current: Current profile to compare against baseline
            significance_threshold: Threshold for statistical significance (0-1)

        Returns:
            DatasetDrift object with complete drift analysis
        """
        # Calculate time elapsed
        time_elapsed = (current.profile_timestamp - baseline.profile_timestamp).total_seconds() / 86400

        # Dataset-level changes
        row_count_change = cls._calc_relative_change(baseline.row_count, current.row_count)
        memory_change = cls._calc_relative_change(baseline.memory_bytes, current.memory_bytes)
        duplicate_change = cls._calc_relative_change(
            baseline.duplicate_row_percentage, current.duplicate_row_percentage
        )

        # Identify column changes
        baseline_cols = {col.name for col in baseline.columns}
        current_cols = {col.name for col in current.columns}

        columns_added = list(current_cols - baseline_cols)
        columns_removed = list(baseline_cols - current_cols)
        common_columns = baseline_cols & current_cols

        # Analyze drift for common columns
        column_drifts = []
        for col_name in common_columns:
            baseline_col = next(c for c in baseline.columns if c.name == col_name)
            current_col = next(c for c in current.columns if c.name == col_name)

            drift = cls._compare_columns(baseline_col, current_col, significance_threshold)
            column_drifts.append(drift)

        # Calculate overall drift metrics
        columns_with_drift = sum(1 for d in column_drifts if d.drift_detected)

        # Count by severity
        severity_counts = {
            "critical": sum(1 for d in column_drifts if d.drift_severity == "critical"),
            "high": sum(1 for d in column_drifts if d.drift_severity == "high"),
            "medium": sum(1 for d in column_drifts if d.drift_severity == "medium"),
            "low": sum(1 for d in column_drifts if d.drift_severity == "low"),
        }

        # Overall drift score (weighted average)
        if column_drifts:
            overall_drift_score = sum(d.drift_score for d in column_drifts) / len(column_drifts)
        else:
            overall_drift_score = 0.0

        # Determine overall severity
        drift_detected = columns_with_drift > 0 or len(columns_added) > 0 or len(columns_removed) > 0
        overall_severity = cls._classify_drift_severity(overall_drift_score)

        return DatasetDrift(
            baseline_timestamp=baseline.profile_timestamp,
            current_timestamp=current.profile_timestamp,
            time_elapsed_days=time_elapsed,
            drift_detected=drift_detected,
            overall_drift_score=overall_drift_score,
            drift_severity=overall_severity,
            columns_analyzed=len(common_columns),
            columns_with_drift=columns_with_drift,
            columns_added=columns_added,
            columns_removed=columns_removed,
            column_drifts=column_drifts,
            row_count_change_pct=row_count_change,
            memory_change_pct=memory_change,
            duplicate_row_change_pct=duplicate_change,
            critical_drifts=severity_counts["critical"],
            high_drifts=severity_counts["high"],
            medium_drifts=severity_counts["medium"],
            low_drifts=severity_counts["low"],
        )

    @classmethod
    def _compare_columns(
        cls, baseline: ColumnProfile, current: ColumnProfile, threshold: float
    ) -> ColumnDrift:
        """Compare two column profiles."""
        metrics = []
        changes = []

        # Check for type change
        type_changed = baseline.type != current.type
        if type_changed:
            changes.append(f"Type changed: {baseline.type.value} → {current.type.value}")

        # Quality metrics comparison
        quality_metrics = cls._compare_quality_metrics(baseline, current, threshold)
        metrics.extend(quality_metrics["metrics"])
        changes.extend(quality_metrics["changes"])
        quality_degraded = quality_metrics["degraded"]

        # Type-specific comparisons
        distribution_shifted = False
        if baseline.type == current.type == ColumnType.NUMERIC and baseline.numeric_stats and current.numeric_stats:
            numeric_metrics = cls._compare_numeric_stats(baseline.numeric_stats, current.numeric_stats, threshold)
            metrics.extend(numeric_metrics["metrics"])
            changes.extend(numeric_metrics["changes"])
            distribution_shifted = numeric_metrics["shifted"]

        elif baseline.type == current.type == ColumnType.CATEGORICAL and baseline.categorical_stats and current.categorical_stats:
            cat_metrics = cls._compare_categorical_stats(baseline.categorical_stats, current.categorical_stats, threshold)
            metrics.extend(cat_metrics["metrics"])
            changes.extend(cat_metrics["changes"])

        # Calculate overall drift score
        if metrics:
            drift_score = sum(m.drift_score for m in metrics) / len(metrics)
        else:
            drift_score = 1.0 if type_changed else 0.0

        # Determine drift severity
        drift_detected = drift_score > threshold or type_changed
        severity = cls._classify_drift_severity(drift_score) if drift_detected else "none"

        return ColumnDrift(
            column_name=baseline.name,
            drift_detected=drift_detected,
            drift_severity=severity,
            drift_score=drift_score,
            type_changed=type_changed,
            quality_degraded=quality_degraded,
            distribution_shifted=distribution_shifted,
            metrics=metrics,
            changes=changes,
        )

    @classmethod
    def _compare_quality_metrics(cls, baseline: ColumnProfile, current: ColumnProfile, threshold: float) -> Dict:
        """Compare data quality metrics."""
        metrics = []
        changes = []
        degraded = False

        # Completeness
        completeness_change = current.quality.completeness - baseline.quality.completeness
        if abs(completeness_change) > threshold * 100:
            metrics.append(DriftMetric(
                metric_name="completeness",
                baseline_value=baseline.quality.completeness,
                current_value=current.quality.completeness,
                absolute_change=completeness_change,
                relative_change_pct=cls._calc_relative_change(baseline.quality.completeness, current.quality.completeness),
                drift_score=abs(completeness_change) / 100,
                is_significant=True,
            ))
            changes.append(f"Completeness: {baseline.quality.completeness:.1f}% → {current.quality.completeness:.1f}%")
            if completeness_change < 0:
                degraded = True

        # Uniqueness
        uniqueness_change = current.quality.uniqueness - baseline.quality.uniqueness
        if abs(uniqueness_change) > threshold * 100:
            metrics.append(DriftMetric(
                metric_name="uniqueness",
                baseline_value=baseline.quality.uniqueness,
                current_value=current.quality.uniqueness,
                absolute_change=uniqueness_change,
                relative_change_pct=cls._calc_relative_change(baseline.quality.uniqueness, current.quality.uniqueness),
                drift_score=abs(uniqueness_change) / 100,
                is_significant=True,
            ))
            changes.append(f"Uniqueness: {baseline.quality.uniqueness:.1f}% → {current.quality.uniqueness:.1f}%")

        return {"metrics": metrics, "changes": changes, "degraded": degraded}

    @classmethod
    def _compare_numeric_stats(cls, baseline, current, threshold: float) -> Dict:
        """Compare numeric statistics."""
        metrics = []
        changes = []
        shifted = False

        # Mean
        if baseline.mean and current.mean:
            rel_change = cls._calc_relative_change(baseline.mean, current.mean)
            if abs(rel_change) > threshold * 100:
                metrics.append(DriftMetric(
                    metric_name="mean",
                    baseline_value=baseline.mean,
                    current_value=current.mean,
                    absolute_change=current.mean - baseline.mean,
                    relative_change_pct=rel_change,
                    drift_score=min(abs(rel_change) / 100, 1.0),
                    is_significant=True,
                ))
                changes.append(f"Mean: {baseline.mean:.2f} → {current.mean:.2f} ({rel_change:+.1f}%)")
                shifted = True

        # Standard deviation
        if baseline.std and current.std:
            rel_change = cls._calc_relative_change(baseline.std, current.std)
            if abs(rel_change) > threshold * 100:
                metrics.append(DriftMetric(
                    metric_name="std",
                    baseline_value=baseline.std,
                    current_value=current.std,
                    absolute_change=current.std - baseline.std,
                    relative_change_pct=rel_change,
                    drift_score=min(abs(rel_change) / 100, 1.0),
                    is_significant=True,
                ))
                changes.append(f"Std Dev: {baseline.std:.2f} → {current.std:.2f} ({rel_change:+.1f}%)")
                shifted = True

        return {"metrics": metrics, "changes": changes, "shifted": shifted}

    @classmethod
    def _compare_categorical_stats(cls, baseline, current, threshold: float) -> Dict:
        """Compare categorical statistics."""
        metrics = []
        changes = []

        # Unique count
        rel_change = cls._calc_relative_change(baseline.unique_count, current.unique_count)
        if abs(rel_change) > threshold * 100:
            metrics.append(DriftMetric(
                metric_name="unique_count",
                baseline_value=float(baseline.unique_count),
                current_value=float(current.unique_count),
                absolute_change=float(current.unique_count - baseline.unique_count),
                relative_change_pct=rel_change,
                drift_score=min(abs(rel_change) / 100, 1.0),
                is_significant=True,
            ))
            changes.append(f"Unique values: {baseline.unique_count} → {current.unique_count} ({rel_change:+.1f}%)")

        return {"metrics": metrics, "changes": changes}

    @staticmethod
    def _calc_relative_change(baseline: float, current: float) -> float:
        """Calculate relative change percentage."""
        if baseline == 0:
            return 100.0 if current != 0 else 0.0
        return ((current - baseline) / baseline) * 100

    @classmethod
    def _classify_drift_severity(cls, drift_score: float) -> str:
        """Classify drift severity based on score."""
        if drift_score >= cls.DRIFT_THRESHOLDS["critical"]:
            return "critical"
        elif drift_score >= cls.DRIFT_THRESHOLDS["high"]:
            return "high"
        elif drift_score >= cls.DRIFT_THRESHOLDS["medium"]:
            return "medium"
        elif drift_score >= cls.DRIFT_THRESHOLDS["low"]:
            return "low"
        else:
            return "none"

    @classmethod
    def generate_drift_report(cls, drift: DatasetDrift) -> str:
        """Generate human-readable drift report."""
        report = []
        report.append("=" * 70)
        report.append("DATA DRIFT ANALYSIS REPORT")
        report.append("=" * 70)
        report.append(f"\nBaseline: {drift.baseline_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Current:  {drift.current_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Time Elapsed: {drift.time_elapsed_days:.1f} days")

        report.append(f"\n{'OVERALL ASSESSMENT':-^70}")
        severity_icon = {"none": "✅", "low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(drift.drift_severity, "⚪")
        report.append(f"{severity_icon} Drift Severity: {drift.drift_severity.upper()}")
        report.append(f"Overall Drift Score: {drift.overall_drift_score:.3f}")
        report.append(f"Columns with Drift: {drift.columns_with_drift}/{drift.columns_analyzed}")

        if drift.columns_added:
            report.append(f"\n✨ Columns Added: {', '.join(drift.columns_added)}")
        if drift.columns_removed:
            report.append(f"\n🗑️  Columns Removed: {', '.join(drift.columns_removed)}")

        report.append(f"\n{'DATASET-LEVEL CHANGES':-^70}")
        report.append(f"Row Count Change: {drift.row_count_change_pct:+.1f}%")
        report.append(f"Memory Usage Change: {drift.memory_change_pct:+.1f}%")
        report.append(f"Duplicate Rows Change: {drift.duplicate_row_change_pct:+.1f}%")

        if drift.columns_with_drift > 0:
            report.append(f"\n{'COLUMN-LEVEL DRIFT':-^70}")
            report.append(f"Critical: {drift.critical_drifts} | High: {drift.high_drifts} | Medium: {drift.medium_drifts} | Low: {drift.low_drifts}")

            # Show top drifted columns
            sorted_drifts = sorted(drift.column_drifts, key=lambda x: x.drift_score, reverse=True)
            for col_drift in sorted_drifts[:10]:  # Top 10
                if col_drift.drift_detected:
                    icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(col_drift.drift_severity, "⚪")
                    report.append(f"\n{icon} {col_drift.column_name} (score: {col_drift.drift_score:.3f})")
                    for change in col_drift.changes[:5]:  # Top 5 changes
                        report.append(f"    • {change}")

        report.append("\n" + "=" * 70)
        return "\n".join(report)
