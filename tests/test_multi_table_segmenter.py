#!/usr/bin/env python3
"""
Test suite for Multi-Table Layout Segmenter Module

This test suite validates the functionality of the multi-table segmenter
including table detection, component segmentation, and model integration.
"""

import unittest
import tempfile
import shutil
import json
import cv2
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
try:
    import torch
except ImportError:  # pragma: no cover - allows tests to run without torch installed
    torch = None

import sys
sys.path.append('src')

from pokertool.modules.multi_table_segmenter import (
    MultiTableSegmenter,
    DetectedObject,
    TableLayout,
    SegmentationResult,
    PokerSegmentationNet
)

class TestMultiTableSegmenter(unittest.TestCase):
    """Test cases for the Multi-Table Segmenter."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.model_dir = Path(self.temp_dir) / "models"
        self.config_path = Path(self.temp_dir) / "test_config.json"
        
        # Create test configuration
        test_config = {
            "segmentation": {
                "input_size": [480, 640],  # Smaller for testing
                "batch_size": 1,
                "max_detections": 50,
                "nms_threshold": 0.4,
                "overlap_threshold": 0.3,
                "min_table_size": 5000,  # Smaller for test images
                "model_preference": ["traditional", "yolo", "custom"]
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Create test images
        self.single_table_image = self._create_single_table_image()
        self.multi_table_image = self._create_multi_table_image()
        self.no_table_image = self._create_no_table_image()
        
        self.single_table_path = Path(self.temp_dir) / "single_table.png"
        self.multi_table_path = Path(self.temp_dir) / "multi_table.png"
        self.no_table_path = Path(self.temp_dir) / "no_table.png"
        
        cv2.imwrite(str(self.single_table_path), self.single_table_image)
        cv2.imwrite(str(self.multi_table_path), self.multi_table_image)
        cv2.imwrite(str(self.no_table_path), self.no_table_image)
        
    def tearDown(self):
        """Clean up after each test method."""
        shutil.rmtree(self.temp_dir)
    
    def _create_single_table_image(self) -> np.ndarray:
        """Create a test image with a single poker table."""
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw poker table (dark green oval)
        center = (320, 240)
        axes = (200, 120)
        cv2.ellipse(image, center, axes, 0, 0, 360, (50, 100, 50), -1)
        
        # Add table components
        # Community cards area (center)
        cv2.rectangle(image, (280, 220), (360, 260), (255, 255, 255), -1)
        
        # Player positions (circles around table)
        positions = [
            (320, 160),  # Top
            (400, 180),  # Top-right
            (420, 240),  # Right
            (400, 300),  # Bottom-right
            (320, 320),  # Bottom
            (240, 300),  # Bottom-left
            (220, 240),  # Left
            (240, 180),  # Top-left
        ]
        
        for i, pos in enumerate(positions):
            # Player seat
            cv2.circle(image, pos, 25, (100, 100, 100), -1)
            # Chip stack
            cv2.circle(image, pos, 15, (0, 0, 255), -1)
        
        # Dealer button
        cv2.circle(image, (350, 200), 10, (255, 255, 0), -1)
        
        # Pot area
        cv2.rectangle(image, (300, 200), (340, 220), (255, 255, 0), -1)
        
        return image
    
    def _create_multi_table_image(self) -> np.ndarray:
        """Create a test image with multiple poker tables."""
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Table 1 (top-left)
        center1 = (160, 120)
        axes1 = (100, 60)
        cv2.ellipse(image, center1, axes1, 0, 0, 360, (50, 100, 50), -1)
        cv2.rectangle(image, (140, 110), (180, 130), (255, 255, 255), -1)
        
        # Table 2 (top-right)
        center2 = (480, 120)
        axes2 = (100, 60)
        cv2.ellipse(image, center2, axes2, 0, 0, 360, (50, 100, 50), -1)
        cv2.rectangle(image, (460, 110), (500, 130), (255, 255, 255), -1)
        
        # Table 3 (bottom-center)
        center3 = (320, 360)
        axes3 = (120, 80)
        cv2.ellipse(image, center3, axes3, 0, 0, 360, (50, 100, 50), -1)
        cv2.rectangle(image, (290, 350), (350, 370), (255, 255, 255), -1)
        
        # Add some player seats for each table
        for center in [center1, center2, center3]:
            for angle in [0, 90, 180, 270]:
                x = int(center[0] + 40 * np.cos(np.radians(angle)))
                y = int(center[1] + 40 * np.sin(np.radians(angle)))
                cv2.circle(image, (x, y), 15, (100, 100, 100), -1)
        
        return image
    
    def _create_no_table_image(self) -> np.ndarray:
        """Create a test image with no poker tables."""
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        # Add some random shapes but no table-like structures
        cv2.rectangle(image, (100, 100), (200, 200), (255, 0, 0), -1)
        cv2.circle(image, (400, 300), 50, (0, 255, 0), -1)
        return image
    
    def test_initialization(self):
        """Test MultiTableSegmenter initialization."""
        segmenter = MultiTableSegmenter(
            model_dir=str(self.model_dir),
            config_path=str(self.config_path),
            use_gpu=False,  # Disable GPU for testing
            confidence_threshold=0.5
        )
        
        self.assertTrue(self.model_dir.exists())
        self.assertIsInstance(segmenter.component_classes, dict)
        self.assertIsInstance(segmenter.class_colors, dict)
        self.assertGreater(len(segmenter.component_classes), 0)
        self.assertFalse(segmenter.use_gpu)  # Should be False as set
        self.assertEqual(segmenter.confidence_threshold, 0.5)
        
    def test_traditional_segmentation_single_table(self):
        """Test traditional segmentation method on single table."""
        segmenter = MultiTableSegmenter(
            model_dir=str(self.model_dir),
            config_path=str(self.config_path),
            use_gpu=False
        )
        
        result = segmenter.segment_image(self.single_table_image, method="traditional")
        
        self.assertIsInstance(result, SegmentationResult)
        self.assertEqual(result.model_used, "traditional")
        self.assertGreater(result.processing_time, 0)
        self.assertGreaterEqual(result.get_table_count(), 1)
        
        # Check that tables were detected
        if result.detected_tables:
            table = result.detected_tables[0]
            self.assertIsInstance(table, TableLayout)
            self.assertIsInstance(table.table_id, str)
            self.assertIsInstance(table.table_bbox, tuple)
            self.assertEqual(len(table.table_bbox), 4)
            self.assertIsInstance(table.components, dict)
            
    def test_traditional_segmentation_multi_table(self):
        """Test traditional segmentation method on multiple tables."""
        segmenter = MultiTableSegmenter(
            model_dir=str(self.model_dir),
            config_path=str(self.config_path),
            use_gpu=False
        )
        
        result = segmenter.segment_image(self.multi_table_image, method="traditional")
        
        self.assertIsInstance(result, SegmentationResult)
        self.assertEqual(result.model_used, "traditional")
        self.assertGreaterEqual(result.get_table_count(), 2)  # Should detect multiple tables
        
        # Check for overlapping tables
        overlaps = result.get_overlapping_tables()
        self.assertIsInstance(overlaps, list)
        
    def test_traditional_segmentation_no_table(self):
        """Test traditional segmentation method on image with no tables."""
        segmenter = MultiTableSegmenter(
            model_dir=str(self.model_dir),
            config_path=str(self.config_path),
            use_gpu=False
        )
        
        result = segmenter.segment_image(self.no_table_image, method="traditional")
        
        self.assertIsInstance(result, SegmentationResult)
        self.assertEqual(result.model_used, "traditional")
        # Should detect 0 or very few tables
        self.assertLessEqual(result.get_table_count(), 1)
        
    def test_auto_method_selection(self):
        """Test automatic method selection."""
        segmenter = MultiTableSegmenter(
            model_dir=str(self.model_dir),
            config_path=str(self.config_path),
            use_gpu=False
        )
        
        result = segmenter.segment_image(self.single_table_image, method="auto")
        
        self.assertIsInstance(result, SegmentationResult)
        self.assertIn(result.model_used, ["traditional", "yolo", "custom", "sam", "onnx"])
        
    def test_visualization(self):
        """Test segmentation visualization."""
        segmenter = MultiTableSegmenter(
            model_dir=str(self.model_dir),
            config_path=str(self.config_path),
            use_gpu=False
        )
        
        result = segmenter.segment_image(self.single_table_image, method="traditional")
        
        # Test visualization without saving
        vis_image = segmenter.visualize_segmentation(self.single_table_image, result)
        
        self.assertIsInstance(vis_image, np.ndarray)
        self.assertEqual(vis_image.shape, self.single_table_image.shape)
        
        # Test visualization with saving
        output_path = Path(self.temp_dir) / "visualization.png"
        vis_image = segmenter.visualize_segmentation(
            self.single_table_image, 
            result, 
            str(output_path)
        )
        
        self.assertTrue(output_path.exists())
        
    def test_extract_table_regions(self):
        """Test extracting table regions."""
        segmenter = MultiTableSegmenter(
            model_dir=str(self.model_dir),
            config_path=str(self.config_path),
            use_gpu=False
        )
        
        result = segmenter.segment_image(self.single_table_image, method="traditional")
        table_regions = segmenter.extract_table_regions(self.single_table_image, result)
        
        self.assertIsInstance(table_regions, dict)
        
        if table_regions:
            for table_id, region in table_regions.items():
                self.assertIsInstance(table_id, str)
                self.assertIsInstance(region, np.ndarray)
                self.assertEqual(len(region.shape), 3)  # Should be color image
                
    def test_get_component_crops(self):
        """Test extracting component crops."""
        segmenter = MultiTableSegmenter(
            model_dir=str(self.model_dir),
            config_path=str(self.config_path),
            use_gpu=False
        )
        
        result = segmenter.segment_image(self.single_table_image, method="traditional")
        component_crops = segmenter.get_component_crops(self.single_table_image, result)
        
        self.assertIsInstance(component_crops, dict)
        
        if component_crops:
            for table_id, components in component_crops.items():
                self.assertIsInstance(table_id, str)
                self.assertIsInstance(components, dict)
                
                for component_type, crops in components.items():
                    self.assertIsInstance(component_type, str)
                    self.assertIsInstance(crops, list)
                    
                    for crop in crops:
                        self.assertIsInstance(crop, np.ndarray)
                        
    def test_statistics_tracking(self):
        """Test statistics tracking."""
        segmenter = MultiTableSegmenter(
            model_dir=str(self.model_dir),
            config_path=str(self.config_path),
            use_gpu=False
        )
        
        # Initial statistics
        initial_stats = segmenter.get_statistics()
        self.assertEqual(initial_stats["total_frames_processed"], 0)
        self.assertEqual(initial_stats["avg_processing_time"], 0.0)
        self.assertEqual(initial_stats["total_tables_detected"], 0)
        
        # Process some images
        result1 = segmenter.segment_image(self.single_table_image, method="traditional")
        result2 = segmenter.segment_image(self.multi_table_image, method="traditional")
        
        # Check updated statistics
        stats = segmenter.get_statistics()
        self.assertEqual(stats["total_frames_processed"], 2)
        self.assertGreater(stats["avg_processing_time"], 0)
        self.assertEqual(stats["total_tables_detected"], 
                        result1.get_table_count() + result2.get_table_count())
        
    def test_batch_processing(self):
        """Test batch processing functionality."""
        segmenter = MultiTableSegmenter(
            model_dir=str(self.model_dir),
            config_path=str(self.config_path),
            use_gpu=False
        )
        
        image_paths = [
            str(self.single_table_path),
            str(self.multi_table_path),
            str(self.no_table_path)
        ]
        
        output_dir = Path(self.temp_dir) / "batch_output"
        results = segmenter.batch_process_images(image_paths, str(output_dir))
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), len(image_paths))
        
        for result in results:
            self.assertIsInstance(result, SegmentationResult)
            
        # Check output directory was created
        self.assertTrue(output_dir.exists())
        
    def test_export_results_json(self):
        """Test exporting results to JSON."""
        segmenter = MultiTableSegmenter(
            model_dir=str(self.model_dir),
            config_path=str(self.config_path),
            use_gpu=False
        )
        
        result = segmenter.segment_image(self.single_table_image, method="traditional")
        results = [result]
        
        output_path = Path(self.temp_dir) / "results.json"
        segmenter.export_results(results, str(output_path), format="json")
        
        self.assertTrue(output_path.exists())
        
        # Load and validate JSON
        with open(output_path, 'r') as f:
            data = json.load(f)
            
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        
        result_data = data[0]
        self.assertIn("image_id", result_data)
        self.assertIn("processing_time", result_data)
        self.assertIn("model_used", result_data)
        self.assertIn("tables", result_data)
        
    def test_detected_object(self):
        """Test DetectedObject named tuple."""
        obj = DetectedObject(
            class_name="table",
            confidence=0.95,
            bbox=(100, 100, 300, 200),
            center=(200, 150),
            area=20000
        )
        
        self.assertEqual(obj.class_name, "table")
        self.assertEqual(obj.confidence, 0.95)
        self.assertEqual(obj.bbox, (100, 100, 300, 200))
        self.assertEqual(obj.center, (200, 150))
        self.assertEqual(obj.area, 20000)
        self.assertIsNone(obj.mask)
        
    def test_table_layout(self):
        """Test TableLayout dataclass."""
        components = {
            "table": [DetectedObject("table", 0.9, (0, 0, 100, 100), (50, 50), 10000)],
            "cards_community": [DetectedObject("cards_community", 0.8, (40, 40, 60, 60), (50, 50), 400)]
        }
        
        layout = TableLayout(
            table_id="table_1",
            table_bbox=(0, 0, 100, 100),
            confidence=0.9,
            components=components,
            metadata={"test": "value"}
        )
        
        self.assertEqual(layout.table_id, "table_1")
        self.assertEqual(layout.get_component_count("table"), 1)
        self.assertEqual(layout.get_component_count("cards_community"), 1)
        self.assertEqual(layout.get_component_count("nonexistent"), 0)
        
        best_table = layout.get_best_component("table")
        self.assertIsNotNone(best_table)
        self.assertEqual(best_table.confidence, 0.9)
        
        best_nonexistent = layout.get_best_component("nonexistent")
        self.assertIsNone(best_nonexistent)
        
    def test_segmentation_result(self):
        """Test SegmentationResult dataclass."""
        table1 = TableLayout("table_1", (0, 0, 50, 50), 0.9, {}, {})
        table2 = TableLayout("table_2", (25, 25, 75, 75), 0.8, {}, {})  # Overlapping
        table3 = TableLayout("table_3", (100, 100, 150, 150), 0.7, {}, {})  # Non-overlapping
        
        result = SegmentationResult(
            detected_tables=[table1, table2, table3],
            processing_time=0.5,
            model_used="test",
            input_resolution=(480, 640),
            confidence_threshold=0.5,
            total_objects=10
        )
        
        self.assertEqual(result.get_table_count(), 3)
        
        overlaps = result.get_overlapping_tables()
        self.assertIsInstance(overlaps, list)
        # Should detect overlap between table_1 and table_2
        self.assertTrue(any("table_1" in overlap and "table_2" in overlap for overlap in overlaps))
        
    def test_invalid_inputs(self):
        """Test handling of invalid inputs."""
        segmenter = MultiTableSegmenter(
            model_dir=str(self.model_dir),
            config_path=str(self.config_path),
            use_gpu=False
        )
        
        # Test invalid image path
        with self.assertRaises((FileNotFoundError, ValueError)):
            segmenter.segment_image("nonexistent.png")
            
        # Test invalid image data
        with self.assertRaises(ValueError):
            segmenter.segment_image(None)
            
    @unittest.skipIf(torch is None, "PyTorch not installed - skipping neural segmentation tests")
    def test_poker_segmentation_net(self):
        """Test PokerSegmentationNet model architecture."""
        model = PokerSegmentationNet(num_classes=12)
        
        # Test model structure
        self.assertEqual(model.num_classes, 12)
        self.assertIsInstance(model.backbone, torch.nn.Module)
        self.assertIsInstance(model.segmentation_head, torch.nn.Sequential)
        self.assertIsInstance(model.detection_head, torch.nn.Sequential)
        
        # Test forward pass with dummy input
        dummy_input = torch.randn(1, 3, 224, 224)
        
        with torch.no_grad():
            output = model(dummy_input)
            
        self.assertIsInstance(output, dict)
        self.assertIn('segmentation', output)
        self.assertIn('detection', output)
        
        # Check output shapes
        seg_output = output['segmentation']
        det_output = output['detection']
        
        self.assertEqual(len(seg_output.shape), 4)  # [batch, classes, height, width]
        self.assertEqual(seg_output.shape[1], 12)   # Number of classes
        
        self.assertEqual(len(det_output.shape), 3)  # [batch, classes, 5]
        self.assertEqual(det_output.shape[1], 12)   # Number of classes
        self.assertEqual(det_output.shape[2], 5)    # conf + 4 bbox coords


class TestIntegration(unittest.TestCase):
    """Integration tests for the Multi-Table Segmenter."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.model_dir = Path(self.temp_dir) / "models"
        self.config_path = Path(self.temp_dir) / "test_config.json"
        
        # Create realistic test configuration
        test_config = {
            "segmentation": {
                "input_size": [480, 640],
                "batch_size": 1,
                "max_detections": 100,
                "nms_threshold": 0.4,
                "overlap_threshold": 0.3,
                "min_table_size": 5000,
                "model_preference": ["traditional", "yolo", "custom"]
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
            
    def tearDown(self):
        """Clean up integration test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_full_workflow(self):
        """Test the complete segmentation workflow."""
        segmenter = MultiTableSegmenter(
            model_dir=str(self.model_dir),
            config_path=str(self.config_path),
            use_gpu=False
        )
        
        # Create complex test image with multiple tables and components
        complex_image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Table 1
        cv2.ellipse(complex_image, (160, 120), (80, 50), 0, 0, 360, (50, 100, 50), -1)
        cv2.rectangle(complex_image, (140, 110), (180, 130), (255, 255, 255), -1)
        
        # Table 2
        cv2.ellipse(complex_image, (480, 120), (80, 50), 0, 0, 360, (50, 100, 50), -1)
        cv2.rectangle(complex_image, (460, 110), (500, 130), (255, 255, 255), -1)
        
        # Add various components
        positions = [(120, 90), (200, 90), (440, 90), (520, 90)]
        for pos in positions:
            cv2.circle(complex_image, pos, 15, (100, 100, 100), -1)  # Player seats
            cv2.circle(complex_image, pos, 10, (255, 0, 0), -1)      # Chip stacks
        
        complex_path = Path(self.temp_dir) / "complex.png"
        cv2.imwrite(str(complex_path), complex_image)
        
        # Step 1: Segment the image
        result = segmenter.segment_image(str(complex_path), method="traditional")
        
        self.assertIsInstance(result, SegmentationResult)
        self.assertGreater(result.processing_time, 0)
        
        # Step 2: Extract table regions
        table_regions = segmenter.extract_table_regions(complex_image, result)
        self.assertIsInstance(table_regions, dict)
        
        # Step 3: Get component crops
        component_crops = segmenter.get_component_crops(complex_image, result)
        self.assertIsInstance(component_crops, dict)
        
        # Step 4: Create visualization
        vis_path = Path(self.temp_dir) / "visualization.png"
        vis_image = segmenter.visualize_segmentation(
            complex_image, 
            result, 
            str(vis_path)
        )
        
        self.assertIsInstance(vis_image, np.ndarray)
        self.assertTrue(vis_path.exists())
        
        # Step 5: Export results
        export_path = Path(self.temp_dir) / "results.json"
        segmenter.export_results([result], str(export_path))
        
        self.assertTrue(export_path.exists())
        
        # Step 6: Check statistics
        stats = segmenter.get_statistics()
        self.assertGreater(stats["total_frames_processed"], 0)
        self.assertGreater(stats["avg_processing_time"], 0)
        
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        segmenter = MultiTableSegmenter(
            model_dir=str(self.model_dir),
            config_path=str(self.config_path),
            use_gpu=False
        )
        
        # Test with corrupted image data
        corrupted_image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        
        # Should not crash, should return valid result
        result = segmenter.segment_image(corrupted_image, method="traditional")
        
        self.assertIsInstance(result, SegmentationResult)
        self.assertEqual(result.model_used, "traditional")
        
        # Test with invalid method
        result = segmenter.segment_image(corrupted_image, method="nonexistent")
        
        self.assertIsInstance(result, SegmentationResult)
        # Should fallback to traditional method
        self.assertEqual(result.model_used, "traditional")


if __name__ == '__main__':
    unittest.main()
