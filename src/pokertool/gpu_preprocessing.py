#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GPU Accelerated Preprocessing Pipeline
=======================================

SCRAPE-013: GPU Accelerated Preprocessing Pipeline

Reduces preprocessing latency for high resolution captures while improving
colour and geometric normalisation.

Features:
- OpenCL/CUDA acceleration for heavy operations
- Automatic fallback to CPU when GPU unavailable
- Runtime capability detection
- Performance monitoring and profiling
- Operations: blur, CLAHE, denoise, deskew, perspective correction

Module: pokertool.gpu_preprocessing
Version: v45.0.0
Author: PokerTool Development Team
"""

__version__ = '45.0.0'
__author__ = 'PokerTool Development Team'

import time
import logging
import platform
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

# Try to import dependencies
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None
    logger.warning("OpenCV not available")

# Try to import GPU acceleration
CUDA_AVAILABLE = False
OPENCL_AVAILABLE = False

if CV2_AVAILABLE:
    try:
        # Check for CUDA support
        if cv2.cuda.getCudaEnabledDeviceCount() > 0:
            CUDA_AVAILABLE = True
            logger.info(f"CUDA available: {cv2.cuda.getCudaEnabledDeviceCount()} device(s)")
    except (AttributeError, cv2.error):
        logger.debug("CUDA not available via OpenCV")

    try:
        # Check for OpenCL support via UMat
        # UMat uses OpenCL transparently if available
        test_umat = cv2.UMat(np.zeros((10, 10), dtype=np.uint8))
        OPENCL_AVAILABLE = True
        logger.info("OpenCL available via cv2.UMat")
    except Exception:
        logger.debug("OpenCL not available via cv2.UMat")


class AcceleratorType(Enum):
    """Types of hardware acceleration available."""
    CUDA = 'cuda'
    OPENCL = 'opencl'
    CPU = 'cpu'


@dataclass
class PerformanceMetrics:
    """Performance metrics for preprocessing operations."""
    operation: str
    accelerator: AcceleratorType
    execution_time_ms: float
    input_size: Tuple[int, int]
    throughput_mpx_per_sec: float  # Megapixels per second

    def __str__(self):
        return (f"{self.operation} ({self.accelerator.value}): "
                f"{self.execution_time_ms:.2f}ms, "
                f"{self.throughput_mpx_per_sec:.1f} MPx/s")


@dataclass
class GPUCapabilities:
    """Information about available GPU acceleration."""
    cuda_available: bool
    opencl_available: bool
    preferred_accelerator: AcceleratorType
    cuda_device_count: int = 0
    cuda_device_name: str = ""
    opencl_device_name: str = ""
    cpu_info: str = ""

    def __post_init__(self):
        """Gather system information."""
        self.cpu_info = platform.processor() or platform.machine()

        if self.cuda_available and cv2:
            try:
                self.cuda_device_count = cv2.cuda.getCudaEnabledDeviceCount()
                if self.cuda_device_count > 0:
                    # Get first device name
                    props = cv2.cuda.DeviceInfo(0)
                    self.cuda_device_name = props.name()
            except Exception as e:
                logger.debug(f"Failed to get CUDA device info: {e}")

        if self.opencl_available:
            self.opencl_device_name = "OpenCL (via cv2.UMat)"

    def summary(self) -> str:
        """Get human-readable summary."""
        lines = [
            "GPU Preprocessing Capabilities:",
            f"  Preferred: {self.preferred_accelerator.value.upper()}",
            f"  CUDA: {'✓' if self.cuda_available else '✗'}",
            f"  OpenCL: {'✓' if self.opencl_available else '✗'}",
            f"  CPU: {self.cpu_info}",
        ]

        if self.cuda_available and self.cuda_device_name:
            lines.append(f"  CUDA Device: {self.cuda_device_name}")

        if self.opencl_available and self.opencl_device_name:
            lines.append(f"  OpenCL Device: {self.opencl_device_name}")

        return "\n".join(lines)


class GPUPreprocessor:
    """
    GPU-accelerated image preprocessing for poker table scraping.

    Automatically selects best available acceleration (CUDA > OpenCL > CPU)
    and provides fallbacks for all operations.
    """

    def __init__(self, force_accelerator: Optional[AcceleratorType] = None):
        """
        Initialize GPU preprocessor.

        Args:
            force_accelerator: Force specific accelerator (for testing)
        """
        if not CV2_AVAILABLE:
            raise RuntimeError("OpenCV not available. Install opencv-python or opencv-contrib-python")

        # Detect capabilities
        self.capabilities = self._detect_capabilities(force_accelerator)

        # Performance tracking
        self.metrics: List[PerformanceMetrics] = []
        self.enable_profiling = True

        logger.info(f"GPU Preprocessor initialized: {self.capabilities.preferred_accelerator.value}")

    def _detect_capabilities(self, force: Optional[AcceleratorType]) -> GPUCapabilities:
        """Detect available GPU acceleration."""
        if force:
            # Force specific accelerator
            caps = GPUCapabilities(
                cuda_available=(force == AcceleratorType.CUDA),
                opencl_available=(force == AcceleratorType.OPENCL),
                preferred_accelerator=force
            )
        else:
            # Auto-detect best available
            preferred = AcceleratorType.CPU
            if CUDA_AVAILABLE:
                preferred = AcceleratorType.CUDA
            elif OPENCL_AVAILABLE:
                preferred = AcceleratorType.OPENCL

            caps = GPUCapabilities(
                cuda_available=CUDA_AVAILABLE,
                opencl_available=OPENCL_AVAILABLE,
                preferred_accelerator=preferred
            )

        return caps

    def _record_metric(self, operation: str, exec_time: float, size: Tuple[int, int]):
        """Record performance metric."""
        if not self.enable_profiling:
            return

        # Calculate throughput (megapixels per second)
        pixels = size[0] * size[1]
        mpx = pixels / 1_000_000
        throughput = mpx / max(exec_time, 1e-6)

        metric = PerformanceMetrics(
            operation=operation,
            accelerator=self.capabilities.preferred_accelerator,
            execution_time_ms=exec_time * 1000,
            input_size=size,
            throughput_mpx_per_sec=throughput
        )

        self.metrics.append(metric)
        logger.debug(str(metric))

    def denoise(self, image: np.ndarray, h: int = 10) -> np.ndarray:
        """
        Denoise image using Non-Local Means Denoising.

        Args:
            image: Input image (grayscale or color)
            h: Filter strength

        Returns:
            Denoised image
        """
        start = time.time()

        try:
            if self.capabilities.preferred_accelerator == AcceleratorType.CUDA:
                # CUDA version
                result = self._denoise_cuda(image, h)
            elif self.capabilities.preferred_accelerator == AcceleratorType.OPENCL:
                # OpenCL version via UMat
                result = self._denoise_opencl(image, h)
            else:
                # CPU fallback
                result = self._denoise_cpu(image, h)

            self._record_metric('denoise', time.time() - start, image.shape[:2])
            return result

        except Exception as e:
            logger.warning(f"GPU denoise failed, falling back to CPU: {e}")
            return self._denoise_cpu(image, h)

    def _denoise_cuda(self, image: np.ndarray, h: int) -> np.ndarray:
        """CUDA-accelerated denoising."""
        # Upload to GPU
        gpu_img = cv2.cuda_GpuMat()
        gpu_img.upload(image)

        # Create denoiser
        if len(image.shape) == 3:
            # Color image
            denoiser = cv2.cuda.createNonLocalMeansDenoising(h, 7, 21)
        else:
            # Grayscale
            denoiser = cv2.cuda.createNonLocalMeansDenoising(h, 7, 21)

        # Process on GPU
        gpu_result = denoiser.process(gpu_img)

        # Download result
        return gpu_result.download()

    def _denoise_opencl(self, image: np.ndarray, h: int) -> np.ndarray:
        """OpenCL-accelerated denoising via UMat."""
        # Upload to OpenCL
        umat_img = cv2.UMat(image)

        # Process (OpenCL acceleration automatic with UMat)
        if len(image.shape) == 3:
            result_umat = cv2.fastNlMeansDenoisingColored(umat_img, None, h, h, 7, 21)
        else:
            result_umat = cv2.fastNlMeansDenoising(umat_img, None, h, 7, 21)

        # Download result
        return result_umat.get()

    def _denoise_cpu(self, image: np.ndarray, h: int) -> np.ndarray:
        """CPU denoising."""
        if len(image.shape) == 3:
            return cv2.fastNlMeansDenoisingColored(image, None, h, h, 7, 21)
        else:
            return cv2.fastNlMeansDenoising(image, None, h, 7, 21)

    def clahe(self, image: np.ndarray, clip_limit: float = 2.0,
              tile_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
        """
        Apply Contrast Limited Adaptive Histogram Equalization.

        Args:
            image: Input grayscale image
            clip_limit: Clipping limit for contrast
            tile_size: Size of tiles for histogram equalization

        Returns:
            Enhanced image
        """
        start = time.time()

        try:
            if self.capabilities.preferred_accelerator == AcceleratorType.CUDA:
                result = self._clahe_cuda(image, clip_limit, tile_size)
            elif self.capabilities.preferred_accelerator == AcceleratorType.OPENCL:
                result = self._clahe_opencl(image, clip_limit, tile_size)
            else:
                result = self._clahe_cpu(image, clip_limit, tile_size)

            self._record_metric('clahe', time.time() - start, image.shape[:2])
            return result

        except Exception as e:
            logger.warning(f"GPU CLAHE failed, falling back to CPU: {e}")
            return self._clahe_cpu(image, clip_limit, tile_size)

    def _clahe_cuda(self, image: np.ndarray, clip_limit: float,
                     tile_size: Tuple[int, int]) -> np.ndarray:
        """CUDA-accelerated CLAHE."""
        # Upload to GPU
        gpu_img = cv2.cuda_GpuMat()
        gpu_img.upload(image)

        # Create CLAHE filter
        clahe = cv2.cuda.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_size)

        # Apply on GPU
        gpu_result = clahe.apply(gpu_img, cv2.cuda_Stream.Null())

        # Download
        return gpu_result.download()

    def _clahe_opencl(self, image: np.ndarray, clip_limit: float,
                      tile_size: Tuple[int, int]) -> np.ndarray:
        """OpenCL-accelerated CLAHE via UMat."""
        # Upload to OpenCL
        umat_img = cv2.UMat(image)

        # Create and apply CLAHE (automatic OpenCL acceleration)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_size)
        result_umat = clahe.apply(umat_img)

        # Download
        return result_umat.get()

    def _clahe_cpu(self, image: np.ndarray, clip_limit: float,
                   tile_size: Tuple[int, int]) -> np.ndarray:
        """CPU CLAHE."""
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_size)
        return clahe.apply(image)

    def gaussian_blur(self, image: np.ndarray, ksize: Tuple[int, int] = (5, 5),
                      sigma: float = 0) -> np.ndarray:
        """
        Apply Gaussian blur.

        Args:
            image: Input image
            ksize: Kernel size (must be odd)
            sigma: Standard deviation

        Returns:
            Blurred image
        """
        start = time.time()

        try:
            if self.capabilities.preferred_accelerator == AcceleratorType.CUDA:
                result = self._gaussian_blur_cuda(image, ksize, sigma)
            elif self.capabilities.preferred_accelerator == AcceleratorType.OPENCL:
                result = self._gaussian_blur_opencl(image, ksize, sigma)
            else:
                result = self._gaussian_blur_cpu(image, ksize, sigma)

            self._record_metric('gaussian_blur', time.time() - start, image.shape[:2])
            return result

        except Exception as e:
            logger.warning(f"GPU Gaussian blur failed, falling back to CPU: {e}")
            return self._gaussian_blur_cpu(image, ksize, sigma)

    def _gaussian_blur_cuda(self, image: np.ndarray, ksize: Tuple[int, int],
                            sigma: float) -> np.ndarray:
        """CUDA Gaussian blur."""
        gpu_img = cv2.cuda_GpuMat()
        gpu_img.upload(image)

        # Create Gaussian filter
        gaussian_filter = cv2.cuda.createGaussianFilter(
            gpu_img.type(), -1, ksize, sigma
        )

        # Apply filter
        gpu_result = gaussian_filter.apply(gpu_img)

        return gpu_result.download()

    def _gaussian_blur_opencl(self, image: np.ndarray, ksize: Tuple[int, int],
                               sigma: float) -> np.ndarray:
        """OpenCL Gaussian blur."""
        umat_img = cv2.UMat(image)
        result_umat = cv2.GaussianBlur(umat_img, ksize, sigma)
        return result_umat.get()

    def _gaussian_blur_cpu(self, image: np.ndarray, ksize: Tuple[int, int],
                           sigma: float) -> np.ndarray:
        """CPU Gaussian blur."""
        return cv2.GaussianBlur(image, ksize, sigma)

    def median_blur(self, image: np.ndarray, ksize: int = 5) -> np.ndarray:
        """
        Apply median blur (noise reduction).

        Args:
            image: Input image
            ksize: Kernel size (must be odd)

        Returns:
            Blurred image
        """
        start = time.time()

        try:
            if self.capabilities.preferred_accelerator == AcceleratorType.CUDA:
                result = self._median_blur_cuda(image, ksize)
            elif self.capabilities.preferred_accelerator == AcceleratorType.OPENCL:
                result = self._median_blur_opencl(image, ksize)
            else:
                result = self._median_blur_cpu(image, ksize)

            self._record_metric('median_blur', time.time() - start, image.shape[:2])
            return result

        except Exception as e:
            logger.warning(f"GPU median blur failed, falling back to CPU: {e}")
            return self._median_blur_cpu(image, ksize)

    def _median_blur_cuda(self, image: np.ndarray, ksize: int) -> np.ndarray:
        """CUDA median blur."""
        gpu_img = cv2.cuda_GpuMat()
        gpu_img.upload(image)

        # Create median filter
        median_filter = cv2.cuda.createMedianFilter(gpu_img.type(), ksize)

        # Apply
        gpu_result = median_filter.apply(gpu_img)

        return gpu_result.download()

    def _median_blur_opencl(self, image: np.ndarray, ksize: int) -> np.ndarray:
        """OpenCL median blur."""
        umat_img = cv2.UMat(image)
        result_umat = cv2.medianBlur(umat_img, ksize)
        return result_umat.get()

    def _median_blur_cpu(self, image: np.ndarray, ksize: int) -> np.ndarray:
        """CPU median blur."""
        return cv2.medianBlur(image, ksize)

    def morphology(self, image: np.ndarray, operation: int,
                   kernel: np.ndarray) -> np.ndarray:
        """
        Apply morphological operation.

        Args:
            image: Input image
            operation: Morphology operation (cv2.MORPH_*)
            kernel: Structuring element

        Returns:
            Processed image
        """
        start = time.time()

        try:
            if self.capabilities.preferred_accelerator == AcceleratorType.CUDA:
                result = self._morphology_cuda(image, operation, kernel)
            elif self.capabilities.preferred_accelerator == AcceleratorType.OPENCL:
                result = self._morphology_opencl(image, operation, kernel)
            else:
                result = self._morphology_cpu(image, operation, kernel)

            self._record_metric('morphology', time.time() - start, image.shape[:2])
            return result

        except Exception as e:
            logger.warning(f"GPU morphology failed, falling back to CPU: {e}")
            return self._morphology_cpu(image, operation, kernel)

    def _morphology_cuda(self, image: np.ndarray, operation: int,
                         kernel: np.ndarray) -> np.ndarray:
        """CUDA morphology."""
        gpu_img = cv2.cuda_GpuMat()
        gpu_img.upload(image)

        # Create morphology filter
        morph_filter = cv2.cuda.createMorphologyFilter(
            operation, gpu_img.type(), kernel
        )

        # Apply
        gpu_result = morph_filter.apply(gpu_img)

        return gpu_result.download()

    def _morphology_opencl(self, image: np.ndarray, operation: int,
                           kernel: np.ndarray) -> np.ndarray:
        """OpenCL morphology."""
        umat_img = cv2.UMat(image)
        result_umat = cv2.morphologyEx(umat_img, operation, kernel)
        return result_umat.get()

    def _morphology_cpu(self, image: np.ndarray, operation: int,
                        kernel: np.ndarray) -> np.ndarray:
        """CPU morphology."""
        return cv2.morphologyEx(image, operation, kernel)

    def perspective_correction(self, image: np.ndarray,
                               src_points: np.ndarray,
                               dst_points: np.ndarray,
                               output_size: Tuple[int, int]) -> np.ndarray:
        """
        Apply perspective correction (deskewing).

        Args:
            image: Input image
            src_points: Source quadrilateral points (4x2)
            dst_points: Destination rectangle points (4x2)
            output_size: Output image size (width, height)

        Returns:
            Corrected image
        """
        start = time.time()

        try:
            if self.capabilities.preferred_accelerator == AcceleratorType.CUDA:
                result = self._perspective_cuda(image, src_points, dst_points, output_size)
            elif self.capabilities.preferred_accelerator == AcceleratorType.OPENCL:
                result = self._perspective_opencl(image, src_points, dst_points, output_size)
            else:
                result = self._perspective_cpu(image, src_points, dst_points, output_size)

            self._record_metric('perspective', time.time() - start, image.shape[:2])
            return result

        except Exception as e:
            logger.warning(f"GPU perspective failed, falling back to CPU: {e}")
            return self._perspective_cpu(image, src_points, dst_points, output_size)

    def _perspective_cuda(self, image: np.ndarray, src_points: np.ndarray,
                          dst_points: np.ndarray, output_size: Tuple[int, int]) -> np.ndarray:
        """CUDA perspective correction."""
        # Get transformation matrix
        M = cv2.getPerspectiveTransform(src_points.astype(np.float32),
                                        dst_points.astype(np.float32))

        # Upload to GPU
        gpu_img = cv2.cuda_GpuMat()
        gpu_img.upload(image)

        # Apply warp perspective on GPU
        gpu_result = cv2.cuda.warpPerspective(gpu_img, M, output_size)

        return gpu_result.download()

    def _perspective_opencl(self, image: np.ndarray, src_points: np.ndarray,
                            dst_points: np.ndarray, output_size: Tuple[int, int]) -> np.ndarray:
        """OpenCL perspective correction."""
        # Get transformation matrix
        M = cv2.getPerspectiveTransform(src_points.astype(np.float32),
                                        dst_points.astype(np.float32))

        # Upload to OpenCL
        umat_img = cv2.UMat(image)

        # Apply warp
        result_umat = cv2.warpPerspective(umat_img, M, output_size)

        return result_umat.get()

    def _perspective_cpu(self, image: np.ndarray, src_points: np.ndarray,
                         dst_points: np.ndarray, output_size: Tuple[int, int]) -> np.ndarray:
        """CPU perspective correction."""
        M = cv2.getPerspectiveTransform(src_points.astype(np.float32),
                                        dst_points.astype(np.float32))
        return cv2.warpPerspective(image, M, output_size)

    def full_preprocessing_pipeline(self, image: np.ndarray,
                                     for_ocr: bool = True) -> np.ndarray:
        """
        Complete preprocessing pipeline optimized for poker OCR.

        Args:
            image: Input image (color or grayscale)
            for_ocr: Optimize for OCR (True) or visual quality (False)

        Returns:
            Preprocessed image
        """
        start = time.time()

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Step 1: Denoise
        denoised = self.denoise(gray, h=10)

        # Step 2: CLAHE for contrast enhancement
        enhanced = self.clahe(denoised, clip_limit=2.0, tile_size=(8, 8))

        if for_ocr:
            # Step 3: Slight blur to connect broken characters
            blurred = self.gaussian_blur(enhanced, ksize=(3, 3), sigma=0.5)

            # Step 4: Morphological closing to clean up
            kernel = np.ones((2, 2), np.uint8)
            final = self.morphology(blurred, cv2.MORPH_CLOSE, kernel)
        else:
            # Just sharpen for visual quality
            final = enhanced

        total_time = time.time() - start
        self._record_metric('full_pipeline', total_time, image.shape[:2])

        logger.debug(f"Full preprocessing completed in {total_time*1000:.2f}ms")

        return final

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance statistics summary."""
        if not self.metrics:
            return {'message': 'No metrics recorded yet'}

        # Group by operation
        ops = {}
        for metric in self.metrics:
            if metric.operation not in ops:
                ops[metric.operation] = []
            ops[metric.operation].append(metric)

        summary = {
            'accelerator': self.capabilities.preferred_accelerator.value,
            'total_operations': len(self.metrics),
            'operations': {}
        }

        for op_name, op_metrics in ops.items():
            times = [m.execution_time_ms for m in op_metrics]
            throughputs = [m.throughput_mpx_per_sec for m in op_metrics]

            summary['operations'][op_name] = {
                'count': len(op_metrics),
                'avg_time_ms': sum(times) / len(times),
                'min_time_ms': min(times),
                'max_time_ms': max(times),
                'avg_throughput_mpx_per_sec': sum(throughputs) / len(throughputs)
            }

        return summary

    def clear_metrics(self):
        """Clear performance metrics."""
        self.metrics.clear()


