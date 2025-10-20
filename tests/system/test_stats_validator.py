"""
Tests for the Statistical Significance Validator module.
"""

import unittest
import math
from src.pokertool.stats_validator import (
    StatisticalValidator,
    HypothesisTester,
    ConfidenceIntervalCalculator,
    SampleSizeCalculator,
    VarianceReducer,
    PValueCorrector,
    TestType,
    CorrectionMethod,
    quick_validate,
    calculate_required_sample_size
)


class TestHypothesisTester(unittest.TestCase):
    """Test hypothesis testing framework."""
    
    def setUp(self):
        self.tester = HypothesisTester(alpha=0.05)
        
    def test_t_test_significant(self):
        """Test t-test with significant difference."""
        result = self.tester.t_test(
            sample_mean=15.0,
            population_mean=10.0,
            std_dev=2.0,
            sample_size=25
        )
        
        self.assertEqual(result.test_type, TestType.T_TEST.value)
        self.assertTrue(result.is_significant)
        self.assertGreater(abs(result.statistic), 0)
        self.assertLess(result.p_value, 0.05)
        
    def test_t_test_not_significant(self):
        """Test t-test with no significant difference."""
        result = self.tester.t_test(
            sample_mean=10.1,
            population_mean=10.0,
            std_dev=2.0,
            sample_size=25
        )
        
        self.assertFalse(result.is_significant)
        self.assertGreater(result.p_value, 0.05)
        
    def test_t_test_insufficient_data(self):
        """Test t-test with insufficient data."""
        result = self.tester.t_test(
            sample_mean=10.0,
            population_mean=10.0,
            std_dev=0,
            sample_size=1
        )
        
        self.assertFalse(result.is_significant)
        self.assertEqual(result.p_value, 1.0)
        
    def test_z_test_significant(self):
        """Test z-test with significant difference."""
        result = self.tester.z_test(
            sample_mean=15.0,
            population_mean=10.0,
            std_dev=3.0,
            sample_size=100
        )
        
        self.assertEqual(result.test_type, TestType.Z_TEST.value)
        self.assertTrue(result.is_significant)
        self.assertLess(result.p_value, 0.05)
        
    def test_z_test_insufficient_sample(self):
        """Test z-test with insufficient sample size."""
        result = self.tester.z_test(
            sample_mean=15.0,
            population_mean=10.0,
            std_dev=3.0,
            sample_size=20
        )
        
        self.assertFalse(result.is_significant)
        self.assertEqual(result.p_value, 1.0)
        
    def test_proportion_test(self):
        """Test proportion test."""
        result = self.tester.proportion_test(
            successes=60,
            trials=100,
            expected_proportion=0.5
        )
        
        self.assertEqual(result.test_type, TestType.PROPORTION_TEST.value)
        self.assertTrue(result.is_significant)
        self.assertLess(result.p_value, 0.05)
        
    def test_proportion_test_not_significant(self):
        """Test proportion test with no significant difference."""
        result = self.tester.proportion_test(
            successes=51,
            trials=100,
            expected_proportion=0.5
        )
        
        self.assertFalse(result.is_significant)
        
    def test_chi_square_test(self):
        """Test chi-square goodness of fit."""
        observed = [25, 30, 25, 20]
        expected = [25.0, 25.0, 25.0, 25.0]
        
        result = self.tester.chi_square_test(observed, expected)
        
        self.assertEqual(result.test_type, TestType.CHI_SQUARE.value)
        self.assertGreater(result.statistic, 0)
        
    def test_chi_square_test_invalid_data(self):
        """Test chi-square with invalid data."""
        result = self.tester.chi_square_test([], [])
        
        self.assertFalse(result.is_significant)
        self.assertEqual(result.p_value, 1.0)


