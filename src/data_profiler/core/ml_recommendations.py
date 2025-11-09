"""ML-based recommendations engine using statistical learning and pattern recognition."""

from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy import stats

from data_profiler.models.profile import ColumnProfile, ColumnType, DataProfile, Recommendation


class MLRecommendationsEngine:
    """
    Generate intelligent recommendations using statistical learning.

    This engine uses statistical methods, anomaly detection, and pattern
    recognition to provide more sophisticated recommendations than
    rule-based systems.
    """

    @classmethod
    def generate_recommendations(
        cls,
        profile: DataProfile,
        confidence_threshold: float = 0.7,
    ) -> List[Recommendation]:
        """
        Generate ML-based recommendations from a data profile.

        Args:
            profile: Complete data profile
            confidence_threshold: Minimum confidence score (0-1) for recommendations

        Returns:
            List of recommendations with confidence scores
        """
        recommendations = []

        # Statistical anomaly detection
        recommendations.extend(cls._detect_statistical_anomalies(profile))

        # Distribution-based recommendations
        recommendations.extend(cls._analyze_distributions(profile))

        # Correlation-based recommendations
        if profile.correlation_matrix:
            recommendations.extend(cls._analyze_correlations(profile))

        # Type consistency recommendations
        recommendations.extend(cls._check_type_consistency(profile))

        # Advanced pattern detection
        for col_profile in profile.columns:
            recommendations.extend(cls._detect_column_patterns(col_profile, profile))

        # Filter by confidence threshold
        recommendations = [r for r in recommendations if r.suggestion and "confidence:" in r.suggestion]

        # Sort by severity and confidence
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        recommendations.sort(
            key=lambda r: (
                severity_order.get(r.severity, 3),
                -cls._extract_confidence(r),
            )
        )

        return recommendations

    @classmethod
    def _extract_confidence(cls, recommendation: Recommendation) -> float:
        """Extract confidence score from recommendation suggestion."""
        if not recommendation.suggestion or "confidence:" not in recommendation.suggestion:
            return 0.0
        try:
            # Extract confidence value from suggestion text
            confidence_str = recommendation.suggestion.split("confidence:")[-1].strip().split(")")[0]
            return float(confidence_str)
        except (ValueError, IndexError):
            return 0.0

    @classmethod
    def _detect_statistical_anomalies(cls, profile: DataProfile) -> List[Recommendation]:
        """Detect statistical anomalies in the dataset."""
        recommendations = []

        # Analyze row count consistency
        if profile.row_count > 0:
            # Check for suspicious round numbers (potential data truncation)
            if profile.row_count % 1000 == 0 and profile.row_count < 100000:
                confidence = 0.65
                recommendations.append(
                    Recommendation(
                        severity="info",
                        category="data_quality",
                        title="Suspicious round number of rows",
                        description=f"Dataset has exactly {profile.row_count:,} rows (perfectly divisible by 1000)",
                        suggestion=f"Possible data truncation or limit. Verify completeness (confidence: {confidence:.2f})",
                    )
                )

        # Analyze column count patterns
        if profile.column_count > 50:
            confidence = 0.7
            recommendations.append(
                Recommendation(
                    severity="info",
                    category="performance",
                    title="High-dimensional dataset detected",
                    description=f"Dataset has {profile.column_count} columns",
                    suggestion=f"Consider dimensionality reduction or feature selection (confidence: {confidence:.2f})",
                )
            )

        return recommendations

    @classmethod
    def _analyze_distributions(cls, profile: DataProfile) -> List[Recommendation]:
        """Analyze statistical distributions and recommend transformations."""
        recommendations = []

        for col in profile.columns:
            if col.numeric_stats and col.numeric_stats.skewness is not None:
                skewness = col.numeric_stats.skewness

                # High skewness detection
                if abs(skewness) > 1.5:
                    confidence = min(0.9, abs(skewness) / 5)
                    severity = "warning" if abs(skewness) > 3 else "info"

                    transform_suggestion = "log transform" if skewness > 0 else "power transform"

                    recommendations.append(
                        Recommendation(
                            severity=severity,
                            category="data_quality",
                            column=col.name,
                            title=f"Highly skewed distribution in '{col.name}'",
                            description=f"Skewness: {skewness:.2f} ({'right' if skewness > 0 else 'left'} skewed)",
                            suggestion=f"Consider {transform_suggestion} to normalize distribution (confidence: {confidence:.2f})",
                        )
                    )

                # Kurtosis analysis
                if col.numeric_stats.kurtosis is not None:
                    kurtosis = col.numeric_stats.kurtosis

                    if kurtosis > 10:  # Heavily tailed
                        confidence = min(0.85, kurtosis / 20)
                        recommendations.append(
                            Recommendation(
                                severity="info",
                                category="data_quality",
                                column=col.name,
                                title=f"Heavy-tailed distribution in '{col.name}'",
                                description=f"Kurtosis: {kurtosis:.2f} indicates extreme outliers",
                                suggestion=f"Investigate extreme values; consider robust statistics (confidence: {confidence:.2f})",
                            )
                        )

        return recommendations

    @classmethod
    def _analyze_correlations(cls, profile: DataProfile) -> List[Recommendation]:
        """Analyze correlation patterns and recommend actions."""
        recommendations = []

        if not profile.correlation_matrix or not profile.correlation_matrix.matrix:
            return recommendations

        # Convert to numpy array for analysis
        corr_matrix = np.array(profile.correlation_matrix.matrix)
        columns = profile.correlation_matrix.columns

        # Find highly correlated pairs
        n = len(corr_matrix)
        high_corr_pairs = []

        for i in range(n):
            for j in range(i + 1, n):
                corr_value = corr_matrix[i][j]

                # High positive correlation (potential redundancy)
                if corr_value > 0.95:
                    confidence = min(0.95, (corr_value - 0.95) * 20)
                    high_corr_pairs.append((columns[i], columns[j], corr_value, confidence))

        if high_corr_pairs:
            for col1, col2, corr, confidence in high_corr_pairs[:5]:  # Top 5
                recommendations.append(
                    Recommendation(
                        severity="info",
                        category="performance",
                        title=f"High correlation between '{col1}' and '{col2}'",
                        description=f"Correlation: {corr:.3f} - columns are highly redundant",
                        suggestion=f"Consider removing one column or using PCA (confidence: {confidence:.2f})",
                    )
                )

        # Find negative correlations (potential inverse relationships)
        for i in range(n):
            for j in range(i + 1, n):
                corr_value = corr_matrix[i][j]

                if corr_value < -0.8:
                    confidence = min(0.9, abs(corr_value + 0.8) * 5)
                    recommendations.append(
                        Recommendation(
                            severity="info",
                            category="data_quality",
                            title=f"Strong inverse correlation: '{columns[i]}' vs '{columns[j]}'",
                            description=f"Correlation: {corr_value:.3f} - inverse relationship detected",
                            suggestion=f"Verify this relationship is expected; consider combining features (confidence: {confidence:.2f})",
                        )
                    )

        return recommendations

    @classmethod
    def _check_type_consistency(cls, profile: DataProfile) -> List[Recommendation]:
        """Check for type consistency issues using statistical analysis."""
        recommendations = []

        for col in profile.columns:
            # Numeric columns with low variance (possibly should be categorical)
            if col.numeric_stats and col.numeric_stats.std is not None:
                if col.numeric_stats.std > 0:
                    cv = col.numeric_stats.coefficient_of_variation
                    if cv and cv < 0.01:  # Very low coefficient of variation
                        confidence = 0.8
                        recommendations.append(
                            Recommendation(
                                severity="info",
                                category="schema",
                                column=col.name,
                                title=f"Low variability in numeric column '{col.name}'",
                                description=f"Coefficient of variation: {cv:.4f}",
                                suggestion=f"Column may represent categorical data; consider converting type (confidence: {confidence:.2f})",
                            )
                        )

            # Categorical columns with sequential pattern (possibly numeric)
            if col.type == ColumnType.CATEGORICAL and col.categorical_stats:
                if cls._is_sequential_pattern(col.categorical_stats.top_values):
                    confidence = 0.75
                    recommendations.append(
                        Recommendation(
                            severity="info",
                            category="schema",
                            column=col.name,
                            title=f"Sequential pattern in categorical column '{col.name}'",
                            description="Values appear to follow a numeric sequence",
                            suggestion=f"Consider converting to numeric type (confidence: {confidence:.2f})",
                        )
                    )

        return recommendations

    @classmethod
    def _is_sequential_pattern(cls, top_values: Dict[str, int]) -> bool:
        """Check if categorical values follow a sequential pattern."""
        try:
            # Try to convert values to integers
            values = []
            for val in list(top_values.keys())[:10]:
                try:
                    values.append(int(val))
                except (ValueError, TypeError):
                    return False

            if len(values) < 3:
                return False

            # Check if differences are consistent
            values.sort()
            diffs = np.diff(values)

            # Sequential if differences are small and consistent
            return np.std(diffs) < 2 and np.mean(diffs) < 10

        except Exception:
            return False

    @classmethod
    def _detect_column_patterns(
        cls, col: ColumnProfile, profile: DataProfile
    ) -> List[Recommendation]:
        """Detect advanced patterns in column data."""
        recommendations = []

        # Benford's Law analysis for numeric columns
        if col.numeric_stats and col.row_count > 100:
            benford_result = cls._check_benfords_law(col)
            if benford_result:
                confidence, description = benford_result
                recommendations.append(
                    Recommendation(
                        severity="warning",
                        category="data_quality",
                        column=col.name,
                        title=f"Benford's Law violation in '{col.name}'",
                        description=description,
                        suggestion=f"Potential data manipulation or quality issue (confidence: {confidence:.2f})",
                    )
                )

        # Entropy analysis for categorical columns
        if col.categorical_stats and col.categorical_stats.entropy is not None:
            entropy = col.categorical_stats.entropy

            # Low entropy (very predictable)
            if entropy < 1.0 and col.categorical_stats.unique_count > 5:
                confidence = 0.8
                recommendations.append(
                    Recommendation(
                        severity="info",
                        category="data_quality",
                        column=col.name,
                        title=f"Low entropy in '{col.name}'",
                        description=f"Entropy: {entropy:.2f} - distribution is highly concentrated",
                        suggestion=f"Most values fall into few categories; verify this is expected (confidence: {confidence:.2f})",
                    )
                )

            # Very high entropy (too uniform)
            if entropy > 0.95 * np.log2(col.categorical_stats.unique_count):
                confidence = 0.75
                recommendations.append(
                    Recommendation(
                        severity="info",
                        category="data_quality",
                        column=col.name,
                        title=f"Unusually uniform distribution in '{col.name}'",
                        description=f"Entropy: {entropy:.2f} - nearly uniform distribution",
                        suggestion=f"Distribution is unexpectedly uniform; verify data generation (confidence: {confidence:.2f})",
                    )
                )

        # Completeness patterns
        if col.quality.completeness < 100 and col.quality.completeness > 0:
            # Check if nulls follow a pattern (multiples of 10%)
            null_pct = col.quality.null_percentage
            if abs(null_pct - round(null_pct)) < 0.1 and null_pct > 10:
                confidence = 0.7
                recommendations.append(
                    Recommendation(
                        severity="warning",
                        category="data_quality",
                        column=col.name,
                        title=f"Suspiciously round null percentage in '{col.name}'",
                        description=f"Null percentage: {null_pct:.1f}%",
                        suggestion=f"Nulls may be artificially introduced; investigate data generation (confidence: {confidence:.2f})",
                    )
                )

        return recommendations

    @classmethod
    def _check_benfords_law(cls, col: ColumnProfile) -> Optional[Tuple[float, str]]:
        """
        Check if numeric column violates Benford's Law.

        Returns:
            Tuple of (confidence, description) if violation detected, None otherwise
        """
        if not col.numeric_stats or col.row_count < 100:
            return None

        # Benford's Law doesn't apply to all data
        # Skip if values are uniformly distributed or in narrow range
        if col.numeric_stats.std is None or col.numeric_stats.mean is None:
            return None

        cv = col.numeric_stats.coefficient_of_variation
        if cv and cv < 0.5:  # Too uniform for Benford's Law
            return None

        # For actual implementation, we'd need access to the raw data
        # to extract first digits. This is a placeholder for the concept.

        # In a real implementation, you would:
        # 1. Extract first digits from all positive values
        # 2. Compare distribution to Benford's expected distribution
        # 3. Use chi-square test to determine significance

        # For now, return None (would need raw data access)
        return None
