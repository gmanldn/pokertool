"""
Statistical Significance Validator - Statistical validation of patterns and reads.

This module implements hypothesis testing framework, confidence interval calculation,
sample size recommendations, variance reduction techniques, and p-value corrections.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum


class TestType(Enum):
    """Types of statistical tests."""
    T_TEST = "t_test"
    Z_TEST = "z_test"
    CHI_SQUARE = "chi_square"
    PROPORTION_TEST = "proportion_test"
    BINOMIAL_TEST = "binomial_test"


class CorrectionMethod(Enum):
    """P-value correction methods."""
    BONFERRONI = "bonferroni"
    HOLM = "holm"
    BENJAMINI_HOCHBERG = "benjamini_hochberg"
    NONE = "none"


@dataclass
class HypothesisTestResult:
    """Result of a hypothesis test."""
    test_type: str
    statistic: float
    p_value: float
    is_significant: bool
    confidence_level: float
    effect_size: float
    sample_size: int
    description: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'test_type': self.test_type,
            'statistic': self.statistic,
            'p_value': self.p_value,
            'is_significant': self.is_significant,
            'confidence_level': self.confidence_level,
            'effect_size': self.effect_size,
            'sample_size': self.sample_size,
            'description': self.description
        }


@dataclass
class ConfidenceInterval:
    """Confidence interval result."""
    lower_bound: float
    upper_bound: float
    confidence_level: float
    mean: float
    margin_of_error: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'lower_bound': self.lower_bound,
            'upper_bound': self.upper_bound,
            'confidence_level': self.confidence_level,
            'mean': self.mean,
            'margin_of_error': self.margin_of_error
        }


@dataclass
class SampleSizeRecommendation:
    """Sample size recommendation."""
    recommended_size: int
    current_size: int
    confidence_level: float
    margin_of_error: float
    effect_size: float
    power: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'recommended_size': self.recommended_size,
            'current_size': self.current_size,
            'confidence_level': self.confidence_level,
            'margin_of_error': self.margin_of_error,
            'effect_size': self.effect_size,
            'power': self.power
        }


class HypothesisTester:
    """Framework for hypothesis testing."""
    
    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha
        
    def t_test(
        self,
        sample_mean: float,
        population_mean: float,
        std_dev: float,
        sample_size: int
    ) -> HypothesisTestResult:
        """Perform one-sample t-test."""
        if sample_size < 2 or std_dev == 0:
            return HypothesisTestResult(
                test_type=TestType.T_TEST.value,
                statistic=0,
                p_value=1.0,
                is_significant=False,
                confidence_level=1 - self.alpha,
                effect_size=0,
                sample_size=sample_size,
                description="Insufficient data for t-test"
            )
            
        # Calculate t-statistic
        se = std_dev / math.sqrt(sample_size)
        t_stat = (sample_mean - population_mean) / se
        
        # Degrees of freedom
        df = sample_size - 1
        
        # Approximate p-value using t-distribution approximation
        p_value = self._t_distribution_p_value(abs(t_stat), df)
        
        # Effect size (Cohen's d)
        effect_size = abs(sample_mean - population_mean) / std_dev
        
        return HypothesisTestResult(
            test_type=TestType.T_TEST.value,
            statistic=t_stat,
            p_value=p_value,
            is_significant=p_value < self.alpha,
            confidence_level=1 - self.alpha,
            effect_size=effect_size,
            sample_size=sample_size,
            description=f"t-test comparing sample mean ({sample_mean:.4f}) to population ({population_mean:.4f})"
        )
        
    def z_test(
        self,
        sample_mean: float,
        population_mean: float,
        std_dev: float,
        sample_size: int
    ) -> HypothesisTestResult:
        """Perform z-test (for large samples)."""
        if sample_size < 30 or std_dev == 0:
            return HypothesisTestResult(
                test_type=TestType.Z_TEST.value,
                statistic=0,
                p_value=1.0,
                is_significant=False,
                confidence_level=1 - self.alpha,
                effect_size=0,
                sample_size=sample_size,
                description="Insufficient sample size for z-test (need n >= 30)"
            )
            
        # Calculate z-statistic
        se = std_dev / math.sqrt(sample_size)
        z_stat = (sample_mean - population_mean) / se
        
        # Calculate p-value
        p_value = 2 * (1 - self._normal_cdf(abs(z_stat)))
        
        # Effect size
        effect_size = abs(sample_mean - population_mean) / std_dev
        
        return HypothesisTestResult(
            test_type=TestType.Z_TEST.value,
            statistic=z_stat,
            p_value=p_value,
            is_significant=p_value < self.alpha,
            confidence_level=1 - self.alpha,
            effect_size=effect_size,
            sample_size=sample_size,
            description=f"z-test comparing sample mean ({sample_mean:.4f}) to population ({population_mean:.4f})"
        )
        
    def proportion_test(
        self,
        successes: int,
        trials: int,
        expected_proportion: float
    ) -> HypothesisTestResult:
        """Test if observed proportion differs from expected."""
        if trials < 10:
            return HypothesisTestResult(
                test_type=TestType.PROPORTION_TEST.value,
                statistic=0,
                p_value=1.0,
                is_significant=False,
                confidence_level=1 - self.alpha,
                effect_size=0,
                sample_size=trials,
                description="Insufficient trials for proportion test"
            )
            
        observed_prop = successes / trials
        
        # Standard error under null hypothesis
        se = math.sqrt(expected_proportion * (1 - expected_proportion) / trials)
        
        # Z-statistic
        z_stat = (observed_prop - expected_proportion) / se
        
        # P-value
        p_value = 2 * (1 - self._normal_cdf(abs(z_stat)))
        
        # Effect size (h - Cohen's h for proportions)
        effect_size = 2 * (math.asin(math.sqrt(observed_prop)) - 
                          math.asin(math.sqrt(expected_proportion)))
        
        return HypothesisTestResult(
            test_type=TestType.PROPORTION_TEST.value,
            statistic=z_stat,
            p_value=p_value,
            is_significant=p_value < self.alpha,
            confidence_level=1 - self.alpha,
            effect_size=abs(effect_size),
            sample_size=trials,
            description=f"Proportion test: observed {observed_prop:.4f} vs expected {expected_proportion:.4f}"
        )
        
    def chi_square_test(
        self,
        observed: List[int],
        expected: List[float]
    ) -> HypothesisTestResult:
        """Chi-square goodness of fit test."""
        if len(observed) != len(expected) or len(observed) < 2:
            return HypothesisTestResult(
                test_type=TestType.CHI_SQUARE.value,
                statistic=0,
                p_value=1.0,
                is_significant=False,
                confidence_level=1 - self.alpha,
                effect_size=0,
                sample_size=sum(observed),
                description="Invalid data for chi-square test"
            )
            
        # Calculate chi-square statistic
        chi_square = sum(
            (o - e) ** 2 / e if e > 0 else 0
            for o, e in zip(observed, expected)
        )
        
        # Degrees of freedom
        df = len(observed) - 1
        
        # Approximate p-value
        p_value = self._chi_square_p_value(chi_square, df)
        
        # Effect size (Cramér's V approximation)
        n = sum(observed)
        effect_size = math.sqrt(chi_square / n) if n > 0 else 0
        
        return HypothesisTestResult(
            test_type=TestType.CHI_SQUARE.value,
            statistic=chi_square,
            p_value=p_value,
            is_significant=p_value < self.alpha,
            confidence_level=1 - self.alpha,
            effect_size=effect_size,
            sample_size=n,
            description=f"Chi-square test with {df} degrees of freedom"
        )
        
    def _normal_cdf(self, x: float) -> float:
        """Approximate normal CDF using error function approximation."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
        
    def _t_distribution_p_value(self, t_stat: float, df: int) -> float:
        """Approximate p-value for t-distribution."""
        # For large df, t-distribution approaches normal
        if df >= 30:
            return 2 * (1 - self._normal_cdf(t_stat))
            
        # Simple approximation for small df
        # This is a rough approximation
        z_equiv = t_stat * math.sqrt(df / (df + t_stat ** 2))
        return 2 * (1 - self._normal_cdf(abs(z_equiv)))
        
    def _chi_square_p_value(self, chi_square: float, df: int) -> float:
        """Approximate p-value for chi-square distribution."""
        # Simple approximation using Wilson-Hilferty transformation
        if df == 0:
            return 1.0
            
        z = ((chi_square / df) ** (1/3) - (1 - 2/(9*df))) / math.sqrt(2/(9*df))
        return 1 - self._normal_cdf(z)


