"""
SmartHelper API Router

FastAPI router providing real-time poker decision recommendations
with factor-based reasoning and GTO frequencies.

Author: PokerTool Team
Created: 2025-10-22
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from pokertool.smarthelper_engine import (
    SmartHelperEngine,
    GameState as EngineGameState,
    Opponent as EngineOpponent,
    Street,
    PokerAction
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/smarthelper",
    tags=["SmartHelper"],
    responses={404: {"description": "Not found"}}
)

# Initialize engine singleton
_engine: Optional[SmartHelperEngine] = None


def get_engine() -> SmartHelperEngine:
    """Get or create SmartHelper engine instance"""
    global _engine
    if _engine is None:
        _engine = SmartHelperEngine()
        logger.info("SmartHelper engine initialized")
    return _engine


# Pydantic models for request/response

class OpponentRequest(BaseModel):
    """Opponent data in request"""
    name: str
    position: str
    stack: float
    stats: Optional[Dict[str, Any]] = None


class ActionHistoryItem(BaseModel):
    """Action history item"""
    player: str
    action: str
    amount: Optional[float] = None


class GameStateRequest(BaseModel):
    """Game state in request"""
    hero_cards: Optional[List[str]] = None
    hero_position: Optional[str] = None
    hero_stack: float = 0.0
    community_cards: List[str] = Field(default_factory=list)
    pot_size: float = 0.0
    bet_to_call: float = 0.0
    street: str = "preflop"
    opponents: List[OpponentRequest] = Field(default_factory=list)
    action_history: List[ActionHistoryItem] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    """Request model for recommendation"""
    game_state: GameStateRequest
    timestamp: Optional[int] = None


class DecisionFactorResponse(BaseModel):
    """Decision factor in response"""
    name: str
    score: float
    weight: float
    description: str
    details: Optional[str] = None


class GTOFrequenciesResponse(BaseModel):
    """GTO frequencies in response"""
    fold: float = 0.0
    check: float = 0.0
    call: float = 0.0
    bet: float = 0.0
    raise_: float = Field(0.0, alias="raise")
    all_in: float = 0.0

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "fold": 30.0,
                "check": 20.0,
                "call": 25.0,
                "bet": 15.0,
                "raise": 8.0,
                "all_in": 2.0
            }
        }


class RecommendationResponse(BaseModel):
    """Response model for recommendation"""
    action: str
    amount: Optional[float] = None
    gtoFrequencies: GTOFrequenciesResponse
    strategicReasoning: str
    confidence: float
    factors: List[DecisionFactorResponse]
    netConfidence: float
    timestamp: int


def convert_game_state(request_state: GameStateRequest) -> EngineGameState:
    """Convert request game state to engine game state"""

    # Convert street string to enum
    street_map = {
        "preflop": Street.PREFLOP,
        "flop": Street.FLOP,
        "turn": Street.TURN,
        "river": Street.RIVER
    }
    street = street_map.get(request_state.street.lower(), Street.PREFLOP)

    # Convert opponents
    opponents = [
        EngineOpponent(
            name=opp.name,
            position=opp.position,
            stack=opp.stack,
            stats=opp.stats
        )
        for opp in request_state.opponents
    ]

    # Convert action history
    action_history = [
        {
            "player": item.player,
            "action": item.action,
            "amount": item.amount
        }
        for item in request_state.action_history
    ]

    return EngineGameState(
        hero_cards=request_state.hero_cards,
        hero_position=request_state.hero_position,
        hero_stack=request_state.hero_stack,
        community_cards=request_state.community_cards,
        pot_size=request_state.pot_size,
        bet_to_call=request_state.bet_to_call,
        street=street,
        opponents=opponents,
        action_history=action_history
    )


@router.post("/recommend", response_model=RecommendationResponse)
async def get_recommendation(request: RecommendationRequest) -> RecommendationResponse:
    """
    Get SmartHelper recommendation for current game state

    Returns real-time action recommendation with:
    - Optimal action (FOLD/CHECK/CALL/BET/RAISE/ALL_IN)
    - Bet/raise amount (if applicable)
    - GTO action frequencies
    - Strategic reasoning one-liner
    - Confidence score (0-100)
    - Factor-based decision reasoning
    - Net confidence calculation
    """
    try:
        logger.info(f"Recommendation request received for {request.game_state.street} street")

        # Get engine instance
        engine = get_engine()

        # Convert request to engine format
        game_state = convert_game_state(request.game_state)

        # Generate recommendation
        recommendation = engine.recommend(game_state)

        # Convert to response format
        return RecommendationResponse(
            action=recommendation.action.value,
            amount=recommendation.amount,
            gtoFrequencies=GTOFrequenciesResponse(
                fold=recommendation.gto_frequencies.fold,
                check=recommendation.gto_frequencies.check,
                call=recommendation.gto_frequencies.call,
                bet=recommendation.gto_frequencies.bet,
                raise_=recommendation.gto_frequencies.raise_,
                all_in=recommendation.gto_frequencies.all_in
            ),
            strategicReasoning=recommendation.strategic_reasoning,
            confidence=recommendation.confidence,
            factors=[
                DecisionFactorResponse(
                    name=factor.name,
                    score=factor.score,
                    weight=factor.weight,
                    description=factor.description,
                    details=factor.details
                )
                for factor in recommendation.factors
            ],
            netConfidence=recommendation.net_confidence,
            timestamp=recommendation.timestamp
        )

    except Exception as e:
        logger.error(f"Error generating recommendation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendation: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for SmartHelper service
    """
    try:
        engine = get_engine()
        return {
            "status": "healthy",
            "engine": "SmartHelperEngine",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SmartHelper service unavailable"
        )


