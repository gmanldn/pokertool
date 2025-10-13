#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for GPU Accelerated Preprocessing Pipeline
================================================

SCRAPE-013: GPU Accelerated Preprocessing Pipeline Tests

Tests cover:
- Capability detection
- GPU/CPU operations parity
- Performance benchmarking
- Fallback behavior
- Full preprocessing pipeline
"""

import pytest
import numpy as np
import time
from typing import Tuple

# Import module under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from pokertool.gpu_preprocessing import (
    GPUPreprocessor,
    AcceleratorType,
    GPUCapabilities,
    PerformanceMetrics,
    get_gpu_preprocessor,
    benchmark_accelerators,
    CV2_AVAILABLE,
    CUDA_AVAILABLE,
    OPENCL_AVAILABLE
)

# Skip all tests if OpenCV not available
pytestmark = pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")


class TestGPUCapabilities:
    """Test GPU capability detection."""

    def test_capability_detection(self):
        """Test that GPU capabilities are detected correctly."""
        caps = GPUPreprocessor()._detect_capabilities(None)

        assert isinstance(caps, GPUCapabilities)
        assert isinstance(caps.cuda_available, bool)
        assert isinstance(caps.opencl_available, bool)
        assert caps.preferred_accelerator in [
            AcceleratorType.CUDA,
            AcceleratorType.OPENCL,
            AcceleratorType.CPU
        ]

    def test_force_cpu(self):
        """Test forcing CPU accelerator."""
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CPU)

        assert preprocessor.capabilities.preferred_accelerator == AcceleratorType.CPU

    def test_capability_summary(self):
        """Test capability summary string."""
        preprocessor = GPUPreprocessor()
        summary = preprocessor.capabilities.summary()

        assert isinstance(summary, str)
        assert 'GPU Preprocessing Capabilities' in summary
        assert preprocessor.capabilities.preferred_accelerator.value.upper() in summary

    def test_cuda_device_info(self):
        """Test CUDA device information (if available)."""
        if not CUDA_AVAILABLE:
            pytest.skip("CUDA not available")

        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CUDA)
        caps = preprocessor.capabilities

        assert caps.cuda_device_count > 0
        assert isinstance(caps.cuda_device_name, str)


class TestPreprocessingOperations:
    """Test individual preprocessing operations."""

    @pytest.fixture
    def test_image(self) -> np.ndarray:
        """Create a test grayscale image."""
        # Create 640x480 grayscale image with some noise
        img = np.random.randint(50, 200, (480, 640), dtype=np.uint8)
        return img

    @pytest.fixture
    def test_color_image(self) -> np.ndarray:
        """Create a test color image."""
        img = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
        return img

    def test_denoise_cpu(self, test_image):
        """Test CPU denoising."""
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CPU)
        result = preprocessor.denoise(test_image, h=10)

        assert result.shape == test_image.shape
        assert result.dtype == test_image.dtype

    @pytest.mark.skipif(not OPENCL_AVAILABLE, reason="OpenCL not available")
    def test_denoise_opencl(self, test_image):
        """Test OpenCL denoising."""
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.OPENCL)
        result = preprocessor.denoise(test_image, h=10)

        assert result.shape == test_image.shape
        assert result.dtype == test_image.dtype

    @pytest.mark.skipif(not CUDA_AVAILABLE, reason="CUDA not available")
    def test_denoise_cuda(self, test_image):
        """Test CUDA denoising."""
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CUDA)
        result = preprocessor.denoise(test_image, h=10)

        assert result.shape == test_image.shape
        assert result.dtype == test_image.dtype

    def test_clahe_cpu(self, test_image):
        """Test CPU CLAHE."""
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CPU)
        result = preprocessor.clahe(test_image, clip_limit=2.0, tile_size=(8, 8))

        assert result.shape == test_image.shape
        assert result.dtype == test_image.dtype
        # CLAHE should increase contrast
        assert result.std() >= test_image.std() * 0.9

    @pytest.mark.skipif(not OPENCL_AVAILABLE, reason="OpenCL not available")
    def test_clahe_opencl(self, test_image):
        """Test OpenCL CLAHE."""
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.OPENCL)
        result = preprocessor.clahe(test_image, clip_limit=2.0, tile_size=(8, 8))

        assert result.shape == test_image.shape
        assert result.dtype == test_image.dtype

    @pytest.mark.skipif(not CUDA_AVAILABLE, reason="CUDA not available")
    def test_clahe_cuda(self, test_image):
        """Test CUDA CLAHE."""
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CUDA)
        result = preprocessor.clahe(test_image, clip_limit=2.0, tile_size=(8, 8))

        assert result.shape == test_image.shape
        assert result.dtype == test_image.dtype

    def test_gaussian_blur_cpu(self, test_image):
        """Test CPU Gaussian blur."""
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CPU)
        result = preprocessor.gaussian_blur(test_image, ksize=(5, 5), sigma=1.0)

        assert result.shape == test_image.shape
        assert result.dtype == test_image.dtype
        # Blur should reduce variance
        assert result.std() <= test_image.std()

    @pytest.mark.skipif(not OPENCL_AVAILABLE, reason="OpenCL not available")
    def test_gaussian_blur_opencl(self, test_image):
        """Test OpenCL Gaussian blur."""
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.OPENCL)
        result = preprocessor.gaussian_blur(test_image, ksize=(5, 5), sigma=1.0)

        assert result.shape == test_image.shape
        assert result.dtype == test_image.dtype

    @pytest.mark.skipif(not CUDA_AVAILABLE, reason="CUDA not available")
    def test_gaussian_blur_cuda(self, test_image):
        """Test CUDA Gaussian blur."""
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CUDA)
        result = preprocessor.gaussian_blur(test_image, ksize=(5, 5), sigma=1.0)

        assert result.shape == test_image.shape
        assert result.dtype == test_image.dtype

    def test_median_blur_cpu(self, test_image):
        """Test CPU median blur."""
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CPU)
        result = preprocessor.median_blur(test_image, ksize=5)

        assert result.shape == test_image.shape
        assert result.dtype == test_image.dtype

    @pytest.mark.skipif(not OPENCL_AVAILABLE, reason="OpenCL not available")
    def test_median_blur_opencl(self, test_image):
        """Test OpenCL median blur."""
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.OPENCL)
        result = preprocessor.median_blur(test_image, ksize=5)

        assert result.shape == test_image.shape
        assert result.dtype == test_image.dtype

    def test_morphology_cpu(self, test_image):
        """Test CPU morphological operations."""
        import cv2
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CPU)
        kernel = np.ones((3, 3), np.uint8)
        result = preprocessor.morphology(test_image, cv2.MORPH_CLOSE, kernel)

        assert result.shape == test_image.shape
        assert result.dtype == test_image.dtype

    @pytest.mark.skipif(not OPENCL_AVAILABLE, reason="OpenCL not available")
    def test_morphology_opencl(self, test_image):
        """Test OpenCL morphological operations."""
        import cv2
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.OPENCL)
        kernel = np.ones((3, 3), np.uint8)
        result = preprocessor.morphology(test_image, cv2.MORPH_CLOSE, kernel)

        assert result.shape == test_image.shape
        assert result.dtype == test_image.dtype

    def test_perspective_correction_cpu(self, test_image):
        """Test CPU perspective correction."""
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CPU)

        # Define source and destination points for perspective transform
        src_points = np.array([[0, 0], [640, 0], [640, 480], [0, 480]], dtype=np.float32)
        # Slight skew
        dst_points = np.array([[50, 0], [590, 0], [640, 480], [0, 480]], dtype=np.float32)

        result = preprocessor.perspective_correction(
            test_image, src_points, dst_points, (640, 480)
        )

        assert result.shape == test_image.shape
        assert result.dtype == test_image.dtype

    @pytest.mark.skipif(not OPENCL_AVAILABLE, reason="OpenCL not available")
    def test_perspective_correction_opencl(self, test_image):
        """Test OpenCL perspective correction."""
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.OPENCL)

        src_points = np.array([[0, 0], [640, 0], [640, 480], [0, 480]], dtype=np.float32)
        dst_points = np.array([[50, 0], [590, 0], [640, 480], [0, 480]], dtype=np.float32)

        result = preprocessor.perspective_correction(
            test_image, src_points, dst_points, (640, 480)
        )

        assert result.shape == test_image.shape
        assert result.dtype == test_image.dtype


class TestAccuracyParity:
    """Test that GPU and CPU implementations produce similar results."""

    @pytest.fixture
    def test_image(self) -> np.ndarray:
        """Create consistent test image."""
        np.random.seed(42)
        return np.random.randint(50, 200, (480, 640), dtype=np.uint8)

    def test_clahe_parity(self, test_image):
        """Test CLAHE produces similar results across accelerators."""
        cpu_preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CPU)
        cpu_result = cpu_preprocessor.clahe(test_image)

        # Test against available accelerators
        if OPENCL_AVAILABLE:
            opencl_preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.OPENCL)
            opencl_result = opencl_preprocessor.clahe(test_image)

            # Results should be very similar (allow small numerical differences)
            diff = np.abs(cpu_result.astype(float) - opencl_result.astype(float))
            assert diff.mean() < 5.0  # Average difference < 5 intensity levels

        if CUDA_AVAILABLE:
            cuda_preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CUDA)
            cuda_result = cuda_preprocessor.clahe(test_image)

            diff = np.abs(cpu_result.astype(float) - cuda_result.astype(float))
            assert diff.mean() < 5.0

    def test_gaussian_blur_parity(self, test_image):
        """Test Gaussian blur produces similar results."""
        cpu_preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CPU)
        cpu_result = cpu_preprocessor.gaussian_blur(test_image, ksize=(5, 5))

        if OPENCL_AVAILABLE:
            opencl_preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.OPENCL)
            opencl_result = opencl_preprocessor.gaussian_blur(test_image, ksize=(5, 5))

            diff = np.abs(cpu_result.astype(float) - opencl_result.astype(float))
            assert diff.mean() < 5.0

        if CUDA_AVAILABLE:
            cuda_preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CUDA)
            cuda_result = cuda_preprocessor.gaussian_blur(test_image, ksize=(5, 5))

            diff = np.abs(cpu_result.astype(float) - cuda_result.astype(float))
            assert diff.mean() < 5.0

    def test_full_pipeline_parity(self, test_image):
        """Test full pipeline produces consistent results."""
        cpu_preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CPU)
        cpu_result = cpu_preprocessor.full_preprocessing_pipeline(test_image)

        if OPENCL_AVAILABLE:
            opencl_preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.OPENCL)
            opencl_result = opencl_preprocessor.full_preprocessing_pipeline(test_image)

            # Allow larger tolerance for full pipeline (multiple operations compound)
            diff = np.abs(cpu_result.astype(float) - opencl_result.astype(float))
            assert diff.mean() < 12.0  # Slightly higher tolerance due to compounding operations


class TestPerformanceMetrics:
    """Test performance tracking."""

    @pytest.fixture
    def test_image(self) -> np.ndarray:
        """Create test image."""
        return np.random.randint(0, 255, (480, 640), dtype=np.uint8)

    def test_metrics_recording(self, test_image):
        """Test that metrics are recorded."""
        preprocessor = GPUPreprocessor()
        preprocessor.clear_metrics()

        # Run some operations
        preprocessor.clahe(test_image)
        preprocessor.gaussian_blur(test_image)

        assert len(preprocessor.metrics) >= 2

    def test_performance_summary(self, test_image):
        """Test performance summary generation."""
        preprocessor = GPUPreprocessor()
        preprocessor.clear_metrics()

        # Run operations
        for _ in range(3):
            preprocessor.clahe(test_image)
            preprocessor.gaussian_blur(test_image)

        summary = preprocessor.get_performance_summary()

        assert 'accelerator' in summary
        assert 'total_operations' in summary
        assert 'operations' in summary
        assert summary['total_operations'] >= 6

        # Check operation stats
        if 'clahe' in summary['operations']:
            clahe_stats = summary['operations']['clahe']
            assert 'count' in clahe_stats
            assert 'avg_time_ms' in clahe_stats
            assert clahe_stats['count'] >= 3

    def test_performance_metric_fields(self, test_image):
        """Test performance metric data structure."""
        preprocessor = GPUPreprocessor()
        preprocessor.clear_metrics()

        preprocessor.clahe(test_image)

        assert len(preprocessor.metrics) > 0
        metric = preprocessor.metrics[0]

        assert isinstance(metric, PerformanceMetrics)
        assert metric.operation == 'clahe'
        assert metric.accelerator in [AcceleratorType.CPU, AcceleratorType.OPENCL, AcceleratorType.CUDA]
        assert metric.execution_time_ms > 0
        assert metric.input_size == (480, 640)
        assert metric.throughput_mpx_per_sec > 0


class TestFullPipeline:
    """Test the complete preprocessing pipeline."""

    @pytest.fixture
    def test_image_grayscale(self) -> np.ndarray:
        """Create grayscale test image."""
        return np.random.randint(50, 200, (480, 640), dtype=np.uint8)

    @pytest.fixture
    def test_image_color(self) -> np.ndarray:
        """Create color test image."""
        return np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)

    def test_pipeline_grayscale(self, test_image_grayscale):
        """Test pipeline with grayscale input."""
        preprocessor = GPUPreprocessor()
        result = preprocessor.full_preprocessing_pipeline(test_image_grayscale, for_ocr=True)

        assert result.shape == test_image_grayscale.shape
        assert result.dtype == test_image_grayscale.dtype

    def test_pipeline_color(self, test_image_color):
        """Test pipeline with color input (converts to grayscale)."""
        preprocessor = GPUPreprocessor()
        result = preprocessor.full_preprocessing_pipeline(test_image_color, for_ocr=True)

        # Should convert to grayscale
        assert len(result.shape) == 2
        assert result.shape[0] == test_image_color.shape[0]
        assert result.shape[1] == test_image_color.shape[1]

    def test_pipeline_for_ocr(self, test_image_grayscale):
        """Test pipeline optimized for OCR."""
        preprocessor = GPUPreprocessor()
        result = preprocessor.full_preprocessing_pipeline(test_image_grayscale, for_ocr=True)

        assert result.shape == test_image_grayscale.shape

    def test_pipeline_for_visual(self, test_image_grayscale):
        """Test pipeline optimized for visual quality."""
        preprocessor = GPUPreprocessor()
        result = preprocessor.full_preprocessing_pipeline(test_image_grayscale, for_ocr=False)

        assert result.shape == test_image_grayscale.shape

    def test_pipeline_performance(self, test_image_grayscale):
        """Test that full pipeline completes in reasonable time."""
        preprocessor = GPUPreprocessor()

        start = time.time()
        result = preprocessor.full_preprocessing_pipeline(test_image_grayscale)
        elapsed = time.time() - start

        # Should complete in < 1 second for 480p image
        assert elapsed < 1.0
        assert result.shape == test_image_grayscale.shape


class TestErrorHandling:
    """Test error handling and fallbacks."""

    @pytest.fixture
    def test_image(self) -> np.ndarray:
        """Create test image."""
        return np.random.randint(0, 255, (480, 640), dtype=np.uint8)

    def test_invalid_image_shape(self):
        """Test handling of invalid image shapes."""
        preprocessor = GPUPreprocessor()

        # Empty image
        empty = np.array([])
        # Should not crash, but may return original or empty
        try:
            result = preprocessor.clahe(empty)
        except Exception:
            pass  # Acceptable to raise exception for invalid input

    def test_cpu_fallback(self, test_image):
        """Test that operations fall back to CPU on error."""
        # This is hard to test directly, but we can verify CPU version works
        preprocessor = GPUPreprocessor(force_accelerator=AcceleratorType.CPU)

        # All operations should work on CPU
        result1 = preprocessor.denoise(test_image)
        result2 = preprocessor.clahe(test_image)
        result3 = preprocessor.gaussian_blur(test_image)
        result4 = preprocessor.median_blur(test_image)

        assert result1.shape == test_image.shape
        assert result2.shape == test_image.shape
        assert result3.shape == test_image.shape
        assert result4.shape == test_image.shape


class TestBenchmarking:
    """Test benchmarking functionality."""

    def test_benchmark_accelerators(self):
        """Test full accelerator benchmark."""
        results = benchmark_accelerators()

        assert 'system' in results
        assert 'benchmarks' in results

        # Should have system info
        system = results['system']
        assert 'cuda_available' in system
        assert 'opencl_available' in system
        assert 'cpu' in system

        # Should have at least CPU benchmark
        assert 'cpu' in results['benchmarks']

        # CPU benchmark should have results for test sizes
        cpu_results = results['benchmarks']['cpu']
        if 'error' not in cpu_results:
            assert '480p' in cpu_results or '720p' in cpu_results

    def test_benchmark_operations(self):
        """Test that benchmark includes expected operations."""
        results = benchmark_accelerators()

        cpu_results = results['benchmarks'].get('cpu', {})
        if 'error' in cpu_results:
            pytest.skip("CPU benchmark failed")

        # Check for expected operations
        for size_label in ['480p', '720p', '1080p']:
            if size_label in cpu_results:
                ops = cpu_results[size_label]
                assert 'denoise' in ops or 'clahe' in ops or 'full_pipeline' in ops


class TestSingletonPattern:
    """Test singleton instance management."""

    def test_singleton_instance(self):
        """Test that get_gpu_preprocessor returns singleton."""
        instance1 = get_gpu_preprocessor()
        instance2 = get_gpu_preprocessor()

        assert instance1 is instance2

    def test_singleton_metrics_persistence(self):
        """Test that metrics persist across singleton calls."""
        preprocessor = get_gpu_preprocessor()
        preprocessor.clear_metrics()

        test_img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        preprocessor.clahe(test_img)

        initial_count = len(preprocessor.metrics)

        # Get instance again
        preprocessor2 = get_gpu_preprocessor()
        assert len(preprocessor2.metrics) == initial_count


class TestIntegration:
    """Integration tests with realistic poker table images."""

    def test_poker_table_preprocessing(self):
        """Test preprocessing on simulated poker table region."""
        # Simulate a poker table text region (pot size, stack, etc.)
        # Create image with text-like patterns
        img = np.ones((80, 200), dtype=np.uint8) * 200  # Light background

        # Add some noise
        noise = np.random.randint(-30, 30, img.shape, dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        # Add dark "text" regions
        img[30:50, 50:150] = 50

        preprocessor = GPUPreprocessor()
        result = preprocessor.full_preprocessing_pipeline(img, for_ocr=True)

        # Result should be same size
        assert result.shape == img.shape

        # Result should have better contrast
        assert result.std() >= img.std() * 0.8

    def test_high_resolution_performance(self):
        """Test performance with high resolution image (1080p)."""
        img = np.random.randint(0, 255, (1080, 1920), dtype=np.uint8)

        preprocessor = GPUPreprocessor()
        start = time.time()
        result = preprocessor.full_preprocessing_pipeline(img)
        elapsed = time.time() - start

        assert result.shape == img.shape
        # Should complete in reasonable time (< 2 seconds for 1080p)
        assert elapsed < 2.0

        # Log performance
        print(f"\n1080p preprocessing: {elapsed*1000:.2f}ms")


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '-s'])