class ConfidenceIntervalCalculator:
    """Calculate confidence intervals for various statistics."""
    
    def mean_confidence_interval(
        self,
        mean: float,
        std_dev: float,
        sample_size: int,
        confidence_level: float = 0.95
    ) -> ConfidenceInterval:
        """Calculate confidence interval for mean."""
        if sample_size < 2:
            return ConfidenceInterval(
                lower_bound=mean,
                upper_bound=mean,
                confidence_level=confidence_level,
                mean=mean,
                margin_of_error=0
            )
            
        # Critical value (approximate z-score for given confidence level)
        alpha = 1 - confidence_level
        z_crit = self._get_z_critical(alpha / 2)
        
        # Standard error
        se = std_dev / math.sqrt(sample_size)
        
        # Margin of error
        margin = z_crit * se
        
        return ConfidenceInterval(
            lower_bound=mean - margin,
            upper_bound=mean + margin,
            confidence_level=confidence_level,
            mean=mean,
            margin_of_error=margin
        )
        
    def proportion_confidence_interval(
        self,
        successes: int,
        trials: int,
        confidence_level: float = 0.95
    ) -> ConfidenceInterval:
        """Calculate confidence interval for proportion."""
        if trials == 0:
            return ConfidenceInterval(
                lower_bound=0,
                upper_bound=0,
                confidence_level=confidence_level,
                mean=0,
                margin_of_error=0
            )
            
        p = successes / trials
        
        # Wilson score interval (better than normal approximation)
        alpha = 1 - confidence_level
        z = self._get_z_critical(alpha / 2)
        
        denominator = 1 + z ** 2 / trials
        center = (p + z ** 2 / (2 * trials)) / denominator
        margin = z * math.sqrt(p * (1 - p) / trials + z ** 2 / (4 * trials ** 2)) / denominator
        
        return ConfidenceInterval(
            lower_bound=max(0, center - margin),
            upper_bound=min(1, center + margin),
            confidence_level=confidence_level,
            mean=p,
            margin_of_error=margin
        )
        
    def _get_z_critical(self, alpha: float) -> float:
        """Get critical z-value for given alpha."""
        # Common critical values
        if abs(alpha - 0.025) < 0.001:  # 95% CI
            return 1.96
        elif abs(alpha - 0.005) < 0.001:  # 99% CI
            return 2.576
        elif abs(alpha - 0.05) < 0.001:  # 90% CI
            return 1.645
        else:
            # Approximate using inverse normal
            return math.sqrt(2) * self._inverse_erf(1 - 2 * alpha)
            
    def _inverse_erf(self, x: float) -> float:
        """Approximate inverse error function."""
        # Simple approximation
        a = 0.147
        b = 2 / (math.pi * a) + math.log(1 - x ** 2) / 2
        return math.copysign(math.sqrt(math.sqrt(b ** 2 - math.log(1 - x ** 2) / a) - b), x)