class TestConfidenceIntervalCalculator(unittest.TestCase):
    """Test confidence interval calculations."""
    
    def setUp(self):
        self.calculator = ConfidenceIntervalCalculator()
        
    def test_mean_confidence_interval(self):
        """Test confidence interval for mean."""
        ci = self.calculator.mean_confidence_interval(
            mean=10.0,
            std_dev=2.0,
            sample_size=30,
            confidence_level=0.95
        )
        
        self.assertLess(ci.lower_bound, 10.0)
        self.assertGreater(ci.upper_bound, 10.0)
        self.assertEqual(ci.confidence_level, 0.95)
        self.assertGreater(ci.margin_of_error, 0)
        
    def test_mean_ci_small_sample(self):
        """Test confidence interval with small sample."""
        ci = self.calculator.mean_confidence_interval(
            mean=10.0,
            std_dev=2.0,
            sample_size=1,
            confidence_level=0.95
        )
        
        self.assertEqual(ci.lower_bound, 10.0)
        self.assertEqual(ci.upper_bound, 10.0)
        
    def test_proportion_confidence_interval(self):
        """Test confidence interval for proportion."""
        ci = self.calculator.proportion_confidence_interval(
            successes=60,
            trials=100,
            confidence_level=0.95
        )
        
        self.assertLess(ci.lower_bound, 0.6)
        self.assertGreater(ci.upper_bound, 0.6)
        self.assertGreaterEqual(ci.lower_bound, 0)
        self.assertLessEqual(ci.upper_bound, 1)
        
    def test_proportion_ci_edge_cases(self):
        """Test proportion CI with edge cases."""
        # Zero successes
        ci = self.calculator.proportion_confidence_interval(0, 100, 0.95)
        self.assertGreaterEqual(ci.lower_bound, 0)
        
        # All successes
        ci = self.calculator.proportion_confidence_interval(100, 100, 0.95)
        self.assertLessEqual(ci.upper_bound, 1)
        
        # Zero trials
        ci = self.calculator.proportion_confidence_interval(0, 0, 0.95)
        self.assertEqual(ci.mean, 0)


class TestSampleSizeCalculator(unittest.TestCase):
    """Test sample size calculations."""
    
    def setUp(self):
        self.calculator = SampleSizeCalculator()
        
    def test_required_sample_size_mean(self):
        """Test sample size calculation for mean."""
        rec = self.calculator.required_sample_size_mean(
            effect_size=0.5,
            std_dev=2.0,
            confidence_level=0.95,
            power=0.80
        )
        
        self.assertGreater(rec.recommended_size, 0)
        self.assertEqual(rec.confidence_level, 0.95)
        self.assertEqual(rec.power, 0.80)
        
    def test_required_sample_size_proportion(self):
        """Test sample size calculation for proportion."""
        rec = self.calculator.required_sample_size_proportion(
            expected_proportion=0.5,
            margin_of_error=0.05,
            confidence_level=0.95
        )
        
        self.assertGreater(rec.recommended_size, 0)
        self.assertEqual(rec.margin_of_error, 0.05)
        
    def test_sample_size_large_effect(self):
        """Test that larger effects require smaller samples."""
        rec_small = self.calculator.required_sample_size_mean(
            effect_size=0.2,
            std_dev=1.0,
            confidence_level=0.95,
            power=0.80
        )
        
        rec_large = self.calculator.required_sample_size_mean(
            effect_size=0.8,
            std_dev=1.0,
            confidence_level=0.95,
            power=0.80
        )
        
        self.assertGreater(rec_small.recommended_size, rec_large.recommended_size)


class TestVarianceReducer(unittest.TestCase):
    """Test variance reduction techniques."""
    
    def setUp(self):
        self.reducer = VarianceReducer()
        
    def test_stratified_sample_variance(self):
        """Test stratified sample variance calculation."""
        variance = self.reducer.stratified_sample_variance(
            strata_sizes=[50, 30, 20],
            strata_variances=[1.0, 2.0, 1.5]
        )
        
        self.assertGreater(variance, 0)
        self.assertLess(variance, 2.0)  # Should be weighted average
        
    def test_stratified_zero_size(self):
        """Test stratified variance with zero total size."""
        variance = self.reducer.stratified_sample_variance(
            strata_sizes=[],
            strata_variances=[]
        )
        
        self.assertEqual(variance, 0)
        
    def test_control_variate_adjustment(self):
        """Test control variate method."""
        estimates = [10.0, 12.0, 11.0, 13.0, 10.5]
        controls = [9.0, 11.0, 10.0, 12.0, 9.5]
        
        adj_mean, adj_var = self.reducer.control_variate_adjustment(
            estimates, controls, control_mean=10.0
        )
        
        self.assertGreater(adj_mean, 0)
        self.assertGreaterEqual(adj_var, 0)
        
    def test_control_variate_empty(self):
        """Test control variate with empty data."""
        adj_mean, adj_var = self.reducer.control_variate_adjustment(
            [], [], control_mean=10.0
        )
        
        self.assertEqual(adj_mean, 0)
        self.assertEqual(adj_var, 0)


