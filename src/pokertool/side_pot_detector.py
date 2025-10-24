"""Side Pot Detection Module

Detects and tracks multiple pots (main pot + side pots) in poker games.
Side pots occur when players are all-in with different stack sizes.

Enhanced Features:
- Player-based pot calculation from bet amounts
- Visual detection from screen regions
- Pot odds calculations per pot
- Eligible player tracking
"""

from typing import List, Optional, Tuple, Set, Dict
from dataclasses import dataclass, field
from enum import Enum
import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class PotType(Enum):
    """Type of pot."""
    MAIN = "main"
    SIDE = "side"


@dataclass
class Player:
    """Player information for pot calculations."""
    seat: int
    name: str
    stack: float
    bet_amount: float
    is_all_in: bool = False
    is_folded: bool = False


@dataclass
class PotInfo:
    """Information about a detected pot."""
    amount: float
    confidence: float
    is_main_pot: bool
    position: Tuple[int, int, int, int]  # (x0, y0, x1, y1)
    pot_number: int  # 0 for main pot, 1,2,3... for side pots
    eligible_players: Set[int] = field(default_factory=set)  # Seat numbers
    all_in_amount: Optional[float] = None

    def get_pot_odds(self, bet_to_call: float) -> Optional[float]:
        """Calculate pot odds for this pot."""
        if bet_to_call <= 0:
            return None
        return self.amount / bet_to_call