class SampleSizeCalculator:
    """Calculate required sample sizes."""
    
    def required_sample_size_mean(
        self,
        effect_size: float,
        std_dev: float,
        confidence_level: float = 0.95,
        power: float = 0.80
    ) -> SampleSizeRecommendation:
        """Calculate required sample size for detecting effect on mean."""
        # Z-scores for alpha and beta
        alpha = 1 - confidence_level
        z_alpha = 1.96 if abs(alpha - 0.05) < 0.001 else 2.576
        z_beta = 0.84 if abs(power - 0.80) < 0.01 else 1.28
        
        # Required sample size
        n = ((z_alpha + z_beta) * std_dev / effect_size) ** 2
        
        return SampleSizeRecommendation(
            recommended_size=int(math.ceil(n)),
            current_size=0,
            confidence_level=confidence_level,
            margin_of_error=effect_size,
            effect_size=effect_size,
            power=power
        )
        
    def required_sample_size_proportion(
        self,
        expected_proportion: float,
        margin_of_error: float,
        confidence_level: float = 0.95
    ) -> SampleSizeRecommendation:
        """Calculate required sample size for proportion."""
        alpha = 1 - confidence_level
        z = 1.96 if abs(alpha - 0.05) < 0.001 else 2.576
        
        # Required sample size
        p = expected_proportion
        n = (z ** 2 * p * (1 - p)) / (margin_of_error ** 2)
        
        return SampleSizeRecommendation(
            recommended_size=int(math.ceil(n)),
            current_size=0,
            confidence_level=confidence_level,
            margin_of_error=margin_of_error,
            effect_size=margin_of_error,
            power=0.80
        )