@router.get("/factors", response_model=List[DecisionFactorResponse])
async def get_decision_factors(
    street: str = "preflop",
    position: Optional[str] = None
) -> List[DecisionFactorResponse]:
    """
    Get available decision factors with their weights

    Returns list of all factors that SmartHelper uses to make decisions,
    including their base weights and descriptions.

    Args:
        street: Current street (preflop/flop/turn/river)
        position: Hero's position (optional, for position-specific factors)

    Returns:
        List of decision factors with weights and descriptions
    """
    try:
        engine = get_engine()

        # Get factors from engine
        factors = engine.get_available_factors(street=street, position=position)

        return [
            DecisionFactorResponse(
                name=factor["name"],
                score=factor.get("default_score", 0.0),
                weight=factor["weight"],
                description=factor["description"],
                details=factor.get("details")
            )
            for factor in factors
        ]

    except Exception as e:
        logger.error(f"Error getting decision factors: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get decision factors: {str(e)}"
        )


class EquityRequest(BaseModel):
    """Request model for equity calculation"""
    hero_cards: List[str]
    villain_range: Optional[List[str]] = None
    villain_hand: Optional[List[str]] = None
    community_cards: List[str] = Field(default_factory=list)
    num_simulations: int = Field(default=1000, ge=100, le=10000)


class EquityResponse(BaseModel):
    """Response model for equity calculation"""
    hero_equity: float
    villain_equity: float
    tie_equity: float
    simulations_run: int
    calculation_time_ms: float