class SidePotDetector:
    """Detect main pot and side pots from poker table screenshots."""

    def __init__(self):
        self.last_pots: List[PotInfo] = []
        self.pot_change_threshold = 0.01  # Minimum change to consider as different pot

    def detect_all_pots(
        self,
        image: np.ndarray,
        main_pot_amount: float,
        main_pot_confidence: float,
        ocr_func=None
    ) -> List[PotInfo]:
        """
        Detect all pots (main + side pots) from table screenshot.

        Args:
            image: BGR image of poker table
            main_pot_amount: Already detected main pot amount
            main_pot_confidence: Confidence of main pot detection
            ocr_func: Optional OCR function for detecting side pot amounts

        Returns:
            List of PotInfo objects, with main pot first, then side pots
        """
        pots = []

        # Add main pot
        h, w = image.shape[:2]
        main_pot_roi = (
            int(w * 0.3), int(h * 0.35),
            int(w * 0.7), int(h * 0.65)
        )

        main_pot = PotInfo(
            amount=main_pot_amount,
            confidence=main_pot_confidence,
            is_main_pot=True,
            position=main_pot_roi,
            pot_number=0
        )
        pots.append(main_pot)

        # Detect side pots if OCR function provided
        if ocr_func and main_pot_amount > 0:
            side_pots = self._detect_side_pots(image, main_pot_roi, ocr_func)
            pots.extend(side_pots)

        self.last_pots = pots
        return pots

    def _detect_side_pots(
        self,
        image: np.ndarray,
        main_pot_roi: Tuple[int, int, int, int],
        ocr_func
    ) -> List[PotInfo]:
        """
        Detect side pots near the main pot.

        Side pots are typically displayed above/below or to the sides of main pot.

        Args:
            image: BGR image of poker table
            main_pot_roi: ROI of main pot (x0, y0, x1, y1)
            ocr_func: Function to extract pot amounts from ROIs

        Returns:
            List of PotInfo objects for side pots
        """
        side_pots = []
        h, w = image.shape[:2]
        main_x0, main_y0, main_x1, main_y1 = main_pot_roi

        # Define search regions for side pots
        # Typically side pots appear above main pot or to the sides
        search_regions = self._get_side_pot_search_regions(w, h, main_pot_roi)

        for idx, (region_x0, region_y0, region_x1, region_y1) in enumerate(search_regions):
            # Extract ROI
            roi = image[region_y0:region_y1, region_x0:region_x1]

            if roi.size == 0:
                continue

            # Try to extract amount using OCR
            try:
                amount = self._extract_pot_amount(roi, ocr_func)

                if amount > 0:
                    # Confidence is lower for side pots (harder to detect)
                    confidence = 0.75  # Lower confidence than main pot

                    side_pot = PotInfo(
                        amount=amount,
                        confidence=confidence,
                        is_main_pot=False,
                        position=(region_x0, region_y0, region_x1, region_y1),
                        pot_number=len(side_pots) + 1
                    )
                    side_pots.append(side_pot)
                    logger.info(f"Side pot #{len(side_pots)} detected: ${amount:.2f} (confidence: {confidence:.2%})")

                    # Limit to 3 side pots (most games won't have more)
                    if len(side_pots) >= 3:
                        break

            except Exception as e:
                logger.debug(f"Side pot detection failed for region {idx}: {e}")
                continue

        return side_pots

    def _get_side_pot_search_regions(
        self,
        width: int,
        height: int,
        main_pot_roi: Tuple[int, int, int, int]
    ) -> List[Tuple[int, int, int, int]]:
        """
        Get regions to search for side pots.

        Returns list of (x0, y0, x1, y1) tuples.
        """
        main_x0, main_y0, main_x1, main_y1 = main_pot_roi
        main_height = main_y1 - main_y0
        main_width = main_x1 - main_x0

        regions = []

        # Region 1: Above main pot
        regions.append((
            main_x0,
            max(0, main_y0 - int(main_height * 0.8)),
            main_x1,
            main_y0 - 5
        ))

        # Region 2: Below main pot
        regions.append((
            main_x0,
            main_y1 + 5,
            main_x1,
            min(height, main_y1 + int(main_height * 0.8))
        ))

        # Region 3: Left of main pot
        regions.append((
            max(0, main_x0 - int(main_width * 0.6)),
            main_y0,
            main_x0 - 5,
            main_y1
        ))

        # Region 4: Right of main pot
        regions.append((
            main_x1 + 5,
            main_y0,
            min(width, main_x1 + int(main_width * 0.6)),
            main_y1
        ))

        # Filter out invalid regions
        valid_regions = []
        for x0, y0, x1, y1 in regions:
            if x1 > x0 and y1 > y0:
                valid_regions.append((x0, y0, x1, y1))

        return valid_regions

    def _extract_pot_amount(self, roi: np.ndarray, ocr_func) -> float:
        """
        Extract pot amount from ROI using OCR.

        Args:
            roi: Region of interest containing pot text
            ocr_func: OCR function that takes image and returns float

        Returns:
            Pot amount as float, or 0.0 if extraction fails
        """
        if roi.size == 0:
            return 0.0

        # Preprocess ROI for better OCR
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Apply threshold to isolate text
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Try OCR
        try:
            amount = ocr_func(thresh)
            return amount if amount > 0 else 0.0
        except Exception as e:
            logger.debug(f"OCR extraction failed: {e}")
            return 0.0

    def get_total_pot(self) -> float:
        """Get total of all pots (main + side pots)."""
        return sum(pot.amount for pot in self.last_pots)

    def get_side_pot_count(self) -> int:
        """Get number of side pots detected."""
        return sum(1 for pot in self.last_pots if not pot.is_main_pot)

    def has_side_pots(self) -> bool:
        """Check if side pots were detected."""
        return self.get_side_pot_count() > 0

    def get_pot_distribution(self) -> dict:
        """Get distribution of pot amounts."""
        return {
            'main_pot': next((p.amount for p in self.last_pots if p.is_main_pot), 0.0),
            'side_pots': [p.amount for p in self.last_pots if not p.is_main_pot],
            'total': self.get_total_pot(),
            'side_pot_count': self.get_side_pot_count()
        }

    def calculate_pots_from_players(
        self,
        players: List[Player],
        total_pot: float
    ) -> List[PotInfo]:
        """
        Calculate pots from player bet amounts (logic-based, not visual).

        Args:
            players: List of players with bet amounts and states
            total_pot: Total pot amount

        Returns:
            List of PotInfo objects
        """
        # Filter active players
        active_players = [p for p in players if not p.is_folded]

        if not active_players:
            return []

        # Find all-in players
        all_in_players = [p for p in active_players if p.is_all_in]

        if not all_in_players:
            # No side pots - just main pot
            main_pot = PotInfo(
                amount=total_pot,
                confidence=0.95,
                is_main_pot=True,
                position=(0, 0, 0, 0),  # No visual position
                pot_number=0,
                eligible_players={p.seat for p in active_players}
            )
            return [main_pot]

        # Calculate pots using algorithm
        pots = self._calculate_pots_from_bets(active_players, all_in_players)

        return pots

    def _calculate_pots_from_bets(
        self,
        active_players: List[Player],
        all_in_players: List[Player]
    ) -> List[PotInfo]:
        """
        Calculate main pot and side pots from bet amounts.

        Algorithm:
        1. Sort all-in players by bet amount (lowest to highest)
        2. Create pot for each all-in level
        3. Track eligible players for each pot
        """
        pots: List[PotInfo] = []

        # Sort all-in players by bet amount
        sorted_all_ins = sorted(all_in_players, key=lambda p: p.bet_amount)

        # Track remaining bets
        remaining_bets = {p.seat: p.bet_amount for p in active_players}

        pot_index = 0
        previous_level = 0.0

        # Create pots for each all-in level
        for all_in_player in sorted_all_ins:
            all_in_level = all_in_player.bet_amount

            if all_in_level <= previous_level:
                continue

            # Calculate pot amount at this level
            pot_amount = 0.0
            eligible = set()

            for player in active_players:
                contribution = min(remaining_bets[player.seat], all_in_level) - previous_level

                if contribution > 0:
                    pot_amount += contribution
                    remaining_bets[player.seat] -= contribution
                    eligible.add(player.seat)

            if pot_amount > 0:
                is_main = pot_index == 0
                pots.append(PotInfo(
                    amount=pot_amount,
                    confidence=0.90,
                    is_main_pot=is_main,
                    position=(0, 0, 0, 0),
                    pot_number=pot_index,
                    eligible_players=eligible,
                    all_in_amount=all_in_level if not is_main else None
                ))
                pot_index += 1

            previous_level = all_in_level

        # Create final pot for remaining bets
        final_amount = sum(remaining_bets.values())
        if final_amount > 0:
            eligible = {p.seat for p in active_players if remaining_bets[p.seat] > 0}
            is_main = pot_index == 0

            pots.append(PotInfo(
                amount=final_amount,
                confidence=0.90,
                is_main_pot=is_main,
                position=(0, 0, 0, 0),
                pot_number=pot_index,
                eligible_players=eligible,
                all_in_amount=None
            ))

        return pots

    def get_pots_for_player(self, seat: int) -> List[PotInfo]:
        """Get all pots that a player is eligible for."""
        return [pot for pot in self.last_pots if seat in pot.eligible_players]

    def calculate_total_pot_odds(
        self,
        seat: int,
        bet_to_call: float
    ) -> Optional[float]:
        """
        Calculate combined pot odds for all pots player is eligible for.

        Args:
            seat: Player's seat number
            bet_to_call: Amount player must call

        Returns:
            Combined pot odds or None if invalid
        """
        if bet_to_call <= 0:
            return None

        player_pots = self.get_pots_for_player(seat)
        total_amount = sum(pot.amount for pot in player_pots)

        if total_amount == 0:
            return None

        return total_amount / bet_to_call