class VarianceReducer:
    """Techniques for variance reduction."""
    
    def stratified_sample_variance(
        self,
        strata_sizes: List[int],
        strata_variances: List[float]
    ) -> float:
        """Calculate variance for stratified sampling."""
        total_size = sum(strata_sizes)
        if total_size == 0:
            return 0
            
        # Weighted variance
        variance = sum(
            (n / total_size) ** 2 * var
            for n, var in zip(strata_sizes, strata_variances)
        )
        
        return variance
        
    def control_variate_adjustment(
        self,
        estimates: List[float],
        control_values: List[float],
        control_mean: float
    ) -> Tuple[float, float]:
        """Apply control variate method for variance reduction."""
        if len(estimates) != len(control_values) or len(estimates) == 0:
            return 0, 0
            
        # Calculate covariance and variance
        est_mean = sum(estimates) / len(estimates)
        control_sample_mean = sum(control_values) / len(control_values)
        
        covariance = sum(
            (e - est_mean) * (c - control_sample_mean)
            for e, c in zip(estimates, control_values)
        ) / len(estimates)
        
        control_variance = sum(
            (c - control_sample_mean) ** 2
            for c in control_values
        ) / len(control_values)
        
        if control_variance == 0:
            return est_mean, sum((e - est_mean) ** 2 for e in estimates) / len(estimates)
            
        # Optimal coefficient
        c_opt = covariance / control_variance
        
        # Adjusted estimates
        adjusted_estimates = [
            e - c_opt * (c - control_mean)
            for e, c in zip(estimates, control_values)
        ]
        
        adjusted_mean = sum(adjusted_estimates) / len(adjusted_estimates)
        adjusted_variance = sum(
            (ae - adjusted_mean) ** 2
            for ae in adjusted_estimates
        ) / len(adjusted_estimates)
        
        return adjusted_mean, adjusted_variance


class PValueCorrector:
    """Apply multiple testing corrections to p-values."""
    
    def bonferroni_correction(self, p_values: List[float]) -> List[float]:
        """Apply Bonferroni correction."""
        n = len(p_values)
        return [min(p * n, 1.0) for p in p_values]
        
    def holm_correction(self, p_values: List[float]) -> List[float]:
        """Apply Holm-Bonferroni correction."""
        n = len(p_values)
        sorted_indices = sorted(range(n), key=lambda i: p_values[i])
        
        corrected = [0.0] * n
        for rank, idx in enumerate(sorted_indices):
            corrected[idx] = min(p_values[idx] * (n - rank), 1.0)
            
        return corrected
        
    def benjamini_hochberg_correction(
        self,
        p_values: List[float],
        fdr: float = 0.05
    ) -> List[Tuple[float, bool]]:
        """Apply Benjamini-Hochberg FDR correction."""
        n = len(p_values)
        sorted_indices = sorted(range(n), key=lambda i: p_values[i])
        
        results = [(0.0, False)] * n
        
        for rank, idx in enumerate(sorted_indices):
            adjusted_p = p_values[idx] * n / (rank + 1)
            is_significant = adjusted_p <= fdr
            results[idx] = (min(adjusted_p, 1.0), is_significant)
            
        return results


