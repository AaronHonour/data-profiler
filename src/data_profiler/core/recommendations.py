"""Recommendations engine for data quality and optimization."""

from typing import List

from data_profiler.models.profile import ColumnProfile, ColumnType, DataProfile, Recommendation


class RecommendationsEngine:
    """Generate data quality and optimization recommendations."""

    @classmethod
    def generate_recommendations(cls, profile: DataProfile) -> List[Recommendation]:
        """
        Generate recommendations from a data profile.

        Args:
            profile: Complete data profile

        Returns:
            List of recommendations
        """
        recommendations = []

        # Dataset-level recommendations
        recommendations.extend(cls._check_duplicate_rows(profile))
        recommendations.extend(cls._check_memory_usage(profile))

        # Column-level recommendations
        for col_profile in profile.columns:
            recommendations.extend(cls._check_column_quality(col_profile))
            recommendations.extend(cls._check_column_optimization(col_profile, profile.row_count))

        # Sort by severity
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        recommendations.sort(key=lambda r: severity_order.get(r.severity, 3))

        return recommendations

    @classmethod
    def _check_duplicate_rows(cls, profile: DataProfile) -> List[Recommendation]:
        """Check for duplicate rows."""
        recommendations = []

        if profile.duplicate_row_percentage > 10:
            recommendations.append(
                Recommendation(
                    severity="warning",
                    category="data_quality",
                    title="High duplicate row percentage",
                    description=f"{profile.duplicate_row_percentage:.1f}% of rows are duplicates ({profile.duplicate_rows:,} rows)",
                    suggestion="Consider removing duplicate rows or investigating the cause of duplication",
                )
            )

        return recommendations

    @classmethod
    def _check_memory_usage(cls, profile: DataProfile) -> List[Recommendation]:
        """Check memory usage and suggest optimizations."""
        recommendations = []

        # Large dataset warning
        memory_mb = profile.memory_bytes / (1024**2)
        if memory_mb > 1000:  # > 1 GB
            recommendations.append(
                Recommendation(
                    severity="info",
                    category="performance",
                    title="Large dataset detected",
                    description=f"Dataset uses {memory_mb:.1f} MB of memory",
                    suggestion="Consider using sampling, chunked processing, or data type optimization",
                )
            )

        return recommendations

    @classmethod
    def _check_column_quality(cls, col_profile: ColumnProfile) -> List[Recommendation]:
        """Check column data quality."""
        recommendations = []

        # High null percentage
        if col_profile.quality.null_percentage > 50:
            recommendations.append(
                Recommendation(
                    severity="critical" if col_profile.quality.null_percentage > 80 else "warning",
                    category="data_quality",
                    column=col_profile.name,
                    title=f"High null percentage in column '{col_profile.name}'",
                    description=f"{col_profile.quality.null_percentage:.1f}% of values are null",
                    suggestion="Consider dropping this column, imputing missing values, or investigating data collection issues",
                )
            )

        # Low uniqueness (potential data quality issue)
        if col_profile.type == ColumnType.TEXT and col_profile.quality.uniqueness < 5:
            recommendations.append(
                Recommendation(
                    severity="info",
                    category="data_quality",
                    column=col_profile.name,
                    title=f"Low uniqueness in text column '{col_profile.name}'",
                    description=f"Only {col_profile.quality.uniqueness:.1f}% of values are unique",
                    suggestion="Consider converting to categorical type or using encoding",
                )
            )

        # PII risk
        if col_profile.text_stats and col_profile.text_stats.pii_risk_level == "high":
            recommendations.append(
                Recommendation(
                    severity="critical",
                    category="security",
                    column=col_profile.name,
                    title=f"PII detected in column '{col_profile.name}'",
                    description="Column contains potentially sensitive personal information (SSN, credit cards, etc.)",
                    suggestion="Ensure proper encryption, access controls, and compliance with data privacy regulations",
                )
            )
        elif col_profile.text_stats and col_profile.text_stats.pii_risk_level == "medium":
            recommendations.append(
                Recommendation(
                    severity="warning",
                    category="security",
                    column=col_profile.name,
                    title=f"Potential PII in column '{col_profile.name}'",
                    description="Column may contain personal information (emails, phone numbers)",
                    suggestion="Review data handling practices and consider anonymization",
                )
            )

        # Outliers
        if col_profile.numeric_stats and col_profile.numeric_stats.outlier_count:
            outlier_pct = (col_profile.numeric_stats.outlier_count / col_profile.row_count) * 100
            if outlier_pct > 5:
                recommendations.append(
                    Recommendation(
                        severity="info",
                        category="data_quality",
                        column=col_profile.name,
                        title=f"Outliers detected in column '{col_profile.name}'",
                        description=f"{outlier_pct:.1f}% of values are outliers ({col_profile.numeric_stats.outlier_count} values)",
                        suggestion="Investigate outliers - they may indicate data quality issues or important edge cases",
                    )
                )

        return recommendations

    @classmethod
    def _check_column_optimization(cls, col_profile: ColumnProfile, row_count: int) -> List[Recommendation]:
        """Check column optimization opportunities."""
        recommendations = []

        # Categorical encoding opportunity
        if col_profile.type == ColumnType.TEXT and col_profile.categorical_stats:
            unique_count = col_profile.categorical_stats.unique_count
            unique_ratio = unique_count / row_count if row_count > 0 else 0

            if unique_ratio < 0.05:  # Less than 5% unique values
                recommendations.append(
                    Recommendation(
                        severity="info",
                        category="performance",
                        column=col_profile.name,
                        title=f"Categorical encoding opportunity: '{col_profile.name}'",
                        description=f"Column has only {unique_count} unique values ({unique_ratio*100:.1f}% of dataset)",
                        suggestion="Consider using categorical encoding or ENUM type to save memory",
                    )
                )

        # Large text column
        if col_profile.text_stats and col_profile.text_stats.avg_length:
            if col_profile.text_stats.avg_length > 1000:
                recommendations.append(
                    Recommendation(
                        severity="info",
                        category="performance",
                        column=col_profile.name,
                        title=f"Large text column: '{col_profile.name}'",
                        description=f"Average text length is {col_profile.text_stats.avg_length:.0f} characters",
                        suggestion="Consider storing large text separately or using compression",
                    )
                )

        # High cardinality categorical
        if col_profile.type == ColumnType.CATEGORICAL and col_profile.categorical_stats:
            if col_profile.categorical_stats.unique_count > row_count * 0.9:
                recommendations.append(
                    Recommendation(
                        severity="info",
                        category="schema",
                        column=col_profile.name,
                        title=f"High cardinality categorical: '{col_profile.name}'",
                        description=f"Column has {col_profile.categorical_stats.unique_count} unique values (>{row_count * 0.9:.0f})",
                        suggestion="Consider if this should be indexed or treated as a unique identifier",
                    )
                )

        # Non-normal numeric distribution
        if col_profile.numeric_stats and col_profile.numeric_stats.normality_tests:
            tests = col_profile.numeric_stats.normality_tests.tests
            if "shapiro_wilk" in tests and not tests["shapiro_wilk"].get("is_normal", True):
                recommendations.append(
                    Recommendation(
                        severity="info",
                        category="data_quality",
                        column=col_profile.name,
                        title=f"Non-normal distribution: '{col_profile.name}'",
                        description="Data does not follow a normal distribution",
                        suggestion="Consider transformations (log, sqrt) if normal distribution is required for analysis",
                    )
                )

        return recommendations