class TestPValueCorrector(unittest.TestCase):
    """Test p-value correction methods."""
    
    def setUp(self):
        self.corrector = PValueCorrector()
        
    def test_bonferroni_correction(self):
        """Test Bonferroni correction."""
        p_values = [0.01, 0.02, 0.03, 0.04]
        corrected = self.corrector.bonferroni_correction(p_values)
        
        self.assertEqual(len(corrected), len(p_values))
        # Corrected p-values should be larger
        for orig, corr in zip(p_values, corrected):
            self.assertGreaterEqual(corr, orig)
            
    def test_holm_correction(self):
        """Test Holm-Bonferroni correction."""
        p_values = [0.001, 0.01, 0.03, 0.05]
        corrected = self.corrector.holm_correction(p_values)
        
        self.assertEqual(len(corrected), len(p_values))
        # All p-values should be <= 1.0
        for corr in corrected:
            self.assertLessEqual(corr, 1.0)
            
    def test_benjamini_hochberg_correction(self):
        """Test Benjamini-Hochberg FDR correction."""
        p_values = [0.001, 0.01, 0.03, 0.05, 0.1]
        results = self.corrector.benjamini_hochberg_correction(p_values, fdr=0.05)
        
        self.assertEqual(len(results), len(p_values))
        # Check format: list of tuples (adjusted_p, is_significant)
        for adj_p, is_sig in results:
            self.assertLessEqual(adj_p, 1.0)
            self.assertIsInstance(is_sig, bool)


