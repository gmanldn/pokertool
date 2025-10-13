#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adaptive Learning System for Poker Screen Scraper
=================================================

Machine learning and adaptive optimization for OCR and detection accuracy.

Features:
- Environment profiling (resolution, brightness, monitor calibration)
- OCR strategy performance tracking and auto-prioritization
- Adaptive parameter tuning based on success metrics
- CDP-based ground truth learning
- Feedback loop integration with validation system
- Persistent storage of learned parameters

Author: Claude Code
"""

import json
import logging
import time
import hashlib
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import deque, defaultdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class ExtractionType(Enum):
    """Types of data extraction."""
    POT_SIZE = "pot_size"
    PLAYER_NAME = "player_name"
    STACK_SIZE = "stack_size"
    CARD_RANK = "card_rank"
    CARD_SUIT = "card_suit"
    BLIND_AMOUNT = "blind_amount"
    TABLE_DETECTION = "table_detection"


@dataclass
class EnvironmentSignature:
    """Unique signature for a scraping environment."""
    screen_width: int
    screen_height: int
    avg_brightness: float  # 0-255
    color_profile: str  # Hash of color distribution

    def to_key(self) -> str:
        """Convert to hashable key."""
        return f"{self.screen_width}x{self.screen_height}_b{int(self.avg_brightness)}_c{self.color_profile[:8]}"

    @classmethod
    def from_image(cls, image: np.ndarray) -> 'EnvironmentSignature':
        """Create signature from image."""
        h, w = image.shape[:2]

        # Calculate average brightness
        if len(image.shape) == 3:
            gray = np.mean(image, axis=2)
        else:
            gray = image
        avg_brightness = float(np.mean(gray))

        # Create color profile hash (histogram-based)
        hist = np.histogram(image.flatten(), bins=32, range=(0, 256))[0]
        hist_str = ','.join(map(str, hist))
        color_hash = hashlib.md5(hist_str.encode()).hexdigest()

        return cls(
            screen_width=w,
            screen_height=h,
            avg_brightness=avg_brightness,
            color_profile=color_hash
        )


@dataclass
class OCRStrategyResult:
    """Result from a single OCR strategy attempt."""
    strategy_id: str
    extracted_value: Any
    confidence: float
    execution_time_ms: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class OCRStrategyStats:
    """Performance statistics for an OCR strategy."""
    strategy_id: str
    total_attempts: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    avg_execution_time_ms: float = 0.0
    success_rate: float = 0.0
    last_success_time: Optional[float] = None

    def update_success(self, execution_time_ms: float):
        """Record successful extraction."""
        self.total_attempts += 1
        self.successful_extractions += 1
        self.last_success_time = time.time()

        # Update running average
        n = self.successful_extractions
        self.avg_execution_time_ms = (
            (self.avg_execution_time_ms * (n - 1) + execution_time_ms) / n
        )
        self.success_rate = self.successful_extractions / self.total_attempts

    def update_failure(self):
        """Record failed extraction."""
        self.total_attempts += 1
        self.failed_extractions += 1
        self.success_rate = self.successful_extractions / self.total_attempts


@dataclass
class EnvironmentProfile:
    """Learned optimal parameters for a specific environment."""
    env_signature: str

    # Detection parameters
    detection_threshold: float = 0.40
    felt_ranges: List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = field(default_factory=list)

    # OCR parameters
    best_ocr_configs: Dict[str, str] = field(default_factory=dict)  # extraction_type -> config
    optimal_preprocessing: Dict[str, Any] = field(default_factory=dict)

    # Performance metrics
    success_count: int = 0
    total_attempts: int = 0
    avg_detection_time_ms: float = 0.0

    # Metadata
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)

    def get_success_rate(self) -> float:
        """Calculate success rate."""
        return self.success_count / max(1, self.total_attempts)

    def update_metrics(self, success: bool, detection_time_ms: float):
        """Update performance metrics."""
        self.total_attempts += 1
        if success:
            self.success_count += 1

        # Update running average
        n = self.total_attempts
        self.avg_detection_time_ms = (
            (self.avg_detection_time_ms * (n - 1) + detection_time_ms) / n
        )
        self.last_updated = time.time()


@dataclass
class ExtractionFeedback:
    """User feedback on an extraction result."""
    extraction_type: ExtractionType
    extracted_value: Any
    corrected_value: Any
    strategy_used: str
    environment: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class CDPGroundTruth:
    """Ground truth data from Chrome DevTools Protocol."""
    pot_size: Optional[float] = None
    player_names: Dict[int, str] = field(default_factory=dict)
    stack_sizes: Dict[int, float] = field(default_factory=dict)
    board_cards: List[str] = field(default_factory=list)
    hero_cards: List[str] = field(default_factory=list)
    blinds: Tuple[float, float] = (0.0, 0.0)
    timestamp: float = field(default_factory=time.time)


# ============================================================================
# Learning System Core
# ============================================================================

class ScraperLearningSystem:
    """
    Adaptive learning system for poker screen scraper.

    Learns from:
    1. Multiple extraction attempts (track which strategies work best)
    2. Environment variations (screen resolution, brightness, color profiles)
    3. CDP ground truth data (when available)
    4. User feedback/corrections (validation loop)
    5. Historical performance data
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize learning system.

        Args:
            storage_dir: Directory for persistent storage of learned data
        """
        self.storage_dir = storage_dir or Path.home() / '.pokertool' / 'learning'
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Environment profiles (keyed by environment signature)
        self.environment_profiles: Dict[str, EnvironmentProfile] = {}

        # OCR strategy performance tracking
        self.ocr_strategy_stats: Dict[str, Dict[str, OCRStrategyStats]] = defaultdict(dict)
        # Format: {extraction_type: {strategy_id: stats}}

        # Adaptive parameters (updated based on recent performance)
        self.adaptive_params = {
            'detection_threshold': 0.40,
            'min_card_area': 1500,
            'max_card_area': 300000,
            'card_aspect_min': 0.5,
            'card_aspect_max': 1.0,
            'ocr_scale_factor': 4.0,
        }

        # Recent results for adaptive tuning (sliding window)
        self.recent_detections = deque(maxlen=100)  # (success, confidence, time_ms)
        self.recent_extractions: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))

        # Feedback history
        self.feedback_history: List[ExtractionFeedback] = []

        # CDP learning data
        self.cdp_ground_truth_history: deque = deque(maxlen=1000)
        self.ocr_vs_cdp_accuracy: Dict[str, List[float]] = defaultdict(list)

        # Pattern learning
        self.learned_patterns = {
            'player_names': set(),  # Common username patterns
            'stack_ranges': {},  # Common stack sizes per stake level
            'pot_multipliers': [],  # Pot size as multiple of BB
        }

        # Load persisted data
        self._load_from_disk()

        logger.info(f"🧠 Learning system initialized (storage: {self.storage_dir})")
        logger.info(f"   Loaded {len(self.environment_profiles)} environment profiles")
        logger.info(f"   Loaded {sum(len(s) for s in self.ocr_strategy_stats.values())} OCR strategy stats")

    # ========================================================================
    # Environment Profiling
    # ========================================================================

    def get_environment_profile(self, image: np.ndarray) -> EnvironmentProfile:
        """
        Get or create environment profile for the current image.

        Args:
            image: Screenshot to analyze

        Returns:
            EnvironmentProfile with optimal parameters for this environment
        """
        signature = EnvironmentSignature.from_image(image)
        env_key = signature.to_key()

        if env_key not in self.environment_profiles:
            # Create new profile with default parameters
            profile = EnvironmentProfile(
                env_signature=env_key,
                detection_threshold=self.adaptive_params['detection_threshold']
            )
            self.environment_profiles[env_key] = profile
            logger.info(f"🆕 Created new environment profile: {env_key}")

        return self.environment_profiles[env_key]

    def update_environment_profile(self, image: np.ndarray, success: bool,
                                   detection_time_ms: float):
        """
        Update environment profile based on detection result.

        Args:
            image: Screenshot used
            success: Whether detection was successful
            detection_time_ms: Time taken for detection
        """
        profile = self.get_environment_profile(image)
        profile.update_metrics(success, detection_time_ms)

        # Adaptive threshold tuning
        if profile.total_attempts >= 10:
            success_rate = profile.get_success_rate()

            if success_rate < 0.70:
                # Too many false negatives - lower threshold
                profile.detection_threshold = max(0.25, profile.detection_threshold - 0.02)
                logger.info(f"📉 Lowering detection threshold to {profile.detection_threshold:.2f} "
                          f"(success rate: {success_rate:.1%})")
            elif success_rate > 0.95 and detection_time_ms > 100:
                # Very high success but slow - can increase threshold
                profile.detection_threshold = min(0.60, profile.detection_threshold + 0.01)
                logger.info(f"📈 Raising detection threshold to {profile.detection_threshold:.2f} "
                          f"(optimizing for speed)")

        # Persist changes periodically
        if profile.total_attempts % 20 == 0:
            self._save_to_disk()

    # ========================================================================
    # OCR Strategy Learning
    # ========================================================================

    def record_ocr_attempt(self, extraction_type: ExtractionType,
                          strategy_id: str, result: OCRStrategyResult):
        """
        Record an OCR strategy attempt.

        Args:
            extraction_type: Type of data being extracted
            strategy_id: Unique identifier for the OCR strategy
            result: Result from the strategy
        """
        type_key = extraction_type.value

        if strategy_id not in self.ocr_strategy_stats[type_key]:
            self.ocr_strategy_stats[type_key][strategy_id] = OCRStrategyStats(
                strategy_id=strategy_id
            )

        # Store for later validation
        self.recent_extractions[type_key].append({
            'strategy_id': strategy_id,
            'result': result,
            'pending_validation': True
        })

    def record_ocr_success(self, extraction_type: ExtractionType,
                          strategy_id: str, execution_time_ms: float):
        """
        Record successful OCR extraction.

        Args:
            extraction_type: Type of data extracted
            strategy_id: Strategy that succeeded
            execution_time_ms: Execution time
        """
        type_key = extraction_type.value
        stats = self.ocr_strategy_stats[type_key].get(strategy_id)

        if stats:
            stats.update_success(execution_time_ms)
            logger.debug(f"✓ OCR success: {type_key}/{strategy_id} "
                        f"(success rate: {stats.success_rate:.1%})")

    def record_ocr_failure(self, extraction_type: ExtractionType, strategy_id: str):
        """Record failed OCR extraction."""
        type_key = extraction_type.value
        stats = self.ocr_strategy_stats[type_key].get(strategy_id)

        if stats:
            stats.update_failure()
            logger.debug(f"✗ OCR failure: {type_key}/{strategy_id} "
                        f"(success rate: {stats.success_rate:.1%})")

    def get_best_ocr_strategies(self, extraction_type: ExtractionType,
                               top_k: int = 3) -> List[str]:
        """
        Get the best-performing OCR strategies for a given extraction type.

        Args:
            extraction_type: Type of extraction
            top_k: Number of top strategies to return

        Returns:
            List of strategy IDs, ordered by performance
        """
        type_key = extraction_type.value
        strategies = self.ocr_strategy_stats[type_key]

        if not strategies:
            return []

        # Sort by success rate, then by execution time
        sorted_strategies = sorted(
            strategies.values(),
            key=lambda s: (s.success_rate, -s.avg_execution_time_ms),
            reverse=True
        )

        # Filter strategies with sufficient data (at least 5 attempts)
        reliable_strategies = [
            s for s in sorted_strategies
            if s.total_attempts >= 5
        ]

        if not reliable_strategies:
            # Fall back to all strategies if none have enough data
            reliable_strategies = sorted_strategies

        return [s.strategy_id for s in reliable_strategies[:top_k]]

    # ========================================================================
    # Adaptive Parameter Tuning
    # ========================================================================

    def get_adaptive_parameters(self) -> Dict[str, Any]:
        """
        Get current adaptive parameters based on recent performance.

        Returns:
            Dictionary of tuned parameters
        """
        return self.adaptive_params.copy()

    def update_adaptive_parameters(self):
        """Update adaptive parameters based on recent results."""
        if len(self.recent_detections) < 20:
            return  # Not enough data yet

        # Analyze recent detection performance
        recent = list(self.recent_detections)
        success_rate = sum(1 for r in recent if r[0]) / len(recent)
        avg_confidence = np.mean([r[1] for r in recent if r[0]])
        avg_time = np.mean([r[2] for r in recent])

        # Adaptive detection threshold
        if success_rate < 0.75:
            # Lower threshold for better detection
            self.adaptive_params['detection_threshold'] = max(
                0.25, self.adaptive_params['detection_threshold'] - 0.02
            )
            logger.info(f"🔧 Lowered detection threshold to "
                       f"{self.adaptive_params['detection_threshold']:.2f}")
        elif success_rate > 0.95 and avg_time < 80:
            # Increase threshold for efficiency
            self.adaptive_params['detection_threshold'] = min(
                0.60, self.adaptive_params['detection_threshold'] + 0.01
            )
            logger.info(f"🔧 Raised detection threshold to "
                       f"{self.adaptive_params['detection_threshold']:.2f}")

        # Adaptive card detection parameters
        card_extraction = self.recent_extractions.get(ExtractionType.CARD_RANK.value, [])
        if len(card_extraction) >= 10:
            # Analyze card detection success
            # Could tune area ranges, aspect ratios, etc. based on results
            pass

    def record_detection_result(self, success: bool, confidence: float,
                               time_ms: float):
        """
        Record a detection attempt for adaptive tuning.

        Args:
            success: Whether detection succeeded
            confidence: Detection confidence score
            time_ms: Detection time in milliseconds
        """
        self.recent_detections.append((success, confidence, time_ms))

        # Update adaptive parameters periodically
        if len(self.recent_detections) % 25 == 0:
            self.update_adaptive_parameters()

    # ========================================================================
    # CDP-Based Learning (Ground Truth)
    # ========================================================================

    def record_cdp_ground_truth(self, cdp_data: CDPGroundTruth):
        """
        Record ground truth data from Chrome DevTools Protocol.

        Args:
            cdp_data: Verified data from CDP
        """
        self.cdp_ground_truth_history.append(cdp_data)

    def compare_ocr_vs_cdp(self, ocr_extracted: Dict[str, Any],
                          cdp_data: CDPGroundTruth,
                          extraction_types: List[ExtractionType]):
        """
        Compare OCR extraction against CDP ground truth and learn from differences.

        Args:
            ocr_extracted: Data extracted via OCR
            cdp_data: Ground truth from CDP
            extraction_types: Types of data to compare
        """
        for ext_type in extraction_types:
            type_key = ext_type.value

            # Compare and calculate accuracy
            if ext_type == ExtractionType.POT_SIZE:
                ocr_val = ocr_extracted.get('pot_size', 0.0)
                cdp_val = cdp_data.pot_size or 0.0

                if cdp_val > 0:
                    accuracy = 1.0 - abs(ocr_val - cdp_val) / cdp_val
                    self.ocr_vs_cdp_accuracy[type_key].append(accuracy)

                    if accuracy < 0.90:
                        logger.warning(f"⚠️ OCR pot size accuracy low: {accuracy:.1%} "
                                     f"(OCR: ${ocr_val:.2f}, CDP: ${cdp_val:.2f})")

            elif ext_type == ExtractionType.PLAYER_NAME:
                ocr_names = ocr_extracted.get('player_names', {})
                cdp_names = cdp_data.player_names

                matches = sum(
                    1 for seat, name in cdp_names.items()
                    if seat in ocr_names and ocr_names[seat].lower() == name.lower()
                )

                if cdp_names:
                    accuracy = matches / len(cdp_names)
                    self.ocr_vs_cdp_accuracy[type_key].append(accuracy)

                    # Learn successful name patterns
                    for name in cdp_names.values():
                        if name:
                            self.learned_patterns['player_names'].add(name)

            elif ext_type == ExtractionType.STACK_SIZE:
                ocr_stacks = ocr_extracted.get('stack_sizes', {})
                cdp_stacks = cdp_data.stack_sizes

                accurate_count = 0
                for seat, cdp_stack in cdp_stacks.items():
                    if seat in ocr_stacks and cdp_stack > 0:
                        ocr_stack = ocr_stacks[seat]
                        accuracy = 1.0 - abs(ocr_stack - cdp_stack) / cdp_stack
                        if accuracy > 0.95:  # Within 5%
                            accurate_count += 1

                if cdp_stacks:
                    accuracy = accurate_count / len(cdp_stacks)
                    self.ocr_vs_cdp_accuracy[type_key].append(accuracy)

    def get_cdp_learning_stats(self) -> Dict[str, Any]:
        """Get statistics on CDP-based learning."""
        stats = {
            'total_cdp_samples': len(self.cdp_ground_truth_history),
            'accuracy_by_type': {}
        }

        for ext_type, accuracy_list in self.ocr_vs_cdp_accuracy.items():
            if accuracy_list:
                stats['accuracy_by_type'][ext_type] = {
                    'avg_accuracy': np.mean(accuracy_list),
                    'min_accuracy': np.min(accuracy_list),
                    'max_accuracy': np.max(accuracy_list),
                    'sample_count': len(accuracy_list)
                }

        return stats

    # ========================================================================
    # Feedback Loop Integration
    # ========================================================================

    def record_user_feedback(self, feedback: ExtractionFeedback):
        """
        Record user correction/validation feedback.

        Args:
            feedback: User's correction of an extraction
        """
        self.feedback_history.append(feedback)

        # Update strategy statistics based on feedback
        type_key = feedback.extraction_type.value

        if feedback.extracted_value == feedback.corrected_value:
            # Extraction was correct
            self.record_ocr_success(
                feedback.extraction_type,
                feedback.strategy_used,
                0.0  # Time not available in feedback
            )
        else:
            # Extraction was incorrect
            self.record_ocr_failure(
                feedback.extraction_type,
                feedback.strategy_used
            )

            logger.info(f"📝 User feedback: {type_key} corrected from "
                       f"'{feedback.extracted_value}' to '{feedback.corrected_value}'")

        # Learn from corrections
        if feedback.extraction_type == ExtractionType.PLAYER_NAME:
            if feedback.corrected_value:
                self.learned_patterns['player_names'].add(feedback.corrected_value)

    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get statistics on user feedback."""
        if not self.feedback_history:
            return {'total_feedback': 0}

        corrections_by_type = defaultdict(int)
        correct_by_type = defaultdict(int)

        for feedback in self.feedback_history:
            type_key = feedback.extraction_type.value
            if feedback.extracted_value == feedback.corrected_value:
                correct_by_type[type_key] += 1
            else:
                corrections_by_type[type_key] += 1

        return {
            'total_feedback': len(self.feedback_history),
            'corrections_by_type': dict(corrections_by_type),
            'correct_by_type': dict(correct_by_type),
            'correction_rate': sum(corrections_by_type.values()) / len(self.feedback_history)
        }

    # ========================================================================
    # Pattern Learning
    # ========================================================================

    def validate_extraction_with_patterns(self, extraction_type: ExtractionType,
                                         extracted_value: Any) -> float:
        """
        Validate an extraction against learned patterns.

        Args:
            extraction_type: Type of extraction
            extracted_value: Value to validate

        Returns:
            Confidence score (0.0 - 1.0)
        """
        if extraction_type == ExtractionType.PLAYER_NAME:
            if not extracted_value or not isinstance(extracted_value, str):
                return 0.0

            # Check against known player names
            if extracted_value in self.learned_patterns['player_names']:
                return 1.0

            # Check for partial matches (handles OCR errors)
            for known_name in self.learned_patterns['player_names']:
                if known_name.lower() in extracted_value.lower() or \
                   extracted_value.lower() in known_name.lower():
                    return 0.85

            # Check if format looks valid (alphanumeric + basic chars)
            if len(extracted_value) >= 3 and extracted_value.replace('_', '').replace('-', '').isalnum():
                return 0.6

            return 0.3

        elif extraction_type == ExtractionType.STACK_SIZE:
            # Validate stack sizes are in reasonable ranges
            if not isinstance(extracted_value, (int, float)):
                return 0.0

            if 0.01 <= extracted_value <= 10000:  # Reasonable poker stack
                return 0.9

            return 0.3

        elif extraction_type == ExtractionType.POT_SIZE:
            if not isinstance(extracted_value, (int, float)):
                return 0.0

            if 0.0 <= extracted_value <= 50000:  # Reasonable pot
                return 0.9

            return 0.3

        return 0.5  # Default neutral confidence

    # ========================================================================
    # Reporting & Monitoring
    # ========================================================================

    def get_learning_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive learning system report.

        Returns:
            Dictionary with all learning metrics
        """
        report = {
            'timestamp': time.time(),
            'environment_profiles': {
                'total': len(self.environment_profiles),
                'profiles': []
            },
            'ocr_strategies': {},
            'adaptive_parameters': self.adaptive_params.copy(),
            'recent_performance': {},
            'cdp_learning': self.get_cdp_learning_stats(),
            'user_feedback': self.get_feedback_stats(),
            'learned_patterns': {
                'player_names_count': len(self.learned_patterns['player_names']),
            }
        }

        # Environment profiles summary
        for env_key, profile in self.environment_profiles.items():
            if profile.total_attempts > 0:
                report['environment_profiles']['profiles'].append({
                    'environment': env_key,
                    'success_rate': profile.get_success_rate(),
                    'attempts': profile.total_attempts,
                    'avg_time_ms': profile.avg_detection_time_ms,
                    'detection_threshold': profile.detection_threshold
                })

        # OCR strategy performance
        for ext_type, strategies in self.ocr_strategy_stats.items():
            if strategies:
                best_strategies = sorted(
                    strategies.values(),
                    key=lambda s: s.success_rate,
                    reverse=True
                )[:3]

                report['ocr_strategies'][ext_type] = [
                    {
                        'strategy_id': s.strategy_id,
                        'success_rate': s.success_rate,
                        'attempts': s.total_attempts,
                        'avg_time_ms': s.avg_execution_time_ms
                    }
                    for s in best_strategies
                ]

        # Recent performance
        if self.recent_detections:
            recent = list(self.recent_detections)
            report['recent_performance'] = {
                'sample_size': len(recent),
                'success_rate': sum(1 for r in recent if r[0]) / len(recent),
                'avg_confidence': np.mean([r[1] for r in recent if r[0]]),
                'avg_time_ms': np.mean([r[2] for r in recent])
            }

        return report

    def print_learning_report(self):
        """Print human-readable learning report."""
        report = self.get_learning_report()

        print("\n" + "=" * 80)
        print("🧠 SCRAPER LEARNING SYSTEM REPORT")
        print("=" * 80)

        # Environment Profiles
        print(f"\n📊 Environment Profiles: {report['environment_profiles']['total']}")
        for profile in report['environment_profiles']['profiles'][:5]:
            print(f"   • {profile['environment']}")
            print(f"     Success Rate: {profile['success_rate']:.1%} "
                  f"({profile['attempts']} attempts)")
            print(f"     Avg Time: {profile['avg_time_ms']:.1f}ms, "
                  f"Threshold: {profile['detection_threshold']:.2f}")

        # OCR Strategies
        print(f"\n🎯 OCR Strategy Performance:")
        for ext_type, strategies in report['ocr_strategies'].items():
            print(f"   {ext_type}:")
            for strat in strategies:
                print(f"      • {strat['strategy_id']}: {strat['success_rate']:.1%} "
                      f"({strat['attempts']} attempts, {strat['avg_time_ms']:.1f}ms)")

        # Recent Performance
        if report['recent_performance']:
            perf = report['recent_performance']
            print(f"\n📈 Recent Performance ({perf['sample_size']} samples):")
            print(f"   Success Rate: {perf['success_rate']:.1%}")
            print(f"   Avg Confidence: {perf.get('avg_confidence', 0):.1%}")
            print(f"   Avg Time: {perf['avg_time_ms']:.1f}ms")

        # CDP Learning
        if report['cdp_learning']['total_cdp_samples'] > 0:
            cdp = report['cdp_learning']
            print(f"\n🎓 CDP-Based Learning ({cdp['total_cdp_samples']} samples):")
            for ext_type, stats in cdp['accuracy_by_type'].items():
                print(f"   {ext_type}: {stats['avg_accuracy']:.1%} accuracy "
                      f"({stats['sample_count']} comparisons)")

        # User Feedback
        if report['user_feedback']['total_feedback'] > 0:
            fb = report['user_feedback']
            print(f"\n📝 User Feedback:")
            print(f"   Total Feedback: {fb['total_feedback']}")
            print(f"   Correction Rate: {fb['correction_rate']:.1%}")

        # Learned Patterns
        print(f"\n🔍 Learned Patterns:")
        print(f"   Player Names: {report['learned_patterns']['player_names_count']}")

        print("\n" + "=" * 80)

    # ========================================================================
    # Persistence
    # ========================================================================

    def _save_to_disk(self):
        """Save learning data to disk."""
        try:
            # Save environment profiles
            profiles_file = self.storage_dir / 'environment_profiles.json'
            profiles_data = {
                env_key: {
                    'env_signature': profile.env_signature,
                    'detection_threshold': profile.detection_threshold,
                    'success_count': profile.success_count,
                    'total_attempts': profile.total_attempts,
                    'avg_detection_time_ms': profile.avg_detection_time_ms,
                    'created_at': profile.created_at,
                    'last_updated': profile.last_updated
                }
                for env_key, profile in self.environment_profiles.items()
            }

            with open(profiles_file, 'w') as f:
                json.dump(profiles_data, f, indent=2)

            # Save OCR strategy stats
            strategies_file = self.storage_dir / 'ocr_strategies.json'
            strategies_data = {
                ext_type: {
                    strat_id: {
                        'strategy_id': stats.strategy_id,
                        'total_attempts': stats.total_attempts,
                        'successful_extractions': stats.successful_extractions,
                        'failed_extractions': stats.failed_extractions,
                        'avg_execution_time_ms': stats.avg_execution_time_ms,
                        'success_rate': stats.success_rate,
                        'last_success_time': stats.last_success_time
                    }
                    for strat_id, stats in strategies.items()
                }
                for ext_type, strategies in self.ocr_strategy_stats.items()
            }

            with open(strategies_file, 'w') as f:
                json.dump(strategies_data, f, indent=2)

            # Save adaptive parameters
            params_file = self.storage_dir / 'adaptive_params.json'
            with open(params_file, 'w') as f:
                json.dump(self.adaptive_params, f, indent=2)

            # Save learned patterns
            patterns_file = self.storage_dir / 'learned_patterns.json'
            patterns_data = {
                'player_names': list(self.learned_patterns['player_names']),
                'stack_ranges': self.learned_patterns['stack_ranges'],
                'pot_multipliers': self.learned_patterns['pot_multipliers']
            }

            with open(patterns_file, 'w') as f:
                json.dump(patterns_data, f, indent=2)

            logger.debug(f"💾 Learning data saved to {self.storage_dir}")

        except Exception as e:
            logger.error(f"Failed to save learning data: {e}")

    def _load_from_disk(self):
        """Load learning data from disk."""
        try:
            # Load environment profiles
            profiles_file = self.storage_dir / 'environment_profiles.json'
            if profiles_file.exists():
                with open(profiles_file, 'r') as f:
                    profiles_data = json.load(f)

                for env_key, data in profiles_data.items():
                    profile = EnvironmentProfile(
                        env_signature=data['env_signature'],
                        detection_threshold=data.get('detection_threshold', 0.40),
                        success_count=data.get('success_count', 0),
                        total_attempts=data.get('total_attempts', 0),
                        avg_detection_time_ms=data.get('avg_detection_time_ms', 0.0),
                        created_at=data.get('created_at', time.time()),
                        last_updated=data.get('last_updated', time.time())
                    )
                    self.environment_profiles[env_key] = profile

            # Load OCR strategy stats
            strategies_file = self.storage_dir / 'ocr_strategies.json'
            if strategies_file.exists():
                with open(strategies_file, 'r') as f:
                    strategies_data = json.load(f)

                for ext_type, strategies in strategies_data.items():
                    for strat_id, data in strategies.items():
                        stats = OCRStrategyStats(
                            strategy_id=data['strategy_id'],
                            total_attempts=data.get('total_attempts', 0),
                            successful_extractions=data.get('successful_extractions', 0),
                            failed_extractions=data.get('failed_extractions', 0),
                            avg_execution_time_ms=data.get('avg_execution_time_ms', 0.0),
                            success_rate=data.get('success_rate', 0.0),
                            last_success_time=data.get('last_success_time')
                        )
                        self.ocr_strategy_stats[ext_type][strat_id] = stats

            # Load adaptive parameters
            params_file = self.storage_dir / 'adaptive_params.json'
            if params_file.exists():
                with open(params_file, 'r') as f:
                    self.adaptive_params.update(json.load(f))

            # Load learned patterns
            patterns_file = self.storage_dir / 'learned_patterns.json'
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    patterns_data = json.load(f)
                    self.learned_patterns['player_names'] = set(patterns_data.get('player_names', []))
                    self.learned_patterns['stack_ranges'] = patterns_data.get('stack_ranges', {})
                    self.learned_patterns['pot_multipliers'] = patterns_data.get('pot_multipliers', [])

            logger.debug(f"📂 Learning data loaded from {self.storage_dir}")

        except Exception as e:
            logger.warning(f"Could not load learning data: {e}")

    def save(self):
        """Manually trigger save to disk."""
        self._save_to_disk()

    def reset_learning_data(self):
        """Reset all learning data (use with caution)."""
        self.environment_profiles.clear()
        self.ocr_strategy_stats.clear()
        self.adaptive_params = {
            'detection_threshold': 0.40,
            'min_card_area': 1500,
            'max_card_area': 300000,
            'card_aspect_min': 0.5,
            'card_aspect_max': 1.0,
            'ocr_scale_factor': 4.0,
        }
        self.recent_detections.clear()
        self.recent_extractions.clear()
        self.feedback_history.clear()
        self.cdp_ground_truth_history.clear()
        self.ocr_vs_cdp_accuracy.clear()
        self.learned_patterns = {
            'player_names': set(),
            'stack_ranges': {},
            'pot_multipliers': [],
        }

        logger.warning("🗑️ All learning data has been reset")


# ============================================================================
# Convenience Functions
# ============================================================================

def create_learning_system(storage_dir: Optional[Path] = None) -> ScraperLearningSystem:
    """
    Create a new learning system instance.

    Args:
        storage_dir: Optional custom storage directory

    Returns:
        Configured ScraperLearningSystem
    """
    return ScraperLearningSystem(storage_dir)


if __name__ == '__main__':
    # Test the learning system
    print("🧠 Scraper Learning System - Test Mode")
    print("=" * 60)

    # Create learning system
    learning = create_learning_system()

    # Simulate some learning
    print("\n📊 Simulating learning...")

    # Simulate detection results
    for i in range(50):
        success = np.random.random() > 0.2  # 80% success rate
        confidence = np.random.uniform(0.6, 0.95) if success else np.random.uniform(0.2, 0.5)
        time_ms = np.random.uniform(40, 100)
        learning.record_detection_result(success, confidence, time_ms)

    # Simulate OCR strategy learning
    strategies = ['otsu', 'adaptive', 'clahe', 'bilateral']
    for _ in range(100):
        strategy = np.random.choice(strategies)
        ext_type = np.random.choice([ExtractionType.POT_SIZE, ExtractionType.PLAYER_NAME])

        if np.random.random() > 0.3:  # 70% success
            learning.record_ocr_success(ext_type, strategy, np.random.uniform(5, 15))
        else:
            learning.record_ocr_failure(ext_type, strategy)

    # Generate report
    print("\n" + "=" * 60)
    learning.print_learning_report()

    # Save data
    learning.save()
    print("\n✓ Learning data saved")
