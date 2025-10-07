#!/usr/bin/env python3
"""
Test suite for Adaptive UI Change Detection Module

This test suite validates the functionality of the adaptive UI detector
including baseline management, image comparison, and change detection.
"""

import unittest
import tempfile
import shutil
import json
import cv2
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.append('src')

from pokertool.modules.adaptive_ui_detector import (
    AdaptiveUIDetector, 
    BaselineState, 
    ComparisonResult, 
    RegionOfInterest
)

class TestAdaptiveUIDetector(unittest.TestCase):
    """Test cases for the Adaptive UI Detector."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.baseline_dir = Path(self.temp_dir) / "ui_baselines"
        self.reports_dir = Path(self.temp_dir) / "ui_changes"
        self.config_path = Path(self.temp_dir) / "test_config.json"
        
        # Create test configuration
        test_config = {
            "ui_detection": {
                "global_ssim_threshold": 0.80,
                "hash_distance_threshold": 10,
                "alert_critical_changes": True,
                "generate_visualizations": False,  # Disable for testing
                "max_baselines_per_site": 50
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Create test images
        self.test_image_1 = self._create_test_image((800, 600), (100, 150, 100))  # Green-ish
        self.test_image_2 = self._create_test_image((800, 600), (100, 150, 100))  # Same as image 1
        self.test_image_3 = self._create_test_image((800, 600), (150, 100, 100))  # Different (Red-ish)
        
        self.test_image_path_1 = Path(self.temp_dir) / "test1.png"
        self.test_image_path_2 = Path(self.temp_dir) / "test2.png"
        self.test_image_path_3 = Path(self.temp_dir) / "test3.png"
        
        cv2.imwrite(str(self.test_image_path_1), self.test_image_1)
        cv2.imwrite(str(self.test_image_path_2), self.test_image_2)
        cv2.imwrite(str(self.test_image_path_3), self.test_image_3)
        
    def tearDown(self):
        """Clean up after each test method."""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_image(self, size: tuple, color: tuple) -> np.ndarray:
        """Create a test image with specified size and color."""
        height, width = size
        image = np.full((height, width, 3), color, dtype=np.uint8)
        
        # Add some poker table elements
        # Draw table (oval)
        center = (width // 2, height // 2)
        axes = (width // 3, height // 4)
        cv2.ellipse(image, center, axes, 0, 0, 360, (50, 100, 50), -1)
        
        # Draw cards area
        cv2.rectangle(image, (width//2 - 60, height//2 - 20), 
                     (width//2 + 60, height//2 + 20), (255, 255, 255), -1)
        
        # Draw some buttons
        cv2.circle(image, (width//4, height//2), 20, (255, 0, 0), -1)
        cv2.circle(image, (3*width//4, height//2), 20, (0, 0, 255), -1)
        
        return image
    
    def test_initialization(self):
        """Test AdaptiveUIDetector initialization."""
        detector = AdaptiveUIDetector(
            baseline_dir=str(self.baseline_dir),
            reports_dir=str(self.reports_dir),
            config_path=str(self.config_path)
        )
        
        self.assertTrue(self.baseline_dir.exists())
        self.assertTrue(self.reports_dir.exists())
        self.assertIsInstance(detector.regions_of_interest, dict)
        self.assertGreater(len(detector.regions_of_interest), 0)
        self.assertIn("cards_area", detector.regions_of_interest)
        self.assertIn("pot_area", detector.regions_of_interest)
        
    def test_add_baseline_screenshot(self):
        """Test adding baseline screenshots."""
        detector = AdaptiveUIDetector(
            baseline_dir=str(self.baseline_dir),
            reports_dir=str(self.reports_dir),
            config_path=str(self.config_path)
        )
        
        # Add baseline screenshot
        baseline_id = detector.add_baseline_screenshot(
            str(self.test_image_path_1),
            site_name="betfair",
            resolution="800x600",
            theme="default",
            metadata={"table_type": "nlhe", "stake": "1/2"}
        )
        
        self.assertIsInstance(baseline_id, str)
        self.assertIn(baseline_id, detector.baselines)
        
        baseline = detector.baselines[baseline_id]
        self.assertEqual(baseline.site_name, "betfair")
        self.assertEqual(baseline.resolution, "800x600")
        self.assertEqual(baseline.theme, "default")
        self.assertEqual(baseline.metadata["table_type"], "nlhe")
        
        # Check that baseline file was created
        baseline_file = self.baseline_dir / f"{baseline_id}.png"
        self.assertTrue(baseline_file.exists())
        
    def test_compare_screenshot_match(self):
        """Test comparing a screenshot that should match a baseline."""
        detector = AdaptiveUIDetector(
            baseline_dir=str(self.baseline_dir),
            reports_dir=str(self.reports_dir),
            config_path=str(self.config_path)
        )
        
        # Add baseline
        detector.add_baseline_screenshot(
            str(self.test_image_path_1),
            site_name="betfair",
            resolution="800x600",
            theme="default"
        )
        
        # Compare identical image
        result = detector.compare_screenshot(
            str(self.test_image_path_2),  # Same image
            site_name="betfair",
            resolution="800x600",
            theme="default"
        )
        
        self.assertIsInstance(result, ComparisonResult)
        self.assertTrue(result.is_match)
        self.assertGreater(result.best_match_score, 0.9)  # Should be very high for identical images
        self.assertEqual(len(result.critical_changes), 0)
        self.assertIsInstance(result.hash_distances, dict)
        self.assertIsInstance(result.ssim_scores, dict)
        
    def test_compare_screenshot_no_match(self):
        """Test comparing a screenshot that should not match a baseline."""
        detector = AdaptiveUIDetector(
            baseline_dir=str(self.baseline_dir),
            reports_dir=str(self.reports_dir),
            config_path=str(self.config_path)
        )
        
        # Add baseline
        detector.add_baseline_screenshot(
            str(self.test_image_path_1),
            site_name="betfair",
            resolution="800x600",
            theme="default"
        )
        
        # Compare different image
        result = detector.compare_screenshot(
            str(self.test_image_path_3),  # Different image
            site_name="betfair",
            resolution="800x600",
            theme="default"
        )
        
        self.assertIsInstance(result, ComparisonResult)
        self.assertLess(result.best_match_score, 0.9)  # Should be lower for different images
        self.assertIsInstance(result.hash_distances, dict)
        self.assertIsInstance(result.ssim_scores, dict)
        
    def test_compare_screenshot_no_baseline(self):
        """Test comparing a screenshot when no matching baseline exists."""
        detector = AdaptiveUIDetector(
            baseline_dir=str(self.baseline_dir),
            reports_dir=str(self.reports_dir),
            config_path=str(self.config_path)
        )
        
        # Compare without any baseline
        result = detector.compare_screenshot(
            str(self.test_image_path_1),
            site_name="pokerstars",  # Different site
            resolution="800x600",
            theme="default"
        )
        
        self.assertIsInstance(result, ComparisonResult)
        self.assertFalse(result.is_match)
        self.assertEqual(result.best_match_score, 0.0)
        self.assertEqual(result.best_match_baseline, "")
        
    def test_generate_alert_report(self):
        """Test generating alert reports."""
        detector = AdaptiveUIDetector(
            baseline_dir=str(self.baseline_dir),
            reports_dir=str(self.reports_dir),
            config_path=str(self.config_path)
        )
        
        # Create a comparison result
        result = ComparisonResult(
            is_match=False,
            best_match_score=0.65,
            best_match_baseline="test_baseline",
            hash_distances={"perceptual": 15, "difference": 12, "average": 8},
            ssim_scores={"cards_area": 0.70, "pot_area": 0.85},
            diff_regions=["cards_area"],
            critical_changes=["cards_area"]
        )
        
        # Generate alert report
        report_path = detector.generate_alert_report(
            result,
            str(self.test_image_path_1),
            "betfair"
        )
        
        self.assertTrue(Path(report_path).exists())
        
        # Load and validate report
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        self.assertEqual(report_data["site_name"], "betfair")
        self.assertEqual(report_data["alert_level"], "CRITICAL")
        self.assertFalse(report_data["is_match"])
        self.assertEqual(report_data["match_score"], 0.65)
        self.assertIn("cards_area", report_data["critical_regions"])
        self.assertIsInstance(report_data["recommendations"], list)
        self.assertGreater(len(report_data["recommendations"]), 0)
        
    def test_detection_statistics(self):
        """Test detection statistics tracking."""
        detector = AdaptiveUIDetector(
            baseline_dir=str(self.baseline_dir),
            reports_dir=str(self.reports_dir),
            config_path=str(self.config_path)
        )
        
        # Initial stats
        initial_stats = detector.get_detection_statistics()
        self.assertEqual(initial_stats["total_comparisons"], 0)
        self.assertEqual(initial_stats["matches_found"], 0)
        self.assertEqual(initial_stats["changes_detected"], 0)
        
        # Add baseline and perform comparisons
        detector.add_baseline_screenshot(
            str(self.test_image_path_1),
            site_name="betfair",
            resolution="800x600"
        )
        
        # Perform some comparisons
        detector.compare_screenshot(str(self.test_image_path_2), "betfair", "800x600")
        detector.compare_screenshot(str(self.test_image_path_3), "betfair", "800x600")
        
        # Check updated stats
        stats = detector.get_detection_statistics()
        self.assertEqual(stats["total_comparisons"], 2)
        self.assertGreater(stats["avg_processing_time"], 0)
        
    def test_region_of_interest(self):
        """Test RegionOfInterest named tuple."""
        roi = RegionOfInterest("test_region", 100, 200, 300, 400, 0.85, True)
        
        self.assertEqual(roi.name, "test_region")
        self.assertEqual(roi.x, 100)
        self.assertEqual(roi.y, 200)
        self.assertEqual(roi.width, 300)
        self.assertEqual(roi.height, 400)
        self.assertEqual(roi.threshold, 0.85)
        self.assertTrue(roi.critical)
        
    def test_baseline_state_serialization(self):
        """Test BaselineState serialization/deserialization."""
        detector = AdaptiveUIDetector(
            baseline_dir=str(self.baseline_dir),
            reports_dir=str(self.reports_dir),
            config_path=str(self.config_path)
        )
        
        # Add baseline
        baseline_id = detector.add_baseline_screenshot(
            str(self.test_image_path_1),
            site_name="betfair",
            resolution="800x600",
            theme="dark",
            metadata={"test": "value"}
        )
        
        # Check baseline was saved and can be loaded
        detector2 = AdaptiveUIDetector(
            baseline_dir=str(self.baseline_dir),
            reports_dir=str(self.reports_dir),
            config_path=str(self.config_path)
        )
        
        self.assertIn(baseline_id, detector2.baselines)
        baseline = detector2.baselines[baseline_id]
        self.assertEqual(baseline.site_name, "betfair")
        self.assertEqual(baseline.resolution, "800x600")
        self.assertEqual(baseline.theme, "dark")
        self.assertEqual(baseline.metadata["test"], "value")
        
    def test_invalid_screenshot_path(self):
        """Test handling of invalid screenshot paths."""
        detector = AdaptiveUIDetector(
            baseline_dir=str(self.baseline_dir),
            reports_dir=str(self.reports_dir),
            config_path=str(self.config_path)
        )
        
        # Test adding baseline with invalid path
        with self.assertRaises(FileNotFoundError):
            detector.add_baseline_screenshot(
                "nonexistent.png",
                site_name="betfair",
                resolution="800x600"
            )
        
        # Test comparing with invalid path
        with self.assertRaises(FileNotFoundError):
            detector.compare_screenshot(
                "nonexistent.png",
                site_name="betfair",
                resolution="800x600"
            )
    
    def test_recommendations_generation(self):
        """Test recommendation generation for different scenarios."""
        detector = AdaptiveUIDetector(
            baseline_dir=str(self.baseline_dir),
            reports_dir=str(self.reports_dir),
            config_path=str(self.config_path)
        )
        
        # Test critical changes
        result_critical = ComparisonResult(
            is_match=False,
            best_match_score=0.60,
            best_match_baseline="test",
            hash_distances={},
            ssim_scores={},
            diff_regions=["cards_area", "pot_area"],
            critical_changes=["cards_area"]
        )
        
        recommendations = detector._generate_recommendations(result_critical)
        self.assertIn("IMMEDIATE ACTION REQUIRED", " ".join(recommendations))
        self.assertIn("Card detection may be affected", " ".join(recommendations))
        
        # Test no changes
        result_no_change = ComparisonResult(
            is_match=True,
            best_match_score=0.95,
            best_match_baseline="test",
            hash_distances={},
            ssim_scores={},
            diff_regions=[],
            critical_changes=[]
        )
        
        recommendations = detector._generate_recommendations(result_no_change)
        self.assertIn("No significant changes detected", " ".join(recommendations))


class TestIntegration(unittest.TestCase):
    """Integration tests for the Adaptive UI Detector."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.baseline_dir = Path(self.temp_dir) / "ui_baselines"
        self.reports_dir = Path(self.temp_dir) / "ui_changes"
        self.config_path = Path(self.temp_dir) / "test_config.json"
        
        # Create realistic test configuration
        test_config = {
            "ui_detection": {
                "global_ssim_threshold": 0.80,
                "hash_distance_threshold": 10,
                "alert_critical_changes": True,
                "generate_visualizations": True,
                "max_baselines_per_site": 50
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
            
    def tearDown(self):
        """Clean up integration test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_full_workflow(self):
        """Test the complete UI detection workflow."""
        detector = AdaptiveUIDetector(
            baseline_dir=str(self.baseline_dir),
            reports_dir=str(self.reports_dir),
            config_path=str(self.config_path)
        )
        
        # Create test images
        original_image = np.zeros((600, 800, 3), dtype=np.uint8)
        cv2.rectangle(original_image, (100, 100), (700, 500), (100, 150, 100), -1)
        cv2.rectangle(original_image, (350, 250), (450, 350), (255, 255, 255), -1)
        
        # Slightly modified image
        modified_image = original_image.copy()
        cv2.rectangle(modified_image, (360, 260), (440, 340), (200, 200, 200), -1)
        
        original_path = Path(self.temp_dir) / "original.png"
        modified_path = Path(self.temp_dir) / "modified.png"
        
        cv2.imwrite(str(original_path), original_image)
        cv2.imwrite(str(modified_path), modified_image)
        
        # Step 1: Add baseline
        baseline_id = detector.add_baseline_screenshot(
            str(original_path),
            site_name="betfair",
            resolution="800x600",
            theme="default",
            metadata={"session_id": "test_123"}
        )
        
        self.assertIsInstance(baseline_id, str)
        
        # Step 2: Compare against baseline
        result = detector.compare_screenshot(
            str(modified_path),
            site_name="betfair",
            resolution="800x600",
            theme="default"
        )
        
        self.assertIsInstance(result, ComparisonResult)
        self.assertIsNotNone(result.best_match_baseline)
        
        # Step 3: Generate alert if needed
        if not result.is_match:
            report_path = detector.generate_alert_report(
                result,
                str(modified_path),
                "betfair"
            )
            
            self.assertTrue(Path(report_path).exists())
            
            # Verify report content
            with open(report_path, 'r') as f:
                report_data = json.load(f)
                
            self.assertIn("timestamp", report_data)
            self.assertIn("recommendations", report_data)
            self.assertIsInstance(report_data["recommendations"], list)
        
        # Step 4: Check statistics
        stats = detector.get_detection_statistics()
        self.assertEqual(stats["total_comparisons"], 1)
        self.assertGreater(stats["avg_processing_time"], 0)


if __name__ == '__main__':
    unittest.main()
