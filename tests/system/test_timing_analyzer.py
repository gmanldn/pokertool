"""
Tests for the Timing Tell Analyzer module.
"""

import unittest
import time
from src.pokertool.timing_analyzer import (
    TimingTellAnalyzer,
    TimingData,
    TimingPattern,
    MicrosecondPrecisionTracker,
    ActionSequenceTimer,
    TimingDeviationDetector,
    PatternClusterer,
    ConfidenceIntervalCalculator,
    analyze_timing_patterns,
    detect_timing_tell
)


class TestMicrosecondPrecisionTracker(unittest.TestCase):
    """Test microsecond precision tracking."""
    
    def setUp(self):
        self.tracker = MicrosecondPrecisionTracker()
        
    def test_start_and_record_action(self):
        """Test starting timer and recording action."""
        self.tracker.start_action_timer('player1')
        time.sleep(0.1)  # Simulate decision time
        
        timing_data = self.tracker.record_action(
            'player1', 'raise 100', 'flop', 200, 1000, 'raise'
        )
        
        self.assertIsNotNone(timing_data)
        self.assertEqual(timing_data.player_id, 'player1')
        self.assertGreater(timing_data.decision_time, 0.09)
        self.assertLess(timing_data.decision_time, 0.15)
        
    def test_record_without_start(self):
        """Test recording without starting timer."""
        timing_data = self.tracker.record_action(
            'player1', 'call', 'river', 500, 800, 'call'
        )
        
        self.assertIsNone(timing_data)
        
    def test_get_player_timings(self):
        """Test retrieving player-specific timings."""
        # Record multiple actions
        for i in range(3):
            self.tracker.start_action_timer('player1')
            time.sleep(0.05)
            self.tracker.record_action('player1', f'action{i}', 'flop', 100, 1000, 'call')
            
        timings = self.tracker.get_player_timings('player1')
        self.assertEqual(len(timings), 3)
        
    def test_get_action_type_timings(self):
        """Test retrieving action-type specific timings."""
        self.tracker.start_action_timer('player1')
        time.sleep(0.05)
        self.tracker.record_action('player1', 'raise', 'flop', 100, 1000, 'raise')
        
        self.tracker.start_action_timer('player2')
        time.sleep(0.05)
        self.tracker.record_action('player2', 'call', 'flop', 100, 1000, 'call')
        
        raise_timings = self.tracker.get_action_type_timings('raise')
        self.assertEqual(len(raise_timings), 1)
        self.assertEqual(raise_timings[0].action_type, 'raise')


class TestActionSequenceTimer(unittest.TestCase):
    """Test action sequence timing."""
    
    def setUp(self):
        self.timer = ActionSequenceTimer()
        
    def test_add_to_sequence(self):
        """Test adding timing data to sequence."""
        timing_data = TimingData(
            'player1', 'raise', 1.5, time.time(), 'flop', 100, 1000, 'raise'
        )
        
        self.timer.add_to_sequence('hand1', timing_data)
        self.assertEqual(len(self.timer.sequences['hand1']), 1)
        
    def test_get_sequence_pattern(self):
        """Test sequence pattern analysis."""
        times = [1.0, 2.0, 1.5, 3.0]
        for i, t in enumerate(times):
            timing_data = TimingData(
                'player1', f'action{i}', t, time.time(), 'flop', 100, 1000, 'call'
            )
            self.timer.add_to_sequence('hand1', timing_data)
            
        pattern = self.timer.get_sequence_pattern('hand1')
        
        self.assertEqual(pattern['action_count'], 4)
        self.assertAlmostEqual(pattern['total_time'], 7.5)
        self.assertAlmostEqual(pattern['mean_time'], 1.875)
        self.assertEqual(pattern['min_time'], 1.0)
        self.assertEqual(pattern['max_time'], 3.0)
        
    def test_detect_speed_changes(self):
        """Test detecting speed changes in sequence."""
        times = [1.0, 5.0, 1.0, 1.0]  # Slowdown at position 1
        for i, t in enumerate(times):
            timing_data = TimingData(
                'player1', f'action{i}', t, time.time(), 'flop', 100, 1000, 'call'
            )
            self.timer.add_to_sequence('hand1', timing_data)
            
        changes = self.timer.detect_speed_changes('hand1')
        
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]['type'], 'slowdown')
        self.assertEqual(changes[0]['position'], 1)


