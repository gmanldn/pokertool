"""
Tests for Real-Time Solver API

Tests caching, approximation, parallel computation, progressive refinement,
and latency optimization functionality.
"""

import unittest
import time
from src.pokertool.solver_api import (
    RealtimeSolverAPI,
    SolverQuery,
    SolverCache,
    ApproximationEngine,
    ProgressiveRefiner,
    LatencyOptimizer,
    ParallelSolverExecutor,
    create_solver_api,
    quick_query
)


class TestSolverQuery(unittest.TestCase):
    """Test SolverQuery functionality."""
    
    def test_query_creation(self):
        """Test creating a solver query."""
        query = SolverQuery(
            game_state={'position': 'BTN', 'stack': 100},
            query_type='action',
            parameters={'pot_odds': 0.33},
            max_time_ms=500
        )
        
        self.assertEqual(query.query_type, 'action')
        self.assertEqual(query.max_time_ms, 500)
        self.assertEqual(query.approximation_level, 1)
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        query1 = SolverQuery(
            game_state={'position': 'BTN'},
            query_type='action',
            parameters={'pot_odds': 0.33}
        )
        
        query2 = SolverQuery(
            game_state={'position': 'BTN'},
            query_type='action',
            parameters={'pot_odds': 0.33}
        )
        
        # Same queries should have same cache key
        self.assertEqual(query1.to_cache_key(), query2.to_cache_key())
    
    def test_different_cache_keys(self):
        """Test that different queries have different cache keys."""
        query1 = SolverQuery(
            game_state={'position': 'BTN'},
            query_type='action',
            parameters={'pot_odds': 0.33}
        )
        
        query2 = SolverQuery(
            game_state={'position': 'UTG'},
            query_type='action',
            parameters={'pot_odds': 0.33}
        )
        
        # Different queries should have different cache keys
        self.assertNotEqual(query1.to_cache_key(), query2.to_cache_key())


