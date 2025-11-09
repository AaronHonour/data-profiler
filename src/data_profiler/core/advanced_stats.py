"""Advanced statistical analysis."""

from typing import Optional, Tuple

import numpy as np
from scipy import stats  # type: ignore

from data_profiler.models.profile import DistributionFit, StatisticalTests


class AdvancedStatistics:
    """Advanced statistical analysis for numeric data."""

    @staticmethod
    def test_normality(data: np.ndarray) -> StatisticalTests:
        """
        Test for normality using multiple methods.

        Args:
            data: Numpy array of numeric values

        Returns:
            StatisticalTests with normality test results
        """
        tests = {}

        # Shapiro-Wilk test (best for n < 5000)
        if len(data) <= 5000:
            try:
                statistic, p_value = stats.shapiro(data)
                tests["shapiro_wilk"] = {
                    "statistic": float(statistic),
                    "p_value": float(p_value),
                    "is_normal": p_value > 0.05,
                }
            except Exception:
                pass

        # Anderson-Darling test
        try:
            result = stats.anderson(data, dist="norm")
            tests["anderson_darling"] = {
                "statistic": float(result.statistic),
                "critical_values": result.critical_values.tolist(),
                "significance_levels": result.significance_level.tolist(),
            }
        except Exception:
            pass

        # Kolmogorov-Smirnov test
        try:
            statistic, p_value = stats.kstest(data, "norm", args=(data.mean(), data.std()))
            tests["kolmogorov_smirnov"] = {
                "statistic": float(statistic),
                "p_value": float(p_value),
                "is_normal": p_value > 0.05,
            }
        except Exception:
            pass

        return StatisticalTests(tests=tests)

    @staticmethod
    def fit_distributions(
        data: np.ndarray, distributions: Optional[list] = None
    ) -> list[DistributionFit]:
        """
        Fit multiple distributions and rank by goodness of fit.

        Args:
            data: Numpy array of numeric values
            distributions: List of distribution names to fit

        Returns:
            List of DistributionFit objects ranked by fit quality
        """
        if distributions is None:
            distributions = ["norm", "lognorm", "expon", "gamma", "beta"]

        fits = []

        for dist_name in distributions:
            try:
                dist = getattr(stats, dist_name)

                # Fit distribution
                params = dist.fit(data)

                # Calculate goodness of fit using Kolmogorov-Smirnov test
                ks_statistic, p_value = stats.kstest(data, dist_name, args=params)

                # Calculate AIC (Akaike Information Criterion)
                log_likelihood = np.sum(dist.logpdf(data, *params))
                k = len(params)
                aic = 2 * k - 2 * log_likelihood

                fits.append(
                    DistributionFit(
                        distribution=dist_name,
                        parameters={f"param_{i}": float(p) for i, p in enumerate(params)},
                        ks_statistic=float(ks_statistic),
                        p_value=float(p_value),
                        aic=float(aic),
                    )
                )
            except Exception:
                continue

        # Sort by AIC (lower is better)
        fits.sort(key=lambda x: x.aic)

        return fits[:3]  # Return top 3 fits

    @staticmethod
    def detect_bimodality(data: np.ndarray) -> Tuple[bool, float]:
        """
        Detect if data is bimodal using coefficient of bimodality.

        Args:
            data: Numpy array of numeric values

        Returns:
            Tuple of (is_bimodal, coefficient)
        """
        if len(data) < 4:
            return False, 0.0

        # Calculate skewness and kurtosis
        skew = stats.skew(data)
        kurt = stats.kurtosis(data, fisher=False)  # Pearson's kurtosis

        # Coefficient of bimodality
        n = len(data)
        coefficient = (skew**2 + 1) / kurt

        # Threshold for bimodality (5/9 ≈ 0.555)
        is_bimodal = coefficient > 0.555

        return is_bimodal, float(coefficient)

    @staticmethod
    def analyze_variance_stability(data: np.ndarray, window_size: int = 100) -> dict:
        """
        Analyze if variance is stable across the dataset.

        Args:
            data: Numpy array of numeric values
            window_size: Size of rolling window

        Returns:
            Dictionary with variance stability metrics
        """
        if len(data) < window_size * 2:
            return {"stable": True, "coefficient_of_variation": 0.0}

        # Calculate rolling variance
        num_windows = len(data) // window_size
        variances = []

        for i in range(num_windows):
            window = data[i * window_size : (i + 1) * window_size]
            variances.append(np.var(window))

        variances = np.array(variances)

        # Coefficient of variation of variances
        cv = np.std(variances) / np.mean(variances) if np.mean(variances) > 0 else 0

        # Variance is stable if CV < 0.3
        is_stable = cv < 0.3

        return {
            "stable": bool(is_stable),
            "coefficient_of_variation": float(cv),
            "variance_range": [float(np.min(variances)), float(np.max(variances))],
        }