# Singleton instance
_gpu_preprocessor: Optional[GPUPreprocessor] = None


def get_gpu_preprocessor(force_accelerator: Optional[AcceleratorType] = None) -> GPUPreprocessor:
    """Get singleton GPU preprocessor instance."""
    global _gpu_preprocessor
    if _gpu_preprocessor is None:
        _gpu_preprocessor = GPUPreprocessor(force_accelerator)
    return _gpu_preprocessor


def benchmark_accelerators() -> Dict[str, Any]:
    """
    Benchmark all available accelerators.

    Returns:
        Dictionary with benchmark results
    """
    results = {
        'system': {
            'cuda_available': CUDA_AVAILABLE,
            'opencl_available': OPENCL_AVAILABLE,
            'cpu': platform.processor() or platform.machine()
        },
        'benchmarks': {}
    }

    # Test image sizes
    test_sizes = [
        (640, 480, '480p'),
        (1280, 720, '720p'),
        (1920, 1080, '1080p'),
    ]

    # Test each accelerator
    for accel_type in [AcceleratorType.CPU, AcceleratorType.OPENCL, AcceleratorType.CUDA]:
        # Skip if not available
        if accel_type == AcceleratorType.CUDA and not CUDA_AVAILABLE:
            continue
        if accel_type == AcceleratorType.OPENCL and not OPENCL_AVAILABLE:
            continue

        try:
            preprocessor = GPUPreprocessor(force_accelerator=accel_type)
            preprocessor.enable_profiling = False  # Manual timing

            accel_results = {}

            for width, height, label in test_sizes:
                # Create test image
                test_img = np.random.randint(0, 255, (height, width), dtype=np.uint8)

                # Benchmark operations
                ops_times = {}

                # Denoise
                start = time.time()
                _ = preprocessor.denoise(test_img, h=10)
                ops_times['denoise'] = (time.time() - start) * 1000

                # CLAHE
                start = time.time()
                _ = preprocessor.clahe(test_img)
                ops_times['clahe'] = (time.time() - start) * 1000

                # Gaussian blur
                start = time.time()
                _ = preprocessor.gaussian_blur(test_img)
                ops_times['gaussian_blur'] = (time.time() - start) * 1000

                # Full pipeline
                start = time.time()
                _ = preprocessor.full_preprocessing_pipeline(test_img)
                ops_times['full_pipeline'] = (time.time() - start) * 1000

                accel_results[label] = ops_times

            results['benchmarks'][accel_type.value] = accel_results

        except Exception as e:
            logger.error(f"Benchmark failed for {accel_type.value}: {e}")
            results['benchmarks'][accel_type.value] = {'error': str(e)}

    return results


if __name__ == '__main__':
    # Test GPU preprocessing
    print("=" * 70)
    print("GPU Accelerated Preprocessing Pipeline")
    print("=" * 70)

    if not CV2_AVAILABLE:
        print("❌ OpenCV not available")
        exit(1)

    # Initialize preprocessor
    preprocessor = get_gpu_preprocessor()

    # Print capabilities
    print("\n" + preprocessor.capabilities.summary())

    # Run benchmarks
    print("\n" + "=" * 70)
    print("Running Benchmarks...")
    print("=" * 70)

    benchmark_results = benchmark_accelerators()

    print("\nBenchmark Results:")
    for accel_name, accel_results in benchmark_results['benchmarks'].items():
        print(f"\n{accel_name.upper()}:")
        if 'error' in accel_results:
            print(f"  Error: {accel_results['error']}")
        else:
            for size_label, ops in accel_results.items():
                print(f"  {size_label}:")
                for op_name, time_ms in ops.items():
                    print(f"    {op_name}: {time_ms:.2f}ms")

    print("\n" + "=" * 70)
    print("✅ GPU Preprocessing Pipeline Ready")
    print("=" * 70)