class TestSolverCache(unittest.TestCase):
    """Test SolverCache functionality."""
    
    def setUp(self):
        """Set up test cache."""
        self.cache = SolverCache(max_size=3, ttl_seconds=1)
    
    def test_cache_miss(self):
        """Test cache miss."""
        result = self.cache.get('nonexistent')
        self.assertIsNone(result)
        
        stats = self.cache.get_stats()
        self.assertEqual(stats['hits'], 0)
        self.assertEqual(stats['misses'], 1)
    
    def test_cache_put_and_get(self):
        """Test putting and getting from cache."""
        from src.pokertool.solver_api import SolverResult
        
        result = SolverResult(
            query_id='test123',
            result_type='action',
            data={'action': 'raise'},
            confidence=0.9,
            computation_time_ms=10.0
        )
        
        self.cache.put('key1', result)
        cached = self.cache.get('key1')
        
        self.assertIsNotNone(cached)
        self.assertEqual(cached.query_id, 'test123')
        self.assertTrue(cached.cached)
        
        stats = self.cache.get_stats()
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 0)
    
    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        from src.pokertool.solver_api import SolverResult
        
        result = SolverResult(
            query_id='test123',
            result_type='action',
            data={'action': 'raise'},
            confidence=0.9,
            computation_time_ms=10.0
        )
        
        self.cache.put('key1', result)
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        cached = self.cache.get('key1')
        self.assertIsNone(cached)
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when max size is reached."""
        from src.pokertool.solver_api import SolverResult
        
        # Add 4 items to cache with max_size=3
        for i in range(4):
            result = SolverResult(
                query_id=f'test{i}',
                result_type='action',
                data={'action': 'raise'},
                confidence=0.9,
                computation_time_ms=10.0
            )
            self.cache.put(f'key{i}', result)
        
        # First item should be evicted
        self.assertIsNone(self.cache.get('key0'))
        
        # Last 3 items should still be there
        self.assertIsNotNone(self.cache.get('key1'))
        self.assertIsNotNone(self.cache.get('key2'))
        self.assertIsNotNone(self.cache.get('key3'))
    
    def test_cache_clear(self):
        """Test clearing the cache."""
        from src.pokertool.solver_api import SolverResult
        
        result = SolverResult(
            query_id='test123',
            result_type='action',
            data={'action': 'raise'},
            confidence=0.9,
            computation_time_ms=10.0
        )
        
        self.cache.put('key1', result)
        self.cache.clear()
        
        self.assertIsNone(self.cache.get('key1'))
        stats = self.cache.get_stats()
        self.assertEqual(stats['size'], 0)


class TestApproximationEngine(unittest.TestCase):
    """Test ApproximationEngine functionality."""
    
    def setUp(self):
        """Set up test engine."""
        self.engine = ApproximationEngine()
    
    def test_approximate_range(self):
        """Test range approximation."""
        query = SolverQuery(
            game_state={'position': 'BTN'},
            query_type='range',
            parameters={'action': 'raise'},
            approximation_level=2
        )
        
        result = self.engine.approximate_range(query)
        
        self.assertIn('range', result)
        self.assertIn('confidence', result)
        self.assertGreater(result['confidence'], 0)
    
    def test_approximate_action(self):
        """Test action approximation."""
        query = SolverQuery(
            game_state={'position': 'BTN'},
            query_type='action',
            parameters={'pot_odds': 0.33, 'equity': 0.60},
            approximation_level=2
        )
        
        result = self.engine.approximate_action(query)
        
        self.assertIn('action', result)
        self.assertIn('ev', result)
        self.assertIn(result['action'], ['raise', 'call', 'fold'])
    
    def test_approximate_equity(self):
        """Test equity approximation."""
        query = SolverQuery(
            game_state={'board': 'Ah Kh Qh'},
            query_type='equity',
            parameters={'hand_strength': 0.7, 'board_texture': 'wet'},
            approximation_level=2
        )
        
        result = self.engine.approximate_equity(query)
        
        self.assertIn('equity', result)
        self.assertIn('confidence', result)
        self.assertGreaterEqual(result['equity'], 0.0)
        self.assertLessEqual(result['equity'], 1.0)
    
    def test_approximate_ev(self):
        """Test EV approximation."""
        query = SolverQuery(
            game_state={'pot': 100},
            query_type='ev',
            parameters={'pot_size': 100, 'bet_size': 50, 'win_probability': 0.6},
            approximation_level=2
        )
        
        result = self.engine.approximate_ev(query)
        
        self.assertIn('ev', result)
        self.assertIn('confidence', result)


class TestProgressiveRefiner(unittest.TestCase):
    """Test ProgressiveRefiner functionality."""
    
    def setUp(self):
        """Set up test refiner."""
        self.refiner = ProgressiveRefiner()
    
    def test_refine_with_time(self):
        """Test refinement with sufficient time."""
        initial_result = {'action': 'raise', 'confidence': 0.5}
        
        query = SolverQuery(
            game_state={},
            query_type='action',
            parameters={},
            max_time_ms=1000
        )
        
        refined = self.refiner.refine(initial_result, query, 500)
        
        # Confidence should improve
        self.assertGreater(refined['confidence'], initial_result['confidence'])
    
    def test_refine_without_time(self):
        """Test refinement with insufficient time."""
        initial_result = {'action': 'raise', 'confidence': 0.5}
        
        query = SolverQuery(
            game_state={},
            query_type='action',
            parameters={},
            max_time_ms=1000
        )
        
        refined = self.refiner.refine(initial_result, query, 10)
        
        # Should not change much with little time
        self.assertLessEqual(refined['confidence'], 0.6)


class TestLatencyOptimizer(unittest.TestCase):
    """Test LatencyOptimizer functionality."""
    
    def setUp(self):
        """Set up test optimizer."""
        self.optimizer = LatencyOptimizer()
    
    def test_record_latency(self):
        """Test recording latencies."""
        self.optimizer.record_latency(100.0)
        self.optimizer.record_latency(200.0)
        
        avg = self.optimizer.get_average_latency()
        self.assertEqual(avg, 150.0)
    
    def test_p95_latency(self):
        """Test 95th percentile calculation."""
        for i in range(100):
            self.optimizer.record_latency(float(i))
        
        p95 = self.optimizer.get_p95_latency()
        self.assertGreaterEqual(p95, 90.0)
        self.assertLessEqual(p95, 100.0)
    
    def test_optimize_query(self):
        """Test query optimization based on latency."""
        # Record high latencies
        for _ in range(10):
            self.optimizer.record_latency(900.0)
        
        query = SolverQuery(
            game_state={},
            query_type='action',
            parameters={},
            max_time_ms=1000,
            approximation_level=1
        )
        
        initial_level = query.approximation_level
        optimized = self.optimizer.optimize_query(query)
        
        # Should increase approximation level
        self.assertGreater(optimized.approximation_level, initial_level)
    
    def test_get_stats(self):
        """Test getting latency statistics."""
        self.optimizer.record_latency(100.0)
        self.optimizer.record_latency(200.0)
        
        stats = self.optimizer.get_stats()
        
        self.assertIn('average_latency_ms', stats)
        self.assertIn('p95_latency_ms', stats)
        self.assertIn('query_count', stats)
        self.assertEqual(stats['query_count'], 2)


class TestRealtimeSolverAPI(unittest.TestCase):
    """Test RealtimeSolverAPI functionality."""
    
    def setUp(self):
        """Set up test API."""
        self.api = RealtimeSolverAPI(cache_size=10, max_parallel_workers=2)
    
    def tearDown(self):
        """Clean up API."""
        self.api.shutdown()
    
    def test_query_range(self):
        """Test range query."""
        query = SolverQuery(
            game_state={'position': 'BTN'},
            query_type='range',
            parameters={'action': 'raise'}
        )
        
        result = self.api.query(query)
        
        self.assertEqual(result.result_type, 'range')
        self.assertIn('range', result.data)
        self.assertGreater(result.confidence, 0)
    
    def test_query_action(self):
        """Test action query."""
        query = SolverQuery(
            game_state={'position': 'BTN'},
            query_type='action',
            parameters={'pot_odds': 0.33, 'equity': 0.60}
        )
        
        result = self.api.query(query)
        
        self.assertEqual(result.result_type, 'action')
        self.assertIn('action', result.data)
    
    def test_query_caching(self):
        """Test that identical queries are cached."""
        query = SolverQuery(
            game_state={'position': 'BTN'},
            query_type='action',
            parameters={'pot_odds': 0.33}
        )
        
        # First query
        result1 = self.api.query(query)
        self.assertFalse(result1.cached)
        
        # Second identical query should be cached
        result2 = self.api.query(query)
        self.assertTrue(result2.cached)
    
    def test_query_approximation(self):
        """Test query with approximation."""
        query = SolverQuery(
            game_state={'position': 'BTN'},
            query_type='action',
            parameters={'pot_odds': 0.33, 'equity': 0.60},
            approximation_level=2
        )
        
        result = self.api.query(query)
        
        self.assertTrue(result.approximated)
    
    def test_query_batch(self):
        """Test batch queries."""
        queries = [
            SolverQuery(
                game_state={'position': 'BTN'},
                query_type='action',
                parameters={'pot_odds': 0.33, 'equity': 0.60}
            ),
            SolverQuery(
                game_state={'position': 'UTG'},
                query_type='range',
                parameters={'action': 'raise'}
            )
        ]
        
        results = self.api.query_batch(queries)
        
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.confidence > 0 for r in results))
    
    def test_get_stats(self):
        """Test getting API statistics."""
        query = SolverQuery(
            game_state={'position': 'BTN'},
            query_type='action',
            parameters={'pot_odds': 0.33}
        )
        
        self.api.query(query)
        
        stats = self.api.get_stats()
        
        self.assertIn('total_queries', stats)
        self.assertIn('cache_stats', stats)
        self.assertIn('latency_stats', stats)
        self.assertEqual(stats['total_queries'], 1)
    
    def test_clear_cache(self):
        """Test clearing the cache."""
        query = SolverQuery(
            game_state={'position': 'BTN'},
            query_type='action',
            parameters={'pot_odds': 0.33}
        )
        
        self.api.query(query)
        self.api.clear_cache()
        
        stats = self.api.get_stats()
        self.assertEqual(stats['cache_stats']['size'], 0)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def test_create_solver_api(self):
        """Test creating API with convenience function."""
        api = create_solver_api(cache_size=100, max_workers=2)
        
        self.assertIsInstance(api, RealtimeSolverAPI)
        self.assertEqual(api.cache.max_size, 100)
        
        api.shutdown()
    
    def test_quick_query(self):
        """Test quick query convenience function."""
        result = quick_query(
            game_state={'position': 'BTN'},
            query_type='action',
            parameters={'pot_odds': 0.33, 'equity': 0.60}
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.result_type, 'action')
        self.assertIn('action', result.data)


if __name__ == '__main__':
    unittest.main()
