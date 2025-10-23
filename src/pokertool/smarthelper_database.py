"""
SmartHelper Database Schemas

Database tables for storing SmartHelper recommendations, opponent profiles,
and user preferences.

Author: PokerTool Team
Created: 2025-10-22
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, JSON, Boolean,
    Index, ForeignKey, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

logger = logging.getLogger(__name__)

Base = declarative_base()


class RecommendationHistory(Base):
    """
    Store all SmartHelper recommendations for analysis and feedback

    Schema allows tracking recommendation accuracy, user feedback,
    and long-term performance analysis.
    """
    __tablename__ = 'recommendation_history'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Timestamps
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # User/Table identification
    user_id = Column(String(50), nullable=False, index=True)
    table_id = Column(String(50), nullable=True, index=True)
    session_id = Column(String(100), nullable=True)

    # Game state (JSON)
    game_state = Column(JSON, nullable=False)
    # {
    #   "heroCards": ["As", "Ks"],
    #   "heroPosition": "BTN",
    #   "heroStack": 1000,
    #   "communityCards": ["Qh", "Jd", "9c"],
    #   "potSize": 150,
    #   "betToCall": 50,
    #   "street": "flop",
    #   "opponents": [...],
    #   "actionHistory": [...]
    # }

    # Recommendation
    action = Column(String(20), nullable=False)  # FOLD/CHECK/CALL/BET/RAISE/ALL_IN
    amount = Column(Float, nullable=True)
    confidence = Column(Float, nullable=False)
    net_confidence = Column(Float, nullable=False)
    strategic_reasoning = Column(Text, nullable=True)

    # GTO frequencies (JSON)
    gto_frequencies = Column(JSON, nullable=True)
    # {
    #   "fold": 30.0,
    #   "check": 20.0,
    #   "call": 25.0,
    #   "bet": 15.0,
    #   "raise": 8.0,
    #   "all_in": 2.0
    # }

    # Decision factors (JSON)
    factors = Column(JSON, nullable=True)
    # [
    #   {
    #     "name": "pot_odds",
    #     "score": 75.0,
    #     "weight": 0.25,
    #     "description": "..."
    #   }
    # ]

    # User feedback
    user_action = Column(String(20), nullable=True)  # What user actually did
    user_amount = Column(Float, nullable=True)
    followed_recommendation = Column(Boolean, nullable=True)
    feedback_rating = Column(Integer, nullable=True)  # 1-5 stars
    feedback_text = Column(Text, nullable=True)

    # Outcome tracking
    outcome = Column(String(20), nullable=True)  # WON/LOST/PUSH
    profit_loss = Column(Float, nullable=True)

    # Metadata
    calculation_time_ms = Column(Float, nullable=True)
    cache_hit = Column(Boolean, default=False)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_table_timestamp', 'table_id', 'timestamp'),
        Index('idx_action_confidence', 'action', 'confidence'),
    )


class OpponentProfile(Base):
    """
    Store opponent statistics and tendencies

    Aggregates opponent behavior over time for exploitative strategy.
    """
    __tablename__ = 'opponent_profiles'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Opponent identification
    user_id = Column(String(50), nullable=False, index=True)  # Observer user
    opponent_name = Column(String(100), nullable=False, index=True)
    opponent_id = Column(String(50), nullable=True, index=True)  # If available
    platform = Column(String(50), nullable=True)  # betfair/pokerstars/etc

    # Timestamps
    first_seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Sample size
    hands_played = Column(Integer, default=0)
    hands_to_showdown = Column(Integer, default=0)

    # Preflop statistics
    vpip = Column(Float, default=0.0)  # Voluntarily Put $ In Pot %
    pfr = Column(Float, default=0.0)   # Preflop Raise %
    threebet = Column(Float, default=0.0)  # 3-Bet %
    fourbet = Column(Float, default=0.0)   # 4-Bet %
    cold_call = Column(Float, default=0.0)  # Cold Call %

    # Postflop statistics
    cbet = Column(Float, default=0.0)  # C-Bet %
    fold_to_cbet = Column(Float, default=0.0)  # Fold to C-Bet %
    fold_to_threebet = Column(Float, default=0.0)  # Fold to 3-Bet %
    fold_to_fourbet = Column(Float, default=0.0)  # Fold to 4-Bet %

    # Aggression metrics
    aggression = Column(Float, default=0.0)  # Aggression Factor
    wtsd = Column(Float, default=0.0)  # Went To Showdown %
    wsd = Column(Float, default=0.0)   # Won at Showdown %

    # Detailed statistics (JSON)
    position_stats = Column(JSON, nullable=True)
    # {
    #   "BTN": {"vpip": 45, "pfr": 35, ...},
    #   "CO": {...},
    #   ...
    # }

    street_stats = Column(JSON, nullable=True)
    # {
    #   "flop": {"cbet": 70, "fold_to_cbet": 40, ...},
    #   "turn": {...},
    #   "river": {...}
    # }

    # Player type classification
    player_type = Column(String(20), nullable=True)  # LAG/TAG/LP/TP/BALANCED
    skill_level = Column(String(20), nullable=True)  # BEGINNER/INTERMEDIATE/ADVANCED/EXPERT

    # Notable patterns (JSON array)
    patterns = Column(JSON, nullable=True)
    # [
    #   "Folds to c-bet >70%",
    #   "3-bets light from BTN",
    #   "Rarely bluffs river"
    # ]

    # Notes
    notes = Column(Text, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_user_opponent', 'user_id', 'opponent_name'),
        Index('idx_last_seen', 'last_seen'),
        Index('idx_hands_played', 'hands_played'),
    )


class SmartHelperPreferences(Base):
    """
    Store user preferences for SmartHelper

    Persists settings across sessions.
    """
    __tablename__ = 'smarthelper_preferences'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # User identification
    user_id = Column(String(50), nullable=False, unique=True, index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Strategy preferences
    strategy_mode = Column(String(20), default='balanced')  # gto/balanced/exploitative
    exploitative_weight = Column(Float, default=50.0)  # 0-100

    # Display preferences
    show_equity_chart = Column(Boolean, default=True)
    show_range_analyzer = Column(Boolean, default=True)
    show_opponent_profiles = Column(Boolean, default=True)
    show_decision_factors = Column(Boolean, default=True)
    show_pot_odds = Column(Boolean, default=True)
    show_implied_odds = Column(Boolean, default=True)

    # Confidence thresholds
    min_confidence_to_show = Column(Float, default=30.0)
    min_confidence_to_highlight = Column(Float, default=70.0)

    # Notification preferences
    enable_sound_alerts = Column(Boolean, default=False)
    enable_visual_alerts = Column(Boolean, default=True)
    alert_on_high_confidence = Column(Boolean, default=True)
    alert_on_exploit_opportunity = Column(Boolean, default=True)

    # Performance settings
    auto_collapse_panels = Column(Boolean, default=False)
    enable_animations = Column(Boolean, default=True)
    refresh_rate = Column(Integer, default=1000)  # milliseconds

    # Advanced settings (JSON)
    factor_weights = Column(JSON, nullable=True)
    # {
    #   "pot_odds": 0.25,
    #   "hand_strength": 0.30,
    #   ...
    # }

    panel_layout = Column(JSON, nullable=True)
    # ["equity", "recommendation", "factors", "opponents"]

    custom_settings = Column(JSON, nullable=True)
    # Additional custom preferences


def create_tables(engine):
    """
    Create all SmartHelper tables

    Args:
        engine: SQLAlchemy engine
    """
    try:
        Base.metadata.create_all(engine)
        logger.info("SmartHelper database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating SmartHelper tables: {e}")
        raise


def drop_tables(engine):
    """
    Drop all SmartHelper tables (use with caution)

    Args:
        engine: SQLAlchemy engine
    """
    try:
        Base.metadata.drop_all(engine)
        logger.info("SmartHelper database tables dropped")
    except Exception as e:
        logger.error(f"Error dropping SmartHelper tables: {e}")
        raise


# Data retention functions

def cleanup_old_recommendations(session, days_to_keep: int = 90):
    """
    Delete recommendations older than specified days

    Args:
        session: SQLAlchemy session
        days_to_keep: Number of days to retain
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted = session.query(RecommendationHistory).filter(
            RecommendationHistory.timestamp < cutoff_date
        ).delete()
        session.commit()
        logger.info(f"Deleted {deleted} old recommendations (older than {days_to_keep} days)")
        return deleted
    except Exception as e:
        session.rollback()
        logger.error(f"Error cleaning up old recommendations: {e}")
        raise


def cleanup_inactive_opponents(session, days_inactive: int = 180):
    """
    Delete opponent profiles not seen in specified days

    Args:
        session: SQLAlchemy session
        days_inactive: Days of inactivity threshold
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)
        deleted = session.query(OpponentProfile).filter(
            OpponentProfile.last_seen < cutoff_date
        ).delete()
        session.commit()
        logger.info(f"Deleted {deleted} inactive opponent profiles (inactive for >{days_inactive} days)")
        return deleted
    except Exception as e:
        session.rollback()
        logger.error(f"Error cleaning up inactive opponents: {e}")
        raise