class TestStatisticalValidator(unittest.TestCase):
    """Test main statistical validator."""
    
    def setUp(self):
        self.validator = StatisticalValidator(alpha=0.05)
        
    def test_validate_pattern_reliable(self):
        """Test pattern validation with reliable data."""
        result = self.validator.validate_pattern(
            observed_mean=15.0,
            expected_mean=10.0,
            std_dev=2.0,
            sample_size=100
        )
        
        self.assertIn('test_result', result)
        self.assertIn('confidence_interval', result)
        self.assertIn('sample_recommendation', result)
        self.assertIn('is_reliable', result)
        
        self.assertTrue(result['test_result']['is_significant'])
        
    def test_validate_pattern_unreliable(self):
        """Test pattern validation with unreliable data."""
        result = self.validator.validate_pattern(
            observed_mean=10.1,
            expected_mean=10.0,
            std_dev=5.0,
            sample_size=10
        )
        
        self.assertFalse(result['is_reliable'])
        
    def test_validate_frequency_reliable(self):
        """Test frequency validation."""
        result = self.validator.validate_frequency(
            observed_count=65,
            total_trials=100,
            expected_proportion=0.5
        )
        
        self.assertIn('test_result', result)
        self.assertIn('confidence_interval', result)
        self.assertTrue(result['test_result']['is_significant'])
        
    def test_validate_frequency_unreliable(self):
        """Test frequency validation with small sample."""
        result = self.validator.validate_frequency(
            observed_count=6,
            total_trials=10,
            expected_proportion=0.5
        )
        
        # Small sample, likely unreliable
        self.assertIn('is_reliable', result)
        
    def test_correct_multiple_tests_bonferroni(self):
        """Test multiple testing correction with Bonferroni."""
        p_values = [0.01, 0.02, 0.03]
        corrected = self.validator.correct_multiple_tests(
            p_values, method=CorrectionMethod.BONFERRONI
        )
        
        self.assertEqual(len(corrected), len(p_values))
        self.assertGreater(corrected[0], p_values[0])
        
    def test_correct_multiple_tests_holm(self):
        """Test multiple testing correction with Holm."""
        p_values = [0.01, 0.02, 0.03]
        corrected = self.validator.correct_multiple_tests(
            p_values, method=CorrectionMethod.HOLM
        )
        
        self.assertEqual(len(corrected), len(p_values))
        
    def test_correct_multiple_tests_bh(self):
        """Test multiple testing correction with Benjamini-Hochberg."""
        p_values = [0.001, 0.01, 0.03, 0.05]
        corrected = self.validator.correct_multiple_tests(
            p_values, method=CorrectionMethod.BENJAMINI_HOCHBERG
        )
        
        self.assertEqual(len(corrected), len(p_values))


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""
    
    def test_quick_validate_reliable(self):
        """Test quick validation with reliable data."""
        result = quick_validate(
            observed=15.0,
            expected=10.0,
            std_dev=2.0,
            sample_size=100
        )
        
        self.assertIsInstance(result, bool)
        self.assertTrue(result)
        
    def test_quick_validate_unreliable(self):
        """Test quick validation with unreliable data."""
        result = quick_validate(
            observed=10.1,
            expected=10.0,
            std_dev=5.0,
            sample_size=10
        )
        
        self.assertFalse(result)
        
    def test_calculate_required_sample_size(self):
        """Test quick sample size calculation."""
        size = calculate_required_sample_size(
            effect_size=0.5,
            std_dev=2.0,
            confidence_level=0.95,
            power=0.80
        )
        
        self.assertIsInstance(size, int)
        self.assertGreater(size, 0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_zero_std_dev(self):
        """Test with zero standard deviation."""
        tester = HypothesisTester()
        result = tester.t_test(10.0, 10.0, 0, 10)
        
        self.assertFalse(result.is_significant)
        
    def test_negative_values(self):
        """Test with negative values."""
        validator = StatisticalValidator()
        result = validator.validate_pattern(-5.0, -10.0, 2.0, 30)
        
        self.assertIn('test_result', result)
        
    def test_very_small_p_value(self):
        """Test with very small p-value."""
        tester = HypothesisTester()
        result = tester.z_test(20.0, 10.0, 1.0, 100)
        
        self.assertLess(result.p_value, 0.001)
        self.assertTrue(result.is_significant)
        
    def test_boundary_sample_sizes(self):
        """Test with boundary sample sizes."""
        calculator = SampleSizeCalculator()
        
        # Very small effect
        rec = calculator.required_sample_size_mean(0.01, 1.0)
        self.assertGreater(rec.recommended_size, 1000)
        
        # Large effect
        rec = calculator.required_sample_size_mean(2.0, 1.0)
        self.assertLess(rec.recommended_size, 100)


class TestStatisticalProperties(unittest.TestCase):
    """Test statistical properties of the methods."""
    
    def test_confidence_interval_coverage(self):
        """Test that CI has proper coverage."""
        calculator = ConfidenceIntervalCalculator()
        ci = calculator.mean_confidence_interval(10.0, 2.0, 30, 0.95)
        
        # Width should be reasonable
        width = ci.upper_bound - ci.lower_bound
        self.assertGreater(width, 0)
        self.assertLess(width, 5.0)
        
    def test_power_analysis(self):
        """Test power analysis properties."""
        calculator = SampleSizeCalculator()
        
        # Higher power should require larger sample
        rec_80 = calculator.required_sample_size_mean(0.5, 2.0, power=0.80)
        rec_90 = calculator.required_sample_size_mean(0.5, 2.0, power=0.90)
        
        self.assertGreater(rec_90.recommended_size, rec_80.recommended_size)
        
    def test_effect_size_relationship(self):
        """Test relationship between effect size and p-value."""
        tester = HypothesisTester()
        
        # Larger effect should have smaller p-value
        result_small = tester.z_test(10.5, 10.0, 2.0, 100)
        result_large = tester.z_test(15.0, 10.0, 2.0, 100)
        
        self.assertLess(result_large.p_value, result_small.p_value)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