@router.post("/equity", response_model=EquityResponse)
async def calculate_equity(request: EquityRequest) -> EquityResponse:
    """
    Calculate real-time equity for hero hand vs villain range/hand

    Performs Monte Carlo simulation to calculate:
    - Hero's win probability
    - Villain's win probability
    - Tie probability

    Args:
        request: Contains hero cards, villain range/hand, community cards, and simulation count

    Returns:
        Equity percentages and simulation metadata
    """
    try:
        import time
        from pokertool.equity_calculator import EquityCalculator

        logger.info(f"Equity calculation request: {len(request.hero_cards)} hero cards vs "
                   f"{'range' if request.villain_range else 'hand'}")

        start_time = time.time()

        # Initialize equity calculator
        calc = EquityCalculator()

        # Validate hero cards
        if not request.hero_cards or len(request.hero_cards) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hero must have exactly 2 cards"
            )

        # Convert hero cards to notation (e.g., ["As", "Ks"] -> "AKs")
        hero_hand = "".join(card[0] for card in request.hero_cards)
        if request.hero_cards[0][1] == request.hero_cards[1][1]:  # Same suit
            hero_hand += "s"
        elif request.hero_cards[0][0] != request.hero_cards[1][0]:  # Different ranks
            hero_hand += "o"

        # Calculate equity
        if request.villain_range:
            # Hand vs range
            hero_equity = calc.calculate_hand_vs_range(
                hero_hand=hero_hand,
                villain_range=request.villain_range
            )
            villain_equity = 100 - hero_equity
            tie_equity = 0.0

        elif request.villain_hand and len(request.villain_hand) == 2:
            # Hand vs hand
            villain_hand = "".join(card[0] for card in request.villain_hand)
            if request.villain_hand[0][1] == request.villain_hand[1][1]:
                villain_hand += "s"
            elif request.villain_hand[0][0] != request.villain_hand[1][0]:
                villain_hand += "o"

            hero_equity = calc.calculate_hand_vs_hand(
                hero_hand=hero_hand,
                villain_hand=villain_hand
            )
            villain_equity = 100 - hero_equity
            tie_equity = 0.0

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either villain_range or villain_hand"
            )

        calculation_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        logger.info(f"Equity calculated: Hero {hero_equity:.1f}% in {calculation_time:.1f}ms")

        return EquityResponse(
            hero_equity=hero_equity,
            villain_equity=villain_equity,
            tie_equity=tie_equity,
            simulations_run=request.num_simulations,
            calculation_time_ms=calculation_time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating equity: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate equity: {str(e)}"
        )


@router.get("/demo")
async def get_demo_recommendation() -> RecommendationResponse:
    """
    Get a demo recommendation with example data

    Useful for testing the SmartHelper UI without real game data
    """
    try:
        # Create demo game state
        demo_state = EngineGameState(
            hero_cards=["As", "Ks"],
            hero_position="BTN",
            hero_stack=1000.0,
            community_cards=["Qh", "Jd", "9c"],
            pot_size=150.0,
            bet_to_call=50.0,
            street=Street.FLOP,
            opponents=[
                EngineOpponent(
                    name="Villain",
                    position="BB",
                    stack=800.0,
                    stats={
                        "vpip": 35.0,
                        "pfr": 18.0,
                        "threebet": 8.0,
                        "foldToCbet": 65.0,
                        "foldToThreebet": 55.0,
                        "aggression": 2.5
                    }
                )
            ],
            action_history=[
                {"player": "BB", "action": "BET", "amount": 50.0}
            ]
        )

        # Generate recommendation
        engine = get_engine()
        recommendation = engine.recommend(demo_state)

        # Convert to response
        return RecommendationResponse(
            action=recommendation.action.value,
            amount=recommendation.amount,
            gtoFrequencies=GTOFrequenciesResponse(
                fold=recommendation.gto_frequencies.fold,
                check=recommendation.gto_frequencies.check,
                call=recommendation.gto_frequencies.call,
                bet=recommendation.gto_frequencies.bet,
                raise_=recommendation.gto_frequencies.raise_,
                all_in=recommendation.gto_frequencies.all_in
            ),
            strategicReasoning=recommendation.strategic_reasoning,
            confidence=recommendation.confidence,
            factors=[
                DecisionFactorResponse(
                    name=factor.name,
                    score=factor.score,
                    weight=factor.weight,
                    description=factor.description,
                    details=factor.details
                )
                for factor in recommendation.factors
            ],
            netConfidence=recommendation.net_confidence,
            timestamp=recommendation.timestamp
        )

    except Exception as e:
        logger.error(f"Error generating demo recommendation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate demo recommendation: {str(e)}"
        )
