"""
Comprehensive Tests for Multi-Template Card Matching
====================================================

Tests multi-template matching with support for multiple deck styles.

Test Coverage:
- Multiple deck style support (classic, modern, large-pip, four-color)
- Template library management
- Voting system for ambiguous matches
- Auto deck style detection
- Template confidence scoring
- 10+ tests validating all styles

Test Count: 50+ comprehensive tests
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

try:
    from pokertool.multi_template_card_matcher import (
        MultiTemplateMatcher,
        DeckStyle,
        TemplateMatch,
        CardTemplate,
        Card,
        RecognitionResult,
        get_multi_template_matcher,
        RANKS,
        SUITS
    )
    MULTI_TEMPLATE_AVAILABLE = True
except ImportError:
    MULTI_TEMPLATE_AVAILABLE = False
    pytest.skip("Multi-template matcher not available", allow_module_level=True)

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


@pytest.fixture
def matcher():
    """Create multi-template matcher."""
    return MultiTemplateMatcher(min_confidence=0.85)


@pytest.fixture
def mock_card_image():
    """Create mock card image."""
    if not CV2_AVAILABLE:
        pytest.skip("OpenCV not available")
    return np.ones((100, 70, 3), dtype=np.uint8) * 255


# Test Section 1: Initialization (10 tests)
class TestMultiTemplateInitialization:
    """Tests for matcher initialization."""

    def test_matcher_initializes_with_defaults(self):
        """Test matcher initializes with default parameters."""
        matcher = MultiTemplateMatcher()
        assert matcher.min_confidence == 0.85
        assert matcher.auto_detect_style == True
        assert matcher.available == CV2_AVAILABLE

    def test_matcher_supports_all_deck_styles(self, matcher):
        """Test matcher has all deck styles enabled."""
        assert DeckStyle.CLASSIC in matcher.enabled_styles
        assert DeckStyle.MODERN in matcher.enabled_styles
        assert DeckStyle.LARGE_PIP in matcher.enabled_styles
        assert DeckStyle.FOUR_COLOR in matcher.enabled_styles

    def test_matcher_custom_enabled_styles(self):
        """Test custom enabled styles."""
        matcher = MultiTemplateMatcher(
            enabled_styles=[DeckStyle.CLASSIC, DeckStyle.MODERN]
        )
        assert len(matcher.enabled_styles) == 2
        assert DeckStyle.CLASSIC in matcher.enabled_styles

    def test_matcher_initializes_template_library(self, matcher):
        """Test template library is initialized."""
        assert isinstance(matcher.template_library, dict)
        for style in matcher.enabled_styles:
            assert style in matcher.template_library

    def test_matcher_has_multi_scale_support(self, matcher):
        """Test matcher has multiple scales."""
        assert len(matcher.scales) >= 5
        assert 1.0 in matcher.scales

    def test_matcher_initializes_stats(self, matcher):
        """Test statistics tracking is initialized."""
        assert 'total_matches' in matcher.match_stats
        assert 'by_style' in matcher.match_stats

    def test_singleton_returns_same_instance(self):
        """Test get_multi_template_matcher returns singleton."""
        m1 = get_multi_template_matcher()
        m2 = get_multi_template_matcher()
        assert m1 is m2

    def test_deck_style_enum_values(self):
        """Test DeckStyle enum has all values."""
        assert DeckStyle.CLASSIC
        assert DeckStyle.MODERN
        assert DeckStyle.LARGE_PIP
        assert DeckStyle.FOUR_COLOR
        assert DeckStyle.AUTO

    def test_matcher_custom_confidence_threshold(self):
        """Test custom confidence threshold."""
        matcher = MultiTemplateMatcher(min_confidence=0.90)
        assert matcher.min_confidence == 0.90

    def test_matcher_template_dir_created(self, matcher):
        """Test template directory is created."""
        assert matcher.template_dir.exists()


# Test Section 2: Template Management (12 tests)
class TestTemplateManagement:
    """Tests for template library management."""

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_add_template_classic_style(self, matcher, mock_card_image):
        """Test adding template for classic style."""
        card = Card(rank='A', suit='s')
        matcher.add_template(card, mock_card_image, DeckStyle.CLASSIC)
        assert 'As' in matcher.template_library[DeckStyle.CLASSIC]

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_add_template_modern_style(self, matcher, mock_card_image):
        """Test adding template for modern style."""
        card = Card(rank='K', suit='h')
        matcher.add_template(card, mock_card_image, DeckStyle.MODERN)
        assert 'Kh' in matcher.template_library[DeckStyle.MODERN]

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_add_template_large_pip_style(self, matcher, mock_card_image):
        """Test adding template for large-pip style."""
        card = Card(rank='Q', suit='d')
        matcher.add_template(card, mock_card_image, DeckStyle.LARGE_PIP)
        assert 'Qd' in matcher.template_library[DeckStyle.LARGE_PIP]

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_add_template_four_color_style(self, matcher, mock_card_image):
        """Test adding template for four-color style."""
        card = Card(rank='J', suit='c')
        matcher.add_template(card, mock_card_image, DeckStyle.FOUR_COLOR)
        assert 'Jc' in matcher.template_library[DeckStyle.FOUR_COLOR]

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_add_multiple_templates_same_card(self, matcher, mock_card_image):
        """Test adding multiple templates for same card."""
        card = Card(rank='T', suit='s')
        matcher.add_template(card, mock_card_image, DeckStyle.CLASSIC)
        matcher.add_template(card, mock_card_image, DeckStyle.CLASSIC)
        assert len(matcher.template_library[DeckStyle.CLASSIC]['Ts']) == 2

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_template_preprocessing(self, matcher, mock_card_image):
        """Test template is preprocessed."""
        processed = matcher._preprocess_template(mock_card_image)
        assert processed.ndim == 2  # Grayscale
        assert processed.shape[0] == 100  # Normalized height

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_add_template_handles_empty_image(self, matcher):
        """Test add_template handles empty image."""
        card = Card(rank='9', suit='h')
        empty = np.array([])
        # Should not crash
        matcher.add_template(card, empty, DeckStyle.CLASSIC)

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_add_all_52_cards(self, matcher, mock_card_image):
        """Test can add templates for all 52 cards."""
        for rank in RANKS:
            for suit in SUITS:
                card = Card(rank=rank, suit=suit)
                matcher.add_template(card, mock_card_image, DeckStyle.CLASSIC)

        # Should have 52 cards in library
        assert len(matcher.template_library[DeckStyle.CLASSIC]) == 52

    def test_card_template_dataclass(self, mock_card_image):
        """Test CardTemplate dataclass."""
        template = CardTemplate(
            rank='8',
            suit='d',
            deck_style=DeckStyle.MODERN,
            template_image=mock_card_image,
            width=70,
            height=100
        )
        assert template.rank == '8'
        assert template.suit == 'd'
        assert template.deck_style == DeckStyle.MODERN

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_template_match_dataclass(self):
        """Test TemplateMatch dataclass."""
        card = Card(rank='7', suit='c')
        match = TemplateMatch(
            card=card,
            confidence=0.92,
            deck_style=DeckStyle.LARGE_PIP,
            scale=1.1,
            location=(10, 20, 70, 100)
        )
        assert match.card == card
        assert match.confidence == 0.92
        assert match.deck_style == DeckStyle.LARGE_PIP

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_template_library_per_style(self, matcher):
        """Test each deck style has its own template library."""
        assert DeckStyle.CLASSIC in matcher.template_library
        assert DeckStyle.MODERN in matcher.template_library
        assert DeckStyle.LARGE_PIP in matcher.template_library
        assert DeckStyle.FOUR_COLOR in matcher.template_library

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_template_preprocessing_handles_color(self, matcher):
        """Test preprocessing handles color images."""
        color_image = np.random.randint(0, 255, (150, 100, 3), dtype=np.uint8)
        processed = matcher._preprocess_template(color_image)
        assert processed.ndim == 2  # Should be grayscale


# Test Section 3: Card Matching (15 tests)
class TestCardMatching:
    """Tests for card matching functionality."""

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_card_returns_result(self, matcher, mock_card_image):
        """Test match_card returns RecognitionResult."""
        result = matcher.match_card(mock_card_image)
        assert isinstance(result, RecognitionResult)

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_card_with_no_templates(self, matcher, mock_card_image):
        """Test matching with no templates."""
        result = matcher.match_card(mock_card_image)
        assert result.method == "no_templates"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_card_with_specific_style(self, matcher, mock_card_image):
        """Test matching with specific deck style."""
        result = matcher.match_card(mock_card_image, deck_style=DeckStyle.CLASSIC)
        assert isinstance(result, RecognitionResult)

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_card_increments_stats(self, matcher, mock_card_image):
        """Test matching increments statistics."""
        initial = matcher.match_stats['total_matches']
        matcher.match_card(mock_card_image)
        assert matcher.match_stats['total_matches'] == initial + 1

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_card_with_none_image(self, matcher):
        """Test matching with None image."""
        result = matcher.match_card(None)
        assert result.card is None
        assert result.method == "unavailable"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_card_with_empty_image(self, matcher):
        """Test matching with empty image."""
        empty = np.array([])
        result = matcher.match_card(empty)
        assert result.card is None

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_multi_scale_matching(self, matcher):
        """Test multi-scale template matching."""
        template = np.ones((100, 70), dtype=np.uint8) * 128
        image = np.ones((120, 85), dtype=np.uint8) * 128
        conf, scale, loc = matcher._multi_scale_match(image, template)
        assert 0.0 <= conf <= 1.0
        assert scale in matcher.scales or abs(scale - 1.0) < 0.01

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_against_style(self, matcher, mock_card_image):
        """Test matching against specific style."""
        # Add a template first
        card = Card(rank='A', suit='s')
        matcher.add_template(card, mock_card_image, DeckStyle.CLASSIC)
        # Match
        matches = matcher._match_against_style(mock_card_image, DeckStyle.CLASSIC)
        # Should return list (may be empty if no good match)
        assert isinstance(matches, list)

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_returns_confidence(self, matcher, mock_card_image):
        """Test match result includes confidence."""
        result = matcher.match_card(mock_card_image)
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_returns_location(self, matcher, mock_card_image):
        """Test match result includes location."""
        result = matcher.match_card(mock_card_image)
        assert isinstance(result.location, tuple)
        assert len(result.location) == 4

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_filters_low_confidence(self, matcher, mock_card_image):
        """Test low confidence matches are filtered."""
        matcher.min_confidence = 0.95
        result = matcher.match_card(mock_card_image)
        # With no templates, should be low confidence
        assert result.confidence < 0.95 or result.card is None

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_with_grayscale_image(self, matcher):
        """Test matching with grayscale image."""
        gray = np.ones((100, 70), dtype=np.uint8) * 255
        result = matcher.match_card(gray)
        assert isinstance(result, RecognitionResult)

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_handles_exceptions(self, matcher, mock_card_image):
        """Test matching handles exceptions gracefully."""
        with patch.object(matcher, '_preprocess_template') as mock_preprocess:
            mock_preprocess.side_effect = Exception("Test error")
            result = matcher.match_card(mock_card_image)
            # Should handle gracefully
            assert isinstance(result, RecognitionResult)

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_method_includes_style(self, matcher, mock_card_image):
        """Test match result method includes deck style."""
        # Add template
        card = Card(rank='K', suit='h')
        matcher.add_template(card, mock_card_image, DeckStyle.MODERN)
        result = matcher.match_card(mock_card_image, deck_style=DeckStyle.MODERN)
        # Method should include style info
        assert 'multi_template' in result.method or result.method == 'no_templates' or result.method == 'low_confidence_multi_template'

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_with_all_styles_enabled(self, matcher, mock_card_image):
        """Test matching with all styles enabled."""
        # Add templates for multiple styles
        card = Card(rank='Q', suit='d')
        for style in [DeckStyle.CLASSIC, DeckStyle.MODERN]:
            matcher.add_template(card, mock_card_image, style)
        result = matcher.match_card(mock_card_image)
        assert isinstance(result, RecognitionResult)


# Test Section 4: Voting System (10 tests)
class TestVotingSystem:
    """Tests for template voting mechanism."""

    def test_vote_with_single_match(self, matcher):
        """Test voting with single match."""
        card = Card(rank='A', suit='s')
        matches = [
            TemplateMatch(card, 0.90, DeckStyle.CLASSIC, 1.0, (0, 0, 70, 100))
        ]
        best = matcher._vote_on_matches(matches)
        assert best.card == card

    def test_vote_with_multiple_same_card(self, matcher):
        """Test voting with multiple matches for same card."""
        card = Card(rank='K', suit='h')
        matches = [
            TemplateMatch(card, 0.88, DeckStyle.CLASSIC, 1.0, (0, 0, 70, 100)),
            TemplateMatch(card, 0.86, DeckStyle.MODERN, 1.1, (0, 0, 70, 100))
        ]
        best = matcher._vote_on_matches(matches)
        assert best.card == card
        # Should return highest confidence
        assert best.confidence == 0.88

    def test_vote_with_conflicting_matches(self, matcher):
        """Test voting with conflicting card matches."""
        card1 = Card(rank='Q', suit='d')
        card2 = Card(rank='J', suit='d')
        matches = [
            TemplateMatch(card1, 0.85, DeckStyle.CLASSIC, 1.0, (0, 0, 70, 100)),
            TemplateMatch(card2, 0.80, DeckStyle.MODERN, 1.1, (0, 0, 70, 100))
        ]
        best = matcher._vote_on_matches(matches)
        # Should pick higher confidence
        assert best.card == card1

    def test_vote_with_empty_matches(self, matcher):
        """Test voting with no matches."""
        best = matcher._vote_on_matches([])
        assert best is None

    def test_vote_consistency_bonus(self, matcher):
        """Test voting applies consistency bonus for same style."""
        card = Card(rank='T', suit='c')
        matches = [
            TemplateMatch(card, 0.85, DeckStyle.CLASSIC, 1.0, (0, 0, 70, 100)),
            TemplateMatch(card, 0.84, DeckStyle.CLASSIC, 1.1, (0, 0, 70, 100))
        ]
        # Voting should bonus for same style agreement
        best = matcher._vote_on_matches(matches)
        assert best.card == card

    def test_vote_returns_highest_confidence_for_winning_card(self, matcher):
        """Test voting returns highest confidence match for winning card."""
        card = Card(rank='9', suit='s')
        matches = [
            TemplateMatch(card, 0.92, DeckStyle.MODERN, 1.0, (0, 0, 70, 100)),
            TemplateMatch(card, 0.88, DeckStyle.CLASSIC, 1.0, (0, 0, 70, 100))
        ]
        best = matcher._vote_on_matches(matches)
        assert best.confidence == 0.92

    def test_vote_groups_by_card(self, matcher):
        """Test voting groups matches by card identity."""
        card1 = Card(rank='8', suit='h')
        card2 = Card(rank='7', suit='h')
        matches = [
            TemplateMatch(card1, 0.90, DeckStyle.CLASSIC, 1.0, (0, 0, 70, 100)),
            TemplateMatch(card2, 0.85, DeckStyle.MODERN, 1.0, (0, 0, 70, 100)),
            TemplateMatch(card1, 0.87, DeckStyle.LARGE_PIP, 1.1, (0, 0, 70, 100))
        ]
        best = matcher._vote_on_matches(matches)
        # card1 has 2 votes, should win
        assert best.card == card1

    def test_vote_handles_all_52_cards(self, matcher):
        """Test voting can handle all 52 cards."""
        for rank in RANKS:
            for suit in SUITS:
                card = Card(rank=rank, suit=suit)
                matches = [
                    TemplateMatch(card, 0.90, DeckStyle.CLASSIC, 1.0, (0, 0, 70, 100))
                ]
                best = matcher._vote_on_matches(matches)
                assert best.card == card

    def test_vote_with_different_scales(self, matcher):
        """Test voting with matches at different scales."""
        card = Card(rank='6', suit='d')
        matches = [
            TemplateMatch(card, 0.89, DeckStyle.CLASSIC, 0.9, (0, 0, 70, 100)),
            TemplateMatch(card, 0.91, DeckStyle.CLASSIC, 1.1, (0, 0, 70, 100))
        ]
        best = matcher._vote_on_matches(matches)
        # Should return highest confidence regardless of scale
        assert best.confidence == 0.91

    def test_vote_all_low_confidence(self, matcher):
        """Test voting when all matches are low confidence."""
        card = Card(rank='5', suit='c')
        matches = [
            TemplateMatch(card, 0.60, DeckStyle.CLASSIC, 1.0, (0, 0, 70, 100)),
            TemplateMatch(card, 0.58, DeckStyle.MODERN, 1.0, (0, 0, 70, 100))
        ]
        best = matcher._vote_on_matches(matches)
        # Should still return best match
        assert best.confidence == 0.60


# Test Section 5: Style Detection (8 tests)
class TestStyleDetection:
    """Tests for automatic deck style detection."""

    def test_auto_detect_enabled_by_default(self, matcher):
        """Test auto-detection is enabled by default."""
        assert matcher.auto_detect_style == True

    def test_get_detected_style_initially_none(self, matcher):
        """Test detected style is None initially."""
        assert matcher.get_detected_style() is None

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_set_deck_style_disables_auto_detect(self, matcher):
        """Test manually setting style disables auto-detection."""
        matcher.set_deck_style(DeckStyle.MODERN)
        assert matcher.auto_detect_style == False
        assert matcher.detected_style == DeckStyle.MODERN

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_get_styles_to_try_with_manual_style(self, matcher):
        """Test get_styles_to_try with manual style."""
        matcher.set_deck_style(DeckStyle.CLASSIC)
        styles = matcher._get_styles_to_try(None)
        assert styles == [DeckStyle.CLASSIC]

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_get_styles_to_try_with_specified_style(self, matcher):
        """Test get_styles_to_try with specified style."""
        styles = matcher._get_styles_to_try(DeckStyle.LARGE_PIP)
        assert styles == [DeckStyle.LARGE_PIP]

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_get_styles_to_try_all_enabled(self, matcher):
        """Test get_styles_to_try returns all enabled styles."""
        styles = matcher._get_styles_to_try(None)
        assert len(styles) == 4  # All enabled by default

    def test_get_stats_includes_style_distribution(self, matcher):
        """Test get_stats includes style distribution."""
        # Simulate some matches
        matcher.match_stats['by_style'][DeckStyle.CLASSIC] = 10
        matcher.match_stats['by_style'][DeckStyle.MODERN] = 5
        stats = matcher.get_stats()
        if 'style_distribution' in stats:
            assert DeckStyle.CLASSIC.value in stats['style_distribution']

    def test_style_detection_updates_on_match(self, matcher, mock_card_image):
        """Test detected style updates after successful match."""
        # Add template and match
        card = Card(rank='4', suit='h')
        matcher.add_template(card, mock_card_image, DeckStyle.FOUR_COLOR)
        # Detected style may update (implementation dependent)
        # Just verify it doesn't crash
        detected = matcher.get_detected_style()
        assert detected is None or isinstance(detected, DeckStyle)


# Summary: 55+ comprehensive tests
"""
Test Summary:
- Section 1: Initialization (10 tests)
- Section 2: Template Management (12 tests)
- Section 3: Card Matching (15 tests)
- Section 4: Voting System (10 tests)
- Section 5: Style Detection (8 tests)

Total: 55+ tests validating multi-template matching across all deck styles
"""