class TestTimingDeviationDetector(unittest.TestCase):
    """Test timing deviation detection."""
    
    def setUp(self):
        self.detector = TimingDeviationDetector()
        
    def test_establish_baseline(self):
        """Test establishing baseline."""
        timings = [
            TimingData('player1', 'call', 2.0, time.time(), 'flop', 100, 1000, 'call'),
            TimingData('player1', 'call', 2.5, time.time(), 'flop', 100, 1000, 'call'),
            TimingData('player1', 'call', 1.5, time.time(), 'flop', 100, 1000, 'call'),
        ]
        
        self.detector.establish_baseline('player1', timings)
        
        self.assertIn('player1', self.detector.baselines)
        self.assertIn('call', self.detector.baselines['player1'])
        self.assertAlmostEqual(self.detector.baselines['player1']['call']['mean'], 2.0)
        
    def test_detect_deviation(self):
        """Test deviation detection."""
        timings = [
            TimingData('player1', 'raise', 2.0, time.time(), 'flop', 100, 1000, 'raise'),
            TimingData('player1', 'raise', 2.2, time.time(), 'flop', 100, 1000, 'raise'),
            TimingData('player1', 'raise', 1.8, time.time(), 'flop', 100, 1000, 'raise'),
        ]
        
        self.detector.establish_baseline('player1', timings)
        
        # Normal timing
        deviation = self.detector.detect_deviation('player1', 'raise', 2.1)
        self.assertIsNotNone(deviation)
        self.assertFalse(deviation['is_deviation'])
        
        # Significant deviation
        deviation = self.detector.detect_deviation('player1', 'raise', 5.0)
        self.assertIsNotNone(deviation)
        self.assertTrue(deviation['is_deviation'])
        self.assertEqual(deviation['deviation_type'], 'slower')


class TestPatternClusterer(unittest.TestCase):
    """Test pattern clustering."""
    
    def setUp(self):
        self.clusterer = PatternClusterer()
        
    def test_cluster_timings(self):
        """Test clustering timing data."""
        timings = [
            TimingData('player1', 'call', 1.0, time.time(), 'flop', 100, 1000, 'call'),
            TimingData('player1', 'call', 1.2, time.time(), 'flop', 100, 1000, 'call'),
            TimingData('player1', 'raise', 5.0, time.time(), 'turn', 100, 1000, 'raise'),
            TimingData('player1', 'raise', 5.5, time.time(), 'turn', 100, 1000, 'raise'),
        ]
        
        clusters = self.clusterer.cluster_timings('player1', timings)
        
        self.assertEqual(len(clusters), 2)  # call_flop and raise_turn
        
    def test_identify_patterns(self):
        """Test pattern identification."""
        timings = [
            TimingData('player1', 'call', 1.0, time.time(), 'flop', 100, 1000, 'call'),
            TimingData('player1', 'call', 1.1, time.time(), 'flop', 100, 1000, 'call'),
            TimingData('player1', 'call', 0.9, time.time(), 'flop', 100, 1000, 'call'),
        ]
        
        self.clusterer.cluster_timings('player1', timings)
        patterns = self.clusterer.identify_patterns('player1')
        
        self.assertGreater(len(patterns), 0)
        # Should detect fast and consistent timing
        pattern_types = [p.pattern_type for p in patterns]
        self.assertIn('fast_decision', pattern_types)


class TestConfidenceIntervalCalculator(unittest.TestCase):
    """Test confidence interval calculations."""
    
    def setUp(self):
        self.calculator = ConfidenceIntervalCalculator()
        
    def test_calculate_interval(self):
        """Test confidence interval calculation."""
        interval = self.calculator.calculate_interval(
            mean=2.0,
            std_dev=0.5,
            sample_size=30,
            confidence_level=0.95
        )
        
        self.assertEqual(len(interval), 2)
        self.assertLess(interval[0], 2.0)
        self.assertGreater(interval[1], 2.0)
        
    def test_calculate_pattern_confidence(self):
        """Test pattern confidence calculation."""
        pattern = TimingPattern(
            pattern_type='fast_decision',
            confidence=0.8,
            mean_time=1.5,
            std_dev=0.3,
            sample_size=25,
            correlation=0.85,
            description='Fast calls'
        )
        
        confidence = self.calculator.calculate_pattern_confidence(pattern)
        
        self.assertGreater(confidence, 0)
        self.assertLessEqual(confidence, 1)


