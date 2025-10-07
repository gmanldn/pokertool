#!/usr/bin/env python3
"""
Adaptive UI Change Detection Module for PokerTool

This module implements perceptual hashing and structural similarity comparison
to detect poker client UI changes before they break the scraper in production.

Features:
- Maintains baseline library of approved table states
- Computes perceptual hashes (pHash, dHash, aHash) for fast comparison
- Uses SSIM (Structural Similarity Index) for detailed analysis
- Generates diff masks and visualizations
- Configurable thresholds per region of interest
- Auto-generates alerts with detailed reports
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Tuple, Optional, Union, NamedTuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pickle

import cv2
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

# Optional dependencies - graceful fallback if not available
try:
    import imagehash
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False
    
try:
    from skimage.metrics import structural_similarity as ssim
    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False
    # Fallback SSIM implementation
    def ssim(img1, img2, **kwargs):
        """Fallback SSIM implementation using basic correlation."""
        return float(np.corrcoef(img1.flatten(), img2.flatten())[0, 1])
    
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RegionOfInterest(NamedTuple):
    """Defines a region of interest for UI change detection."""
    name: str
    x: int
    y: int
    width: int
    height: int
    threshold: float  # SSIM threshold for this region
    critical: bool = False  # If True, changes here trigger immediate alerts

@dataclass
class BaselineState:
    """Represents a baseline UI state with multiple hash types."""
    site_name: str
    resolution: str
    theme: str
    timestamp: str
    screenshot_path: str
    perceptual_hash: str
    difference_hash: str
    average_hash: str
    ssim_regions: Dict[str, float]  # Region name -> baseline SSIM score
    metadata: Dict[str, any]

@dataclass
class ComparisonResult:
    """Results from comparing a screenshot against baseline states."""
    is_match: bool
    best_match_score: float
    best_match_baseline: str
    hash_distances: Dict[str, int]  # Hash type -> distance
    ssim_scores: Dict[str, float]  # Region -> SSIM score
    diff_regions: List[str]  # Regions that exceeded threshold
    critical_changes: List[str]  # Critical regions with changes
    diff_mask_path: Optional[str] = None
    visualization_path: Optional[str] = None

class AdaptiveUIDetector:
    """
    Adaptive UI Change Detection system for poker client interfaces.
    
    Maintains a baseline library of approved UI states and detects deviations
    that could break the scraper before they reach production.
    """
    
    def __init__(self, 
                 baseline_dir: str = "assets/ui_baselines",
                 reports_dir: str = "reports/ui_changes",
                 config_path: str = "poker_config.json"):
        """
        Initialize the Adaptive UI Detector.
        
        Args:
            baseline_dir: Directory to store baseline screenshots and metadata
            reports_dir: Directory to store change detection reports
            config_path: Path to poker configuration file
        """
        self.baseline_dir = Path(baseline_dir)
        self.reports_dir = Path(reports_dir)
        self.config_path = Path(config_path)
        
        # Create directories if they don't exist
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Define standard regions of interest for poker tables
        self.regions_of_interest = {
            "cards_area": RegionOfInterest("cards_area", 300, 200, 400, 150, 0.85, True),
            "pot_area": RegionOfInterest("pot_area", 400, 100, 200, 80, 0.90, True),
            "player_actions": RegionOfInterest("player_actions", 200, 500, 600, 100, 0.80, True),
            "chip_stacks": RegionOfInterest("chip_stacks", 100, 300, 100, 200, 0.75, False),
            "dealer_button": RegionOfInterest("dealer_button", 350, 250, 50, 50, 0.95, True),
            "betting_area": RegionOfInterest("betting_area", 300, 350, 400, 100, 0.85, True),
            "hud_panels": RegionOfInterest("hud_panels", 50, 50, 200, 150, 0.70, False),
            "table_theme": RegionOfInterest("table_theme", 0, 0, -1, -1, 0.60, False),  # Full image
        }
        
        # Load existing baselines
        self.baselines = self._load_baselines()
        
        # Performance tracking
        self.detection_stats = {
            "total_comparisons": 0,
            "matches_found": 0,
            "changes_detected": 0,
            "critical_alerts": 0,
            "avg_processing_time": 0.0
        }
        
        logger.info(f"AdaptiveUIDetector initialized with {len(self.baselines)} baseline states")

    def _load_config(self) -> Dict:
        """Load configuration from poker_config.json."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}. Using defaults.")
            return {
                "ui_detection": {
                    "global_ssim_threshold": 0.80,
                    "hash_distance_threshold": 10,
                    "alert_critical_changes": True,
                    "generate_visualizations": True,
                    "max_baselines_per_site": 50
                }
            }

    def _load_baselines(self) -> Dict[str, BaselineState]:
        """Load existing baseline states from disk."""
        baselines = {}
        baselines_file = self.baseline_dir / "baselines.json"
        
        if baselines_file.exists():
            try:
                with open(baselines_file, 'r') as f:
                    data = json.load(f)
                    for key, baseline_data in data.items():
                        baselines[key] = BaselineState(**baseline_data)
                logger.info(f"Loaded {len(baselines)} baseline states")
            except Exception as e:
                logger.error(f"Error loading baselines: {e}")
        
        return baselines

    def _save_baselines(self):
        """Save baseline states to disk."""
        baselines_file = self.baseline_dir / "baselines.json"
        try:
            data = {key: asdict(baseline) for key, baseline in self.baselines.items()}
            with open(baselines_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.baselines)} baseline states")
        except Exception as e:
            logger.error(f"Error saving baselines: {e}")

    def add_baseline_screenshot(self, 
                               screenshot_path: str,
                               site_name: str,
                               resolution: str = "1920x1080",
                               theme: str = "default",
                               metadata: Optional[Dict] = None) -> str:
        """
        Add a new baseline screenshot to the approved states library.
        
        Args:
            screenshot_path: Path to the screenshot file
            site_name: Name of the poker site (e.g., "betfair", "pokerstars")
            resolution: Screen resolution (e.g., "1920x1080")
            theme: UI theme name
            metadata: Additional metadata about this baseline
            
        Returns:
            Unique identifier for this baseline state
        """
        if not Path(screenshot_path).exists():
            raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")
        
        # Load and process the image
        image = cv2.imread(screenshot_path)
        if image is None:
            raise ValueError(f"Could not load image: {screenshot_path}")
        
        # Generate hashes
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if HAS_IMAGEHASH:
            phash = str(imagehash.phash(pil_image))
            dhash = str(imagehash.dhash(pil_image))
            ahash = str(imagehash.average_hash(pil_image))
        else:
            # Fallback hash implementation
            phash = self._simple_hash(image, 8)
            dhash = self._simple_hash(image, 8, method='diff')
            ahash = self._simple_hash(image, 8, method='average')
        
        # Calculate SSIM scores for regions (baseline against itself = 1.0)
        ssim_regions = {}
        for region_name, region in self.regions_of_interest.items():
            if region.width == -1:  # Full image region
                ssim_regions[region_name] = 1.0
            else:
                ssim_regions[region_name] = 1.0
        
        # Create baseline state
        timestamp = datetime.now(timezone.utc).isoformat()
        baseline_id = f"{site_name}_{resolution}_{theme}_{hashlib.md5(phash.encode()).hexdigest()[:8]}"
        
        # Copy screenshot to baselines directory
        baseline_screenshot_path = self.baseline_dir / f"{baseline_id}.png"
        cv2.imwrite(str(baseline_screenshot_path), image)
        
        baseline = BaselineState(
            site_name=site_name,
            resolution=resolution,
            theme=theme,
            timestamp=timestamp,
            screenshot_path=str(baseline_screenshot_path),
            perceptual_hash=phash,
            difference_hash=dhash,
            average_hash=ahash,
            ssim_regions=ssim_regions,
            metadata=metadata or {}
        )
        
        # Add to baselines
        self.baselines[baseline_id] = baseline
        self._save_baselines()
        
        logger.info(f"Added baseline state: {baseline_id}")
        return baseline_id

    def _compute_hash_distances(self, 
                               image: Image.Image, 
                               baseline: BaselineState) -> Dict[str, int]:
        """Compute distances between image hashes and baseline hashes."""
        if HAS_IMAGEHASH:
            phash = imagehash.phash(image)
            dhash = imagehash.dhash(image)
            ahash = imagehash.average_hash(image)
            
            baseline_phash = imagehash.hex_to_hash(baseline.perceptual_hash)
            baseline_dhash = imagehash.hex_to_hash(baseline.difference_hash)
            baseline_ahash = imagehash.hex_to_hash(baseline.average_hash)
            
            return {
                "perceptual": phash - baseline_phash,
                "difference": dhash - baseline_dhash,
                "average": ahash - baseline_ahash
            }
        else:
            # Fallback hash comparison
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            phash = self._simple_hash(cv_image, 8)
            dhash = self._simple_hash(cv_image, 8, method='diff')
            ahash = self._simple_hash(cv_image, 8, method='average')
            
            return {
                "perceptual": self._simple_hash_distance(phash, baseline.perceptual_hash),
                "difference": self._simple_hash_distance(dhash, baseline.difference_hash),
                "average": self._simple_hash_distance(ahash, baseline.average_hash)
            }

    def _compute_ssim_scores(self,
                            image: np.ndarray, 
                            baseline_image: np.ndarray) -> Dict[str, float]:
        """Compute SSIM scores for all regions of interest."""
        # Convert to grayscale for SSIM computation
        gray_current = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_baseline = cv2.cvtColor(baseline_image, cv2.COLOR_BGR2GRAY)
        
        ssim_scores = {}
        
        for region_name, region in self.regions_of_interest.items():
            try:
                if region.width == -1:  # Full image
                    score = ssim(gray_current, gray_baseline)
                else:
                    # Extract region
                    current_region = gray_current[region.y:region.y+region.height, 
                                                region.x:region.x+region.width]
                    baseline_region = gray_baseline[region.y:region.y+region.height,
                                                  region.x:region.x+region.width]
                    
                    if current_region.size > 0 and baseline_region.size > 0:
                        score = ssim(current_region, baseline_region)
                    else:
                        score = 0.0
                        
                ssim_scores[region_name] = score
            except Exception as e:
                logger.warning(f"Error computing SSIM for region {region_name}: {e}")
                ssim_scores[region_name] = 0.0
        
        return ssim_scores

    def _generate_diff_mask(self, 
                           image: np.ndarray, 
                           baseline_image: np.ndarray,
                           comparison_id: str) -> str:
        """Generate a difference mask highlighting changed areas."""
        try:
            # Compute absolute difference
            diff = cv2.absdiff(image, baseline_image)
            
            # Convert to grayscale and threshold
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
            
            # Create colorized diff mask
            diff_mask = cv2.applyColorMap(thresh, cv2.COLORMAP_HOT)
            
            # Save diff mask
            mask_path = self.reports_dir / f"{comparison_id}_diff_mask.png"
            cv2.imwrite(str(mask_path), diff_mask)
            
            return str(mask_path)
        except Exception as e:
            logger.error(f"Error generating diff mask: {e}")
            return ""

    def _generate_visualization(self,
                               image: np.ndarray,
                               baseline_image: np.ndarray,
                               comparison_result: ComparisonResult,
                               comparison_id: str) -> str:
        """Generate a comprehensive visualization of the comparison."""
        try:
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            fig.suptitle(f'UI Change Detection Analysis - {comparison_id}', fontsize=16)
            
            # Convert BGR to RGB for matplotlib
            current_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            baseline_rgb = cv2.cvtColor(baseline_image, cv2.COLOR_BGR2RGB)
            
            # Original images
            axes[0, 0].imshow(current_rgb)
            axes[0, 0].set_title(f'Current Screenshot')
            axes[0, 0].axis('off')
            
            axes[0, 1].imshow(baseline_rgb)
            axes[0, 1].set_title(f'Baseline Screenshot')
            axes[0, 1].axis('off')
            
            # Difference visualization
            diff = cv2.absdiff(image, baseline_image)
            diff_rgb = cv2.cvtColor(diff, cv2.COLOR_BGR2RGB)
            axes[0, 2].imshow(diff_rgb)
            axes[0, 2].set_title('Absolute Difference')
            axes[0, 2].axis('off')
            
            # SSIM scores bar chart
            regions = list(comparison_result.ssim_scores.keys())
            scores = list(comparison_result.ssim_scores.values())
            colors = ['red' if region in comparison_result.diff_regions else 'green' for region in regions]
            
            axes[1, 0].bar(range(len(regions)), scores, color=colors, alpha=0.7)
            axes[1, 0].set_xticks(range(len(regions)))
            axes[1, 0].set_xticklabels(regions, rotation=45, ha='right')
            axes[1, 0].set_ylabel('SSIM Score')
            axes[1, 0].set_title('Region SSIM Scores')
            axes[1, 0].axhline(y=0.8, color='orange', linestyle='--', label='Threshold')
            axes[1, 0].legend()
            
            # Hash distances
            hash_types = list(comparison_result.hash_distances.keys())
            distances = list(comparison_result.hash_distances.values())
            
            axes[1, 1].bar(hash_types, distances, color=['blue', 'cyan', 'navy'])
            axes[1, 1].set_ylabel('Hash Distance')
            axes[1, 1].set_title('Perceptual Hash Distances')
            axes[1, 1].axhline(y=10, color='red', linestyle='--', label='Threshold')
            axes[1, 1].legend()
            
            # Summary statistics
            summary_text = f"""
Match Found: {comparison_result.is_match}
Best Match Score: {comparison_result.best_match_score:.3f}
Changed Regions: {len(comparison_result.diff_regions)}
Critical Changes: {len(comparison_result.critical_changes)}

Regions with Changes:
{chr(10).join(comparison_result.diff_regions)}

Critical Regions:
{chr(10).join(comparison_result.critical_changes)}
"""
            axes[1, 2].text(0.1, 0.9, summary_text, transform=axes[1, 2].transAxes,
                           fontsize=10, verticalalignment='top', fontfamily='monospace')
            axes[1, 2].set_title('Detection Summary')
            axes[1, 2].axis('off')
            
            plt.tight_layout()
            
            # Save visualization
            viz_path = self.reports_dir / f"{comparison_id}_analysis.png"
            plt.savefig(str(viz_path), dpi=150, bbox_inches='tight')
            plt.close()
            
            return str(viz_path)
        except Exception as e:
            logger.error(f"Error generating visualization: {e}")
            return ""

    def compare_screenshot(self, 
                          screenshot_path: str,
                          site_name: str,
                          resolution: str = "1920x1080",
                          theme: str = "default") -> ComparisonResult:
        """
        Compare a screenshot against all matching baseline states.
        
        Args:
            screenshot_path: Path to the screenshot to analyze
            site_name: Name of the poker site
            resolution: Screen resolution
            theme: UI theme name
            
        Returns:
            ComparisonResult with detailed analysis
        """
        start_time = datetime.now()
        
        if not Path(screenshot_path).exists():
            raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")
        
        # Load the image
        image = cv2.imread(screenshot_path)
        if image is None:
            raise ValueError(f"Could not load image: {screenshot_path}")
        
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Find matching baselines (same site, resolution, theme)
        matching_baselines = {
            bid: baseline for bid, baseline in self.baselines.items()
            if (baseline.site_name == site_name and 
                baseline.resolution == resolution and 
                baseline.theme == theme)
        }
        
        if not matching_baselines:
            logger.warning(f"No matching baselines found for {site_name}_{resolution}_{theme}")
            return ComparisonResult(
                is_match=False,
                best_match_score=0.0,
                best_match_baseline="",
                hash_distances={},
                ssim_scores={},
                diff_regions=[],
                critical_changes=[]
            )
        
        best_match_score = 0.0
        best_match_baseline = ""
        best_comparison = None
        
        # Compare against each matching baseline
        for baseline_id, baseline in matching_baselines.items():
            # Load baseline image
            baseline_image = cv2.imread(baseline.screenshot_path)
            if baseline_image is None:
                continue
            
            # Compute hash distances
            hash_distances = self._compute_hash_distances(pil_image, baseline)
            
            # Compute SSIM scores
            ssim_scores = self._compute_ssim_scores(image, baseline_image)
            
            # Calculate overall match score (weighted average of SSIM scores)
            weights = {
                "cards_area": 0.25,
                "pot_area": 0.20,
                "player_actions": 0.20,
                "betting_area": 0.15,
                "dealer_button": 0.10,
                "chip_stacks": 0.05,
                "hud_panels": 0.03,
                "table_theme": 0.02
            }
            
            match_score = sum(ssim_scores.get(region, 0) * weights.get(region, 0) 
                            for region in ssim_scores.keys())
            
            if match_score > best_match_score:
                best_match_score = match_score
                best_match_baseline = baseline_id
                
                # Identify regions that exceed threshold
                diff_regions = []
                critical_changes = []
                
                for region_name, score in ssim_scores.items():
                    region = self.regions_of_interest.get(region_name)
                    if region and score < region.threshold:
                        diff_regions.append(region_name)
                        if region.critical:
                            critical_changes.append(region_name)
                
                best_comparison = ComparisonResult(
                    is_match=len(critical_changes) == 0 and best_match_score > 0.8,
                    best_match_score=best_match_score,
                    best_match_baseline=baseline_id,
                    hash_distances=hash_distances,
                    ssim_scores=ssim_scores,
                    diff_regions=diff_regions,
                    critical_changes=critical_changes
                )
                
                # Generate visualizations if configured
                if self.config.get("ui_detection", {}).get("generate_visualizations", True):
                    comparison_id = f"{site_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    # Generate diff mask
                    diff_mask_path = self._generate_diff_mask(image, baseline_image, comparison_id)
                    best_comparison.diff_mask_path = diff_mask_path
                    
                    # Generate comprehensive visualization
                    viz_path = self._generate_visualization(image, baseline_image, best_comparison, comparison_id)
                    best_comparison.visualization_path = viz_path
        
        # Update statistics
        self.detection_stats["total_comparisons"] += 1
        if best_comparison and best_comparison.is_match:
            self.detection_stats["matches_found"] += 1
        else:
            self.detection_stats["changes_detected"] += 1
            
        if best_comparison and len(best_comparison.critical_changes) > 0:
            self.detection_stats["critical_alerts"] += 1
            
        processing_time = (datetime.now() - start_time).total_seconds()
        self.detection_stats["avg_processing_time"] = (
            (self.detection_stats["avg_processing_time"] * (self.detection_stats["total_comparisons"] - 1) + 
             processing_time) / self.detection_stats["total_comparisons"]
        )
        
        return best_comparison or ComparisonResult(
            is_match=False,
            best_match_score=0.0,
            best_match_baseline="",
            hash_distances={},
            ssim_scores={},
            diff_regions=[],
            critical_changes=[]
        )

    def generate_alert_report(self, 
                            comparison_result: ComparisonResult,
                            screenshot_path: str,
                            site_name: str) -> str:
        """Generate a detailed alert report for UI changes."""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        report_path = self.reports_dir / f"ui_change_alert_{site_name}_{timestamp}.json"
        
        alert_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "site_name": site_name,
            "screenshot_path": screenshot_path,
            "alert_level": "CRITICAL" if comparison_result.critical_changes else "WARNING",
            "is_match": comparison_result.is_match,
            "match_score": comparison_result.best_match_score,
            "best_baseline": comparison_result.best_match_baseline,
            "changed_regions": comparison_result.diff_regions,
            "critical_regions": comparison_result.critical_changes,
            "ssim_scores": comparison_result.ssim_scores,
            "hash_distances": comparison_result.hash_distances,
            "diff_mask_path": comparison_result.diff_mask_path,
            "visualization_path": comparison_result.visualization_path,
            "recommendations": self._generate_recommendations(comparison_result)
        }
        
        try:
            with open(report_path, 'w') as f:
                json.dump(alert_data, f, indent=2)
            logger.info(f"Alert report generated: {report_path}")
            return str(report_path)
        except Exception as e:
            logger.error(f"Error generating alert report: {e}")
            return ""

    def _generate_recommendations(self, comparison_result: ComparisonResult) -> List[str]:
        """Generate recommendations based on comparison results."""
        recommendations = []
        
        if len(comparison_result.critical_changes) > 0:
            recommendations.append("IMMEDIATE ACTION REQUIRED: Critical UI regions have changed")
            recommendations.append("Review scraper extraction logic for affected regions")
            recommendations.append("Update baseline screenshots if changes are legitimate")
            
        if comparison_result.best_match_score < 0.5:
            recommendations.append("Major UI changes detected - comprehensive scraper review needed")
            
        if "cards_area" in comparison_result.diff_regions:
            recommendations.append("Card detection may be affected - verify card recognition accuracy")
            
        if "pot_area" in comparison_result.diff_regions:
            recommendations.append("Pot reading may be affected - verify bet size extraction")
            
        if "player_actions" in comparison_result.diff_regions:
            recommendations.append("Action button detection may be affected - verify UI automation")
            
        if len(comparison_result.diff_regions) == 0:
            recommendations.append("No significant changes detected - scraper should continue to work normally")
            
        return recommendations

    def get_detection_statistics(self) -> Dict:
        """Get current detection statistics."""
        return self.detection_stats.copy()

    def cleanup_old_reports(self, days_to_keep: int = 30):
        """Clean up old detection reports to save disk space."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for report_file in self.reports_dir.glob("*.json"):
            try:
                file_time = datetime.fromtimestamp(report_file.stat().st_mtime)
                if file_time < cutoff_date:
                    report_file.unlink()
                    logger.info(f"Cleaned up old report: {report_file}")
            except Exception as e:
                logger.warning(f"Error cleaning up {report_file}: {e}")

    def _simple_hash(self, image: np.ndarray, hash_size: int = 8, method: str = 'average') -> str:
        """Fallback hash implementation when imagehash is not available."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Resize to hash_size x hash_size
        resized = cv2.resize(gray, (hash_size, hash_size), interpolation=cv2.INTER_AREA)
        
        if method == 'average':
            # Average hash: compare each pixel to average
            avg = resized.mean()
            hash_bits = (resized > avg).flatten()
        elif method == 'diff':
            # Difference hash: compare adjacent pixels
            hash_bits = []
            for row in resized:
                for i in range(len(row) - 1):
                    hash_bits.append(row[i] > row[i + 1])
            hash_bits = np.array(hash_bits)
        else:  # perceptual (simplified)
            # Simple perceptual hash using DCT approximation
            # For fallback, just use average hash
            avg = resized.mean()
            hash_bits = (resized > avg).flatten()
        
        # Convert to hex string
        hash_int = 0
        for i, bit in enumerate(hash_bits[:64]):  # Limit to 64 bits
            if bit:
                hash_int |= (1 << i)
        
        return f"{hash_int:016x}"

    def _simple_hash_distance(self, hash1: str, hash2: str) -> int:
        """Compute Hamming distance between two simple hashes."""
        try:
            int1 = int(hash1, 16)
            int2 = int(hash2, 16)
            return bin(int1 ^ int2).count('1')
        except (ValueError, TypeError):
            return 64  # Maximum distance for fallback

def main():
    """Example usage of the Adaptive UI Detector."""
    # Initialize detector
    detector = AdaptiveUIDetector()
    
    # Example: Add a baseline screenshot
    # detector.add_baseline_screenshot(
    #     "screenshot.png",
    #     site_name="betfair",
    #     resolution="1920x1080",
    #     theme="default",
    #     metadata={"table_type": "nlhe", "stake": "1/2"}
    # )
    
    # Example: Compare a new screenshot
    # result = detector.compare_screenshot(
    #     "new_screenshot.png",
    #     site_name="betfair",
    #     resolution="1920x1080"
    # )
    
    # Generate alert if changes detected
    # if not result.is_match:
    #     detector.generate_alert_report(result, "new_screenshot.png", "betfair")
    
    print("Adaptive UI Detector initialized successfully!")
    print("Use the detector methods to add baselines and compare screenshots.")

if __name__ == "__main__":
    main()