class StatisticalValidator:
    """Main class orchestrating all statistical validation."""
    
    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha
        self.hypothesis_tester = HypothesisTester(alpha)
        self.ci_calculator = ConfidenceIntervalCalculator()
        self.sample_calculator = SampleSizeCalculator()
        self.variance_reducer = VarianceReducer()
        self.p_corrector = PValueCorrector()
        
    def validate_pattern(
        self,
        observed_mean: float,
        expected_mean: float,
        std_dev: float,
        sample_size: int,
        confidence_level: float = 0.95
    ) -> Dict:
        """Comprehensive validation of a pattern."""
        # Hypothesis test
        if sample_size >= 30:
            test_result = self.hypothesis_tester.z_test(
                observed_mean, expected_mean, std_dev, sample_size
            )
        else:
            test_result = self.hypothesis_tester.t_test(
                observed_mean, expected_mean, std_dev, sample_size
            )
            
        # Confidence interval
        ci = self.ci_calculator.mean_confidence_interval(
            observed_mean, std_dev, sample_size, confidence_level
        )
        
        # Sample size recommendation
        effect_size = abs(observed_mean - expected_mean)
        sample_rec = self.sample_calculator.required_sample_size_mean(
            effect_size, std_dev, confidence_level
        )
        sample_rec.current_size = sample_size
        
        return {
            'test_result': test_result.to_dict(),
            'confidence_interval': ci.to_dict(),
            'sample_recommendation': sample_rec.to_dict(),
            'is_reliable': test_result.is_significant and sample_size >= sample_rec.recommended_size
        }
        
    def validate_frequency(
        self,
        observed_count: int,
        total_trials: int,
        expected_proportion: float,
        confidence_level: float = 0.95
    ) -> Dict:
        """Validate observed frequency against expected."""
        # Proportion test
        test_result = self.hypothesis_tester.proportion_test(
            observed_count, total_trials, expected_proportion
        )
        
        # Confidence interval for proportion
        ci = self.ci_calculator.proportion_confidence_interval(
            observed_count, total_trials, confidence_level
        )
        
        # Sample size recommendation
        margin = 0.05  # 5% margin of error
        sample_rec = self.sample_calculator.required_sample_size_proportion(
            expected_proportion, margin, confidence_level
        )
        sample_rec.current_size = total_trials
        
        return {
            'test_result': test_result.to_dict(),
            'confidence_interval': ci.to_dict(),
            'sample_recommendation': sample_rec.to_dict(),
            'is_reliable': test_result.is_significant and total_trials >= sample_rec.recommended_size
        }
        
    def correct_multiple_tests(
        self,
        p_values: List[float],
        method: CorrectionMethod = CorrectionMethod.HOLM
    ) -> List[float]:
        """Apply multiple testing correction."""
        if method == CorrectionMethod.BONFERRONI:
            return self.p_corrector.bonferroni_correction(p_values)
        elif method == CorrectionMethod.HOLM:
            return self.p_corrector.holm_correction(p_values)
        elif method == CorrectionMethod.BENJAMINI_HOCHBERG:
            results = self.p_corrector.benjamini_hochberg_correction(p_values, self.alpha)
            return [p for p, _ in results]
        else:
            return p_values


# Utility functions
def quick_validate(
    observed: float,
    expected: float,
    std_dev: float,
    sample_size: int
) -> bool:
    """Quick validation check."""
    validator = StatisticalValidator()
    result = validator.validate_pattern(observed, expected, std_dev, sample_size)
    return result['is_reliable']


def calculate_required_sample_size(
    effect_size: float,
    std_dev: float,
    confidence_level: float = 0.95,
    power: float = 0.80
) -> int:
    """Quick sample size calculation."""
    calculator = SampleSizeCalculator()
    rec = calculator.required_sample_size_mean(effect_size, std_dev, confidence_level, power)
    return rec.recommended_size