class TestTimingTellAnalyzer(unittest.TestCase):
    """Test main timing tell analyzer."""
    
    def setUp(self):
        self.analyzer = TimingTellAnalyzer()
        
    def test_full_workflow(self):
        """Test complete analysis workflow."""
        # Record multiple actions
        for i in range(5):
            self.analyzer.start_action('player1')
            time.sleep(0.05)
            self.analyzer.record_action(
                'player1', f'call{i}', 'flop', 100, 1000, 'call', f'hand{i}'
            )
            
        # Analyze player
        analysis = self.analyzer.analyze_player('player1')
        
        self.assertIn('player_id', analysis)
        self.assertEqual(analysis['player_id'], 'player1')
        self.assertEqual(analysis['total_actions'], 5)
        self.assertIn('patterns', analysis)
        
    def test_detect_live_deviation(self):
        """Test live deviation detection."""
        # Establish baseline
        for i in range(10):
            self.analyzer.start_action('player1')
            time.sleep(0.05)
            self.analyzer.record_action('player1', 'call', 'flop', 100, 1000, 'call')
            
        # Analyze to establish baseline
        self.analyzer.analyze_player('player1')
        
        # Test deviation
        deviation = self.analyzer.detect_live_deviation('player1', 'call', 0.5)
        
        self.assertIsNotNone(deviation)
        
    def test_hand_sequence_analysis(self):
        """Test hand sequence analysis."""
        # Record sequence
        for i in range(3):
            self.analyzer.start_action(f'player{i}')
            time.sleep(0.05)
            self.analyzer.record_action(
                f'player{i}', f'action{i}', 'flop', 100, 1000, 'call', 'hand1'
            )
            
        analysis = self.analyzer.get_hand_sequence_analysis('hand1')
        
        self.assertIn('sequence_pattern', analysis)
        self.assertIn('speed_changes', analysis)
        
    def test_export_import(self):
        """Test data export and import."""
        # Record some data
        self.analyzer.start_action('player1')
        time.sleep(0.05)
        self.analyzer.record_action('player1', 'call', 'flop', 100, 1000, 'call')
        
        # Export
        data = self.analyzer.export_data()
        
        self.assertIn('timing_data', data)
        self.assertIn('baselines', data)
        
        # Import to new analyzer
        new_analyzer = TimingTellAnalyzer()
        new_analyzer.import_data(data)
        
        self.assertEqual(
            len(new_analyzer.deviation_detector.baselines),
            len(self.analyzer.deviation_detector.baselines)
        )


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""
    
    def test_analyze_timing_patterns(self):
        """Test quick pattern analysis utility."""
        timings = [
            TimingData('player1', 'call', 1.0, time.time(), 'flop', 100, 1000, 'call'),
            TimingData('player1', 'call', 1.1, time.time(), 'flop', 100, 1000, 'call'),
            TimingData('player1', 'call', 0.9, time.time(), 'flop', 100, 1000, 'call'),
        ]
        
        patterns = analyze_timing_patterns(timings)
        
        self.assertIsInstance(patterns, list)
        
    def test_detect_timing_tell(self):
        """Test quick timing tell detection."""
        result = detect_timing_tell(
            baseline_mean=2.0,
            baseline_std=0.5,
            decision_time=5.0
        )
        
        self.assertIn('is_tell', result)
        self.assertTrue(result['is_tell'])
        self.assertEqual(result['deviation_type'], 'slower')


class TestTimingDataSerializat ion(unittest.TestCase):
    """Test data serialization."""
    
    def test_timing_data_to_dict(self):
        """Test TimingData serialization."""
        timing_data = TimingData(
            'player1', 'raise', 2.5, time.time(), 'flop', 100, 1000, 'raise'
        )
        
        data_dict = timing_data.to_dict()
        
        self.assertEqual(data_dict['player_id'], 'player1')
        self.assertEqual(data_dict['action'], 'raise')
        self.assertEqual(data_dict['decision_time'], 2.5)
        
    def test_timing_pattern_to_dict(self):
        """Test TimingPattern serialization."""
        pattern = TimingPattern(
            'fast_decision', 0.85, 1.2, 0.3, 20, 0.8, 'Fast calls on flop'
        )
        
        pattern_dict = pattern.to_dict()
        
        self.assertEqual(pattern_dict['pattern_type'], 'fast_decision')
        self.assertEqual(pattern_dict['confidence'], 0.85)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
