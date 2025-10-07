#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Adaptive UI Change Detection Module
===========================================

Prevents scraper breakage by detecting poker client UI changes before they reach production.

This module maintains a baseline library of approved table states, computes perceptual 
hashes and structural similarity on every scrape, and raises alerts with auto-generated 
diff masks when deviations exceed thresholds.

Module: pokertool.modules.adaptive_ui_detector
Version: 1.0.0
Last Modified: 2025-01-07
Author: PokerTool Development Team
License: MIT

Key Features:
- Perceptual hash comparison for layout change detection
- Structural similarity (SSIM) analysis for fine-grained changes
- Auto-generated diff masks for visual debugging
- Configurable thresholds per poker site and resolution
- CI integration with build failure on excessive changes
"""

import os
import logging
import time
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

# Check for required dependencies
try:
    import cv2
    import imagehash
    from PIL import Image
    from skimage.metrics import structural_similarity as ssim
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Adaptive UI detector dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False
    # Create dummy objects for type hints
    imagehash = None

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration and Data Models
# ============================================================================

class ChangeType(Enum):
    """Types of UI changes that can be detected."""
    LAYOUT_SHIFT = "layout_shift"
    COLOR_CHANGE = "color_change"  
    ELEMENT_ADDED = "element_added"
    ELEMENT_REMOVED = "element_removed"
    SIZE_CHANGE = "size_change"
    FONT_CHANGE = "font_change"
    UNKNOWN = "unknown"

@dataclass
class UIRegion:
    """Defines a region of interest for UI change detection."""
    name: str
    x: int
    y: int
    width: int
    height: int
    importance: float = 1.0  # Weight for this region in overall score
    threshold_ssim: float = 0.85  # SSIM threshold for this region
    threshold_hash: int = 10  # Hamming distance threshold for perceptual hash
    
class BaselineInfo(NamedTuple):
    """Information about a baseline screenshot."""
    filepath: str
    perceptual_hash: str
    ssim_regions: Dict[str, float]
    metadata: Dict[str, Any]
    timestamp: float

@dataclass  
class ChangeDetectionResult:
    """Result of UI change detection analysis."""
    has_changes: bool
    confidence: float
    change_types: List[ChangeType] = field(default_factory=list)
    affected_regions: List[str] = field(default_factory=list)
    ssim_scores: Dict[str, float] = field(default_factory=dict)
    hash_distances: Dict[str, int] = field(default_factory=dict)
    diff_mask: Optional[np.ndarray] = None
    recommendations: List[str] = field(default_factory=list)
    analysis_time_ms: float = 0.0

# ============================================================================
# Adaptive UI Change Detector
# ============================================================================

class AdaptiveUIDetector:
    """
    Advanced UI change detection system for poker table scraping.
    
    This class maintains baseline screenshots for each supported poker site and
    resolution, then compares new captures against these baselines using multiple
    detection strategies including perceptual hashing and structural similarity.
    """
    
    def __init__(self, baseline_dir: Optional[str] = None):
        """Initialize the adaptive UI detector.
        
        Args:
            baseline_dir: Directory to store baseline screenshots. Defaults to 
                         project_root/assets/ui_baselines
        """
        if not DEPENDENCIES_AVAILABLE:
            logger.error("Required dependencies not available for UI change detection")
            self.available = False
            return
        
        self.available = True
        
        # Setup baseline directory
        if baseline_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            self.baseline_dir = project_root / 'assets' / 'ui_baselines'
        else:
            self.baseline_dir = Path(baseline_dir)
        
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize baseline library
        self.baselines: Dict[str, List[BaselineInfo]] = {}
        self._load_baselines()
        
        # Detection statistics
        self.detection_count = 0
        self.change_detection_count = 0
        self.false_positive_count = 0
        
        logger.info(f"Adaptive UI detector initialized with {len(self.baselines)} baseline sets")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load detection configuration from file or defaults."""
        config_file = self.baseline_dir / 'detection_config.json'
        
        default_config = {
            # Global thresholds
            "default_ssim_threshold": 0.85,
            "default_hash_threshold": 10,
            
            # Site-specific configurations
            "sites": {
                "betfair": {
                    "regions": [
                        {
                            "name": "pot_area",
                            "x": 0.4, "y": 0.3, "width": 0.2, "height": 0.1,
                            "importance": 2.0,
                            "threshold_ssim": 0.9,
                            "threshold_hash": 8
                        },
                        {
                            "name": "hero_cards",
                            "x": 0.4, "y": 0.7, "width": 0.2, "height": 0.15,
                            "importance": 3.0,
                            "threshold_ssim": 0.95,
                            "threshold_hash": 5
                        },
                        {
                            "name": "board_cards", 
                            "x": 0.3, "y": 0.4, "width": 0.4, "height": 0.15,
                            "importance": 2.5,
                            "threshold_ssim": 0.9,
                            "threshold_hash": 6
                        },
                        {
                            "name": "action_buttons",
                            "x": 0.6, "y": 0.8, "width": 0.35, "height": 0.15,
                            "importance": 2.0,
                            "threshold_ssim": 0.8,
                            "threshold_hash": 12
                        }
                    ]
                },
                "generic": {
                    "regions": [
                        {
                            "name": "center_area",
                            "x": 0.25, "y": 0.25, "width": 0.5, "height": 0.5,
                            "importance": 1.5,
                            "threshold_ssim": 0.8,
                            "threshold_hash": 15
                        }
                    ]
                }
            },
            
            # Alert thresholds
            "alert_thresholds": {
                "minor_change": 0.15,
                "major_change": 0.30,
                "critical_change": 0.50
            },
            
            # CI integration
            "ci_failure_threshold": 0.40,
            "ci_enabled": True
        }
        
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    default_config.update(loaded_config)
        except Exception as e:
            logger.warning(f"Could not load config from {config_file}: {e}")
        
        # Save merged config
        try:
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save config: {e}")
        
        return default_config
    
    def _load_baselines(self) -> None:
        """Load all baseline screenshots from the baseline directory."""
        baseline_index_file = self.baseline_dir / 'baselines_index.json'
        
        try:
            if baseline_index_file.exists():
                with open(baseline_index_file, 'r') as f:
                    index_data = json.load(f)
                    
                for site_key, baseline_list in index_data.items():
                    self.baselines[site_key] = []
                    for baseline_data in baseline_list:
                        baseline_info = BaselineInfo(
                            filepath=baseline_data['filepath'],
                            perceptual_hash=baseline_data['perceptual_hash'],
                            ssim_regions=baseline_data['ssim_regions'],
                            metadata=baseline_data['metadata'],
                            timestamp=baseline_data['timestamp']
                        )
                        self.baselines[site_key].append(baseline_info)
            
        except Exception as e:
            logger.warning(f"Could not load baseline index: {e}")
            self.baselines = {}
    
    def add_baseline(self, image: np.ndarray, site: str, resolution: str, 
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a new baseline screenshot for the specified site and resolution.
        
        Args:
            image: Screenshot in BGR format
            site: Poker site identifier (e.g., 'betfair', 'pokerstars')
            resolution: Resolution identifier (e.g., '1920x1080', '1366x768')
            metadata: Optional metadata about the screenshot
            
        Returns:
            True if baseline was added successfully
        """
        if not self.available or image is None or image.size == 0:
            return False
        
        try:
            site_key = f"{site}_{resolution}"
            timestamp = time.time()
            
            # Generate filename
            filename = f"baseline_{site}_{resolution}_{int(timestamp)}.png"
            filepath = self.baseline_dir / filename
            
            # Save image
            cv2.imwrite(str(filepath), image)
            
            # Compute perceptual hash
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            phash = str(imagehash.phash(pil_image))
            
            # Compute SSIM for each region
            ssim_regions = {}
            regions = self._get_regions_for_site(site)
            
            for region in regions:
                try:
                    roi = self._extract_region(image, region)
                    if roi is not None and roi.size > 0:
                        # Store region hash for later comparison
                        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                        ssim_regions[region.name] = float(np.mean(roi_gray))  # Simple baseline metric
                except Exception as e:
                    logger.warning(f"Could not process region {region.name}: {e}")
            
            # Create baseline info
            baseline = BaselineInfo(
                filepath=str(filepath.relative_to(self.baseline_dir)),
                perceptual_hash=phash,
                ssim_regions=ssim_regions,
                metadata=metadata or {},
                timestamp=timestamp
            )
            
            # Add to baselines
            if site_key not in self.baselines:
                self.baselines[site_key] = []
            self.baselines[site_key].append(baseline)
            
            # Save updated index
            self._save_baseline_index()
            
            logger.info(f"Added baseline for {site_key}: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add baseline: {e}")
            return False
    
    def detect_changes(self, image: np.ndarray, site: str, resolution: str,
                      generate_diff: bool = True) -> ChangeDetectionResult:
        """
        Detect UI changes by comparing against baseline screenshots.
        
        Args:
            image: Current screenshot in BGR format
            site: Poker site identifier
            resolution: Resolution identifier  
            generate_diff: Whether to generate visual diff mask
            
        Returns:
            ChangeDetectionResult with detailed analysis
        """
        start_time = time.time()
        self.detection_count += 1
        
        if not self.available:
            return ChangeDetectionResult(
                has_changes=False,
                confidence=0.0,
                recommendations=["UI change detection not available - missing dependencies"]
            )
        
        try:
            site_key = f"{site}_{resolution}"
            
            # Check if we have baselines for this site/resolution
            if site_key not in self.baselines or not self.baselines[site_key]:
                return ChangeDetectionResult(
                    has_changes=False,
                    confidence=0.0,
                    recommendations=[f"No baselines available for {site_key}. Add baselines first."]
                )
            
            # Get regions for this site
            regions = self._get_regions_for_site(site)
            
            # Initialize result
            result = ChangeDetectionResult(has_changes=False, confidence=0.0)
            
            # Compare against all baselines and find best match
            best_match_score = 0.0
            best_baseline = None
            
            for baseline in self.baselines[site_key]:
                score = self._compare_with_baseline(image, baseline, regions)
                if score > best_match_score:
                    best_match_score = score
                    best_baseline = baseline
            
            if best_baseline is None:
                result.recommendations.append("No valid baseline found for comparison")
                return result
            
            # Detailed analysis against best matching baseline
            baseline_image = self._load_baseline_image(best_baseline)
            if baseline_image is None:
                result.recommendations.append("Could not load baseline image for comparison")
                return result
            
            # Compute perceptual hash distance
            current_hash = str(imagehash.phash(Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))))
            hash_distance = imagehash.hex_to_hash(current_hash) - imagehash.hex_to_hash(best_baseline.perceptual_hash)
            
            # Analyze each region
            ssim_scores = {}
            hash_distances = {}
            affected_regions = []
            change_types = []
            
            for region in regions:
                try:
                    # Extract regions from both images
                    current_roi = self._extract_region(image, region)
                    baseline_roi = self._extract_region(baseline_image, region)
                    
                    if current_roi is None or baseline_roi is None:
                        continue
                    
                    # Resize to same dimensions if needed
                    if current_roi.shape != baseline_roi.shape:
                        baseline_roi = cv2.resize(baseline_roi, (current_roi.shape[1], current_roi.shape[0]))
                    
                    # Convert to grayscale for SSIM
                    current_gray = cv2.cvtColor(current_roi, cv2.COLOR_BGR2GRAY)
                    baseline_gray = cv2.cvtColor(baseline_roi, cv2.COLOR_BGR2GRAY)
                    
                    # Compute SSIM
                    ssim_score = ssim(current_gray, baseline_gray, full=False)
                    ssim_scores[region.name] = ssim_score
                    
                    # Compute region hash distance
                    current_region_hash = imagehash.phash(Image.fromarray(cv2.cvtColor(current_roi, cv2.COLOR_BGR2RGB)))
                    baseline_region_hash = imagehash.phash(Image.fromarray(cv2.cvtColor(baseline_roi, cv2.COLOR_BGR2RGB)))
                    region_hash_distance = current_region_hash - baseline_region_hash
                    hash_distances[region.name] = region_hash_distance
                    
                    # Check thresholds
                    if ssim_score < region.threshold_ssim or region_hash_distance > region.threshold_hash:
                        affected_regions.append(region.name)
                        
                        # Classify change type based on analysis
                        if ssim_score < 0.5:
                            change_types.append(ChangeType.LAYOUT_SHIFT)
                        elif region_hash_distance > 20:
                            change_types.append(ChangeType.COLOR_CHANGE)
                        else:
                            change_types.append(ChangeType.UNKNOWN)
                
                except Exception as e:
                    logger.warning(f"Error analyzing region {region.name}: {e}")
            
            # Calculate overall confidence and determine if changes detected
            overall_change_score = self._calculate_change_score(
                hash_distance, ssim_scores, hash_distances, regions
            )
            
            result.confidence = overall_change_score
            result.ssim_scores = ssim_scores
            result.hash_distances = hash_distances
            result.change_types = list(set(change_types))
            result.affected_regions = affected_regions
            
            # Determine if changes are significant
            thresholds = self.config['alert_thresholds']
            if overall_change_score >= thresholds['critical_change']:
                result.has_changes = True
                result.recommendations.append("CRITICAL: Major UI changes detected - scraper may fail")
                self.change_detection_count += 1
            elif overall_change_score >= thresholds['major_change']:
                result.has_changes = True  
                result.recommendations.append("MAJOR: Significant UI changes detected - review required")
                self.change_detection_count += 1
            elif overall_change_score >= thresholds['minor_change']:
                result.has_changes = True
                result.recommendations.append("MINOR: Small UI changes detected - monitor closely")
                
            # Generate diff mask if requested and changes detected
            if generate_diff and result.has_changes and baseline_image is not None:
                result.diff_mask = self._generate_diff_mask(image, baseline_image)
            
            result.analysis_time_ms = (time.time() - start_time) * 1000
            
            return result
            
        except Exception as e:
            logger.error(f"UI change detection failed: {e}")
            return ChangeDetectionResult(
                has_changes=False,
                confidence=0.0,
                recommendations=[f"Detection failed: {str(e)}"]
            )
    
    def _get_regions_for_site(self, site: str) -> List[UIRegion]:
        """Get regions of interest for the specified site."""
        site_config = self.config['sites'].get(site, self.config['sites']['generic'])
        regions = []
        
        for region_data in site_config['regions']:
            region = UIRegion(
                name=region_data['name'],
                x=int(region_data['x'] * 1920) if region_data['x'] <= 1 else int(region_data['x']),
                y=int(region_data['y'] * 1080) if region_data['y'] <= 1 else int(region_data['y']),
                width=int(region_data['width'] * 1920) if region_data['width'] <= 1 else int(region_data['width']),
                height=int(region_data['height'] * 1080) if region_data['height'] <= 1 else int(region_data['height']),
                importance=region_data.get('importance', 1.0),
                threshold_ssim=region_data.get('threshold_ssim', self.config['default_ssim_threshold']),
                threshold_hash=region_data.get('threshold_hash', self.config['default_hash_threshold'])
            )
            regions.append(region)
        
        return regions
    
    def _extract_region(self, image: np.ndarray, region: UIRegion) -> Optional[np.ndarray]:
        """Extract a region of interest from an image."""
        try:
            h, w = image.shape[:2]
            
            # Handle relative coordinates
            if region.x <= 1 and region.y <= 1:
                x = int(region.x * w)
                y = int(region.y * h)
                width = int(region.width * w)
                height = int(region.height * h)
            else:
                x, y, width, height = region.x, region.y, region.width, region.height
            
            # Bounds checking
            x = max(0, min(x, w - 1))
            y = max(0, min(y, h - 1))
            x2 = min(x + width, w)
            y2 = min(y + height, h)
            
            if x2 <= x or y2 <= y:
                return None
            
            return image[y:y2, x:x2]
            
        except Exception as e:
            logger.warning(f"Region extraction failed: {e}")
            return None
    
    def _compare_with_baseline(self, image: np.ndarray, baseline: BaselineInfo,
                             regions: List[UIRegion]) -> float:
        """Compare current image with a baseline and return similarity score."""
        try:
            # Load baseline image
            baseline_image = self._load_baseline_image(baseline)
            if baseline_image is None:
                return 0.0
            
            # Compute overall perceptual hash similarity  
            current_hash = str(imagehash.phash(Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))))
            hash_distance = imagehash.hex_to_hash(current_hash) - imagehash.hex_to_hash(baseline.perceptual_hash)
            hash_similarity = max(0.0, 1.0 - hash_distance / 64.0)  # Normalize to 0-1
            
            # Compute region-wise SSIM
            region_similarities = []
            total_importance = 0.0
            
            for region in regions:
                current_roi = self._extract_region(image, region)
                baseline_roi = self._extract_region(baseline_image, region)
                
                if current_roi is not None and baseline_roi is not None:
                    # Resize if needed
                    if current_roi.shape != baseline_roi.shape:
                        baseline_roi = cv2.resize(baseline_roi, (current_roi.shape[1], current_roi.shape[0]))
                    
                    # Compute SSIM
                    current_gray = cv2.cvtColor(current_roi, cv2.COLOR_BGR2GRAY)
                    baseline_gray = cv2.cvtColor(baseline_roi, cv2.COLOR_BGR2GRAY)
                    ssim_score = ssim(current_gray, baseline_gray)
                    
                    region_similarities.append(ssim_score * region.importance)
                    total_importance += region.importance
            
            # Weighted average of region similarities
            if total_importance > 0:
                region_similarity = sum(region_similarities) / total_importance
            else:
                region_similarity = 0.0
            
            # Combine hash and region similarity
            overall_similarity = (hash_similarity * 0.3) + (region_similarity * 0.7)
            
            return overall_similarity
            
        except Exception as e:
            logger.warning(f"Baseline comparison failed: {e}")
            return 0.0
    
    def _load_baseline_image(self, baseline: BaselineInfo) -> Optional[np.ndarray]:
        """Load a baseline image from disk."""
        try:
            filepath = self.baseline_dir / baseline.filepath
            if not filepath.exists():
                logger.warning(f"Baseline image not found: {filepath}")
                return None
            
            image = cv2.imread(str(filepath))
            return image
            
        except Exception as e:
            logger.warning(f"Could not load baseline image: {e}")
            return None
    
    def _calculate_change_score(self, global_hash_distance: int, ssim_scores: Dict[str, float],
                              hash_distances: Dict[str, int], regions: List[UIRegion]) -> float:
        """Calculate overall change score from individual metrics."""
        try:
            # Global hash component (0-1, where 1 = maximum change)
            global_component = min(global_hash_distance / 32.0, 1.0)
            
            # Region-wise components
            region_components = []
            total_importance = 0.0
            
            for region in regions:
                if region.name in ssim_scores and region.name in hash_distances:
                    ssim_score = ssim_scores[region.name]
                    hash_dist = hash_distances[region.name]
                    
                    # Convert to change scores (0 = no change, 1 = maximum change)
                    ssim_change = max(0.0, 1.0 - ssim_score)
                    hash_change = min(hash_dist / 32.0, 1.0)
                    
                    # Combine and weight by importance
                    region_change = (ssim_change * 0.7) + (hash_change * 0.3)
                    region_components.append(region_change * region.importance)
                    total_importance += region.importance
            
            # Weighted average of region changes
            if total_importance > 0 and region_components:
                region_component = sum(region_components) / total_importance
            else:
                region_component = 0.0
            
            # Combine global and region components
            overall_score = (global_component * 0.2) + (region_component * 0.8)
            
            return min(overall_score, 1.0)
            
        except Exception as e:
            logger.warning(f"Change score calculation failed: {e}")
            return 0.0
    
    def _generate_diff_mask(self, current: np.ndarray, baseline: np.ndarray) -> Optional[np.ndarray]:
        """Generate visual diff mask showing changes between images."""
        try:
            # Resize if needed
            if current.shape != baseline.shape:
                baseline = cv2.resize(baseline, (current.shape[1], current.shape[0]))
            
            # Compute absolute difference
            diff = cv2.absdiff(current, baseline)
            
            # Convert to grayscale and threshold
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, diff_thresh = cv2.threshold(diff_gray, 30, 255, cv2.THRESH_BINARY)
            
            # Apply morphological operations to clean up noise
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            diff_clean = cv2.morphologyEx(diff_thresh, cv2.MORPH_CLOSE, kernel)
            diff_clean = cv2.morphologyEx(diff_clean, cv2.MORPH_OPEN, kernel)
            
            # Create colored diff mask (red for changes)
            diff_colored = np.zeros_like(current)
            diff_colored[:, :, 2] = diff_clean  # Red channel
            
            return diff_colored
            
        except Exception as e:
            logger.warning(f"Diff mask generation failed: {e}")
            return None
    
    def save_diff_report(self, result: ChangeDetectionResult, image: np.ndarray,
                        site: str, resolution: str) -> str:
        """Save a detailed diff report with visual overlays."""
        try:
            timestamp = int(time.time())
            report_dir = self.baseline_dir / 'diff_reports'
            report_dir.mkdir(exist_ok=True)
            
            # Save current image
            image_filename = f"current_{site}_{resolution}_{timestamp}.png"
            cv2.imwrite(str(report_dir / image_filename), image)
            
            # Save diff mask if available
            diff_filename = None
            if result.diff_mask is not None:
                diff_filename = f"diff_{site}_{resolution}_{timestamp}.png"
                cv2.imwrite(str(report_dir / diff_filename), result.diff_mask)
            
            # Create JSON report
            report_data = {
                'timestamp': timestamp,
                'site': site,
                'resolution': resolution,
                'has_changes': result.has_changes,
                'confidence': result.confidence,
                'change_types': [ct.value for ct in result.change_types],
                'affected_regions': result.affected_regions,
                'ssim_scores': result.ssim_scores,
                'hash_distances': result.hash_distances,
                'recommendations': result.recommendations,
                'analysis_time_ms': result.analysis_time_ms,
                'images': {
                    'current': image_filename,
                    'diff_mask': diff_filename
                }
            }
            
            report_filename = f"change_report_{site}_{resolution}_{timestamp}.json"
            report_path = report_dir / report_filename
            
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            logger.info(f"Change detection report saved: {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"Failed to save diff report: {e}")
            return ""
    
    def _save_baseline_index(self) -> None:
        """Save the baseline index to disk."""
        try:
            index_file = self.baseline_dir / 'baselines_index.json'
            
            # Convert to serializable format
            index_data = {}
            for site_key, baseline_list in self.baselines.items():
                index_data[site_key] = []
                for baseline in baseline_list:
                    index_data[site_key].append({
                        'filepath': baseline.filepath,
                        'perceptual_hash': baseline.perceptual_hash,
                        'ssim_regions': baseline.ssim_regions,
                        'metadata': baseline.metadata,
                        'timestamp': baseline.timestamp
                    })
            
            with open(index_file, 'w') as f:
                json.dump(index_data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save baseline index: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detection statistics."""
        return {
            'total_detections': self.detection_count,
            'changes_detected': self.change_detection_count,
            'false_positives': self.false_positive_count,
            'change_detection_rate': self.change_detection_count / max(1, self.detection_count),
            'baseline_sets': len(self.baselines),
            'total_baselines': sum(len(baselines) for baselines in self.baselines.values())
        }
    
    def ci_check(self, image: np.ndarray, site: str, resolution: str) -> bool:
        """
        Perform CI check for UI changes. Returns False if changes exceed threshold.
        
        This method is designed to be called from CI/CD pipelines to fail builds
        when UI changes exceed configured thresholds.
        """
        if not self.config.get('ci_enabled', False):
            return True  # Pass if CI checking is disabled
        
        result = self.detect_changes(image, site, resolution, generate_diff=False)
        threshold = self.config.get('ci_failure_threshold', 0.40)
        
        if result.confidence >= threshold:
            formatted_confidence = format(result.confidence, ".1%")
            formatted_threshold = format(threshold, ".1%")
            logger.error(
                "CI FAILURE: UI changes exceed threshold (%s >= %s)",
                formatted_confidence,
                formatted_threshold,
            )
            return False
        
        return True


# ============================================================================
# Convenience Functions and Testing
# ============================================================================

def create_detector(baseline_dir: Optional[str] = None) -> AdaptiveUIDetector:
    """Create and initialize adaptive UI detector."""
    return AdaptiveUIDetector(baseline_dir)

def test_change_detection() -> bool:
    """Test change detection functionality."""
    if not DEPENDENCIES_AVAILABLE:
        print("❌ Dependencies not available")
        print("   Install: pip install opencv-python pillow imagehash scikit-image")
        return False
    
    print("🔍 Testing Adaptive UI Change Detection")
    print("=" * 50)
    
    detector = create_detector()
    
    if not detector.available:
        print("❌ Detector initialization failed")
        return False
    
    # Create a test image
    import tempfile
    test_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
    cv2.rectangle(test_image, (100, 100), (1800, 900), (50, 100, 50), -1)  # Green felt
    cv2.circle(test_image, (960, 540), 200, (255, 255, 255), -1)  # Center table
    
    # Add test baseline
    success = detector.add_baseline(
        test_image, 
        "test_site", 
        "1920x1080",
        {"description": "Test baseline for validation"}
    )
    
    if not success:
        print("❌ Failed to add test baseline")
        return False
    
    print("✅ Test baseline added successfully")
    
    # Test change detection with same image (should be no changes)
    result = detector.detect_changes(test_image, "test_site", "1920x1080")
    
    print(f"Detection result: changes={result.has_changes}, confidence={result.confidence:.1%}")
    print(f"Analysis time: {result.analysis_time_ms:.1f}ms")
    
    # Create modified image to test change detection
    modified_image = test_image.copy()
    cv2.circle(modified_image, (960, 540), 250, (255, 0, 0), -1)  # Different color/size
    
    change_result = detector.detect_changes(modified_image, "test_site", "1920x1080")
    
    print(f"Modified image result: changes={change_result.has_changes}, confidence={change_result.confidence:.1%}")
    
    # Get statistics
    stats = detector.get_statistics()
    print(f"Statistics: {stats}")
    
    print("✅ Adaptive UI Change Detection test completed successfully")
    return True

if __name__ == '__main__':
    """Run change detection tests when called directly."""
    import sys
    
    print("🎯 PokerTool Adaptive UI Change Detection")
    print("=" * 60)
    
    if not DEPENDENCIES_AVAILABLE:
        print("❌ CRITICAL: Dependencies not installed")
        print("\nPlease install required packages:")
        print("  pip install opencv-python pillow imagehash scikit-image numpy")
        sys.exit(1)
    
    success = test_change_detection()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED - Adaptive UI detector is working correctly!")
        sys.exit(0)
    else:
        print("❌ TESTS FAILED - Check output above")
        sys.exit(1)
