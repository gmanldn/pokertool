#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Detailed Advice Explainer
==========================

Generates comprehensive, multi-line explanations for poker decisions.
Takes LiveAdviceData and creates readable, detailed reasoning that explains:
- What action to take and why
- Key metrics supporting the decision
- Alternative actions and why they're inferior
- Strategic context

Version: 65.0.0
Author: PokerTool Development Team
"""

from __future__ import annotations

from typing import Optional
from .compact_live_advice_window import LiveAdviceData, ActionType


class DetailedAdviceExplainer:
    """Generate detailed, multi-line explanations for poker decisions."""

    @staticmethod
    def generate_detailed_explanation(advice_data: LiveAdviceData) -> str:
        """
        Generate detailed explanation from advice data.

        Args:
            advice_data: LiveAdviceData with recommendation and metrics

        Returns:
            Multi-line string explaining the decision in detail
        """
        if not advice_data or not advice_data.has_data:
            return "⏳ Waiting for game data...\n\nAutopilot will analyze the table state and provide recommendations."

        lines = []

        # 1. PRIMARY RECOMMENDATION
        action_text = DetailedAdviceExplainer._format_action_recommendation(advice_data)
        lines.append(f"💡 {action_text}")
        lines.append("")

        # 2. WHY THIS ACTION (based on key metrics)
        why_text = DetailedAdviceExplainer._generate_why_section(advice_data)
        lines.append(f"📊 WHY: {why_text}")
        lines.append("")

        # 3. KEY METRICS
        metrics_text = DetailedAdviceExplainer._format_key_metrics(advice_data)
        if metrics_text:
            lines.append(f"📈 METRICS:")
            lines.append(metrics_text)
            lines.append("")

        # 4. ALTERNATIVE ACTIONS (if available)
        alternatives_text = DetailedAdviceExplainer._format_alternatives(advice_data)
        if alternatives_text:
            lines.append(f"🔄 ALTERNATIVES:")
            lines.append(alternatives_text)

        return "\n".join(lines)

    @staticmethod
    def _format_action_recommendation(advice_data: LiveAdviceData) -> str:
        """Format the primary action recommendation."""
        action = advice_data.action.value

        if advice_data.action_amount:
            return f"{action} ${advice_data.action_amount:.0f}"
        else:
            return action

    @staticmethod
    def _generate_why_section(advice_data: LiveAdviceData) -> str:
        """
        Generate the 'WHY' section explaining the core reasoning.

        This is the most important part - it explains the decision logic.
        """
        action = advice_data.action
        win_prob = advice_data.win_probability
        confidence = advice_data.confidence
        pot_odds = advice_data.pot_odds
        ev_call = advice_data.ev_call
        ev_raise = advice_data.ev_raise

        # Action-specific explanations
        if action == ActionType.FOLD:
            return DetailedAdviceExplainer._explain_fold(
                win_prob, pot_odds, ev_call, advice_data
            )
        elif action == ActionType.CALL:
            return DetailedAdviceExplainer._explain_call(
                win_prob, pot_odds, ev_call, advice_data
            )
        elif action == ActionType.RAISE:
            return DetailedAdviceExplainer._explain_raise(
                win_prob, ev_raise, confidence, advice_data
            )
        elif action == ActionType.CHECK:
            return "No cost to see another card. Checking allows you to realize equity without investing more chips."
        elif action == ActionType.ALL_IN:
            return DetailedAdviceExplainer._explain_allin(
                win_prob, confidence, advice_data
            )
        else:
            return "Analyzing game state..."

    @staticmethod
    def _explain_fold(
        win_prob: float,
        pot_odds: Optional[float],
        ev_call: Optional[float],
        advice_data: LiveAdviceData
    ) -> str:
        """Explain why folding is recommended."""
        parts = []

        # Main reason
        if pot_odds and win_prob < pot_odds:
            equity_needed = pot_odds * 100
            equity_have = win_prob * 100
            parts.append(
                f"Your hand has {equity_have:.1f}% equity but needs {equity_needed:.1f}% to call profitably. "
            )
        elif win_prob < 0.3:
            parts.append(f"Your hand is very weak ({win_prob*100:.1f}% to win). ")
        else:
            parts.append(f"The math doesn't support continuing with {win_prob*100:.1f}% equity. ")

        # EV context
        if ev_call and ev_call < -5:
            parts.append(f"Calling would lose ${abs(ev_call):.0f} on average (negative EV). ")

        # Strategic context
        if advice_data.position and advice_data.position in ['SB', 'BB', 'EP']:
            parts.append("Your position is weak, making it harder to realize equity.")

        parts.append("Folding preserves your stack for better spots.")

        return "".join(parts)

    @staticmethod
    def _explain_call(
        win_prob: float,
        pot_odds: Optional[float],
        ev_call: Optional[float],
        advice_data: LiveAdviceData
    ) -> str:
        """Explain why calling is recommended."""
        parts = []

        # Main reason
        if pot_odds and win_prob >= pot_odds:
            parts.append(
                f"You have {win_prob*100:.1f}% equity vs {pot_odds*100:.1f}% pot odds required - "
                "mathematically correct to call. "
            )
        elif ev_call and ev_call > 0:
            parts.append(f"Calling is +EV (expected to win ${ev_call:.0f} on average). ")
        elif win_prob > 0.45:
            parts.append(f"Your {win_prob*100:.1f}% equity justifies calling. ")
        else:
            parts.append("You're getting the right price to draw. ")

        # Drawing context
        if advice_data.outs_count and advice_data.outs_percentage:
            outs = advice_data.outs_count
            pct = advice_data.outs_percentage
            parts.append(f"You have ~{outs} outs ({pct:.1f}% to improve). ")

        # Strategic context
        if advice_data.stack_pot_ratio and advice_data.stack_pot_ratio < 3:
            parts.append("Low SPR means you're committed to this pot.")

        return "".join(parts)

    @staticmethod
    def _explain_raise(
        win_prob: float,
        ev_raise: Optional[float],
        confidence: float,
        advice_data: LiveAdviceData
    ) -> str:
        """Explain why raising is recommended."""
        parts = []

        # Main reason based on hand strength
        if win_prob > 0.7:
            parts.append(
                f"Strong hand ({win_prob*100:.1f}% to win) - raising for value. "
                "You want to build the pot and get paid by worse hands. "
            )
        elif win_prob > 0.55:
            parts.append(
                f"You're ahead ({win_prob*100:.1f}% equity) - raising builds the pot "
                "while you have the advantage. "
            )
        elif win_prob > 0.35:
            parts.append(
                f"Semi-bluff opportunity: You have {win_prob*100:.1f}% equity plus fold equity. "
                "Even if called, you have outs to improve. "
            )
        else:
            parts.append(
                f"Bluff with fold equity: Even with {win_prob*100:.1f}% equity, "
                "opponents may fold better hands. "
            )

        # EV context
        if ev_raise and ev_raise > 10:
            parts.append(f"This raise is highly +EV (${ev_raise:.0f} expected profit). ")
        elif ev_raise and ev_raise > 0:
            parts.append(f"Positive EV play (+${ev_raise:.0f}). ")

        # Strategic context
        if advice_data.position and advice_data.position in ['BTN', 'CO']:
            parts.append("Good position increases fold equity and control.")

        return "".join(parts)

    @staticmethod
    def _explain_allin(
        win_prob: float,
        confidence: float,
        advice_data: LiveAdviceData
    ) -> str:
        """Explain why all-in is recommended."""
        if win_prob > 0.75 and confidence > 0.7:
            return (
                f"Premium hand ({win_prob*100:.1f}% to win) - going all-in maximizes value. "
                "You want to get your entire stack in with this advantage."
            )
        elif win_prob > 0.55:
            return (
                f"Commitment point reached: With {win_prob*100:.1f}% equity and "
                "pot-to-stack ratio, it's correct to commit your entire stack."
            )
        else:
            return (
                f"Fold equity all-in: Even with {win_prob*100:.1f}% equity, "
                "opponents may fold, and if called, you still have a shot to win."
            )

    @staticmethod
    def _format_key_metrics(advice_data: LiveAdviceData) -> str:
        """Format key metrics supporting the decision."""
        metrics = []

        # Win Probability
        win_prob = advice_data.win_probability * 100
        win_lower = advice_data.win_prob_lower * 100
        win_upper = advice_data.win_prob_upper * 100
        metrics.append(f"  • Win Probability: {win_prob:.1f}% (range: {win_lower:.1f}%-{win_upper:.1f}%)")

        # Confidence
        conf = advice_data.confidence * 100
        metrics.append(f"  • Confidence: {conf:.1f}%")

        # Pot Odds (if available)
        if advice_data.pot_odds is not None:
            pot_odds = advice_data.pot_odds * 100
            metrics.append(f"  • Pot Odds: {pot_odds:.1f}% equity needed")

        # EV for available actions
        ev_strs = []
        if advice_data.ev_call is not None:
            ev_strs.append(f"Call ${advice_data.ev_call:+.1f}")
        if advice_data.ev_raise is not None:
            ev_strs.append(f"Raise ${advice_data.ev_raise:+.1f}")
        if ev_strs:
            metrics.append(f"  • Expected Value: {', '.join(ev_strs)}")

        # Stack-to-Pot Ratio
        if advice_data.stack_pot_ratio is not None:
            spr = advice_data.stack_pot_ratio
            metrics.append(f"  • Stack-to-Pot Ratio: {spr:.1f}")

        # Hand Percentile
        if advice_data.hand_percentile is not None:
            percentile = advice_data.hand_percentile
            metrics.append(f"  • Hand Strength: {percentile:.0f}th percentile")

        # Outs (for drawing hands)
        if advice_data.outs_count is not None:
            outs = advice_data.outs_count
            pct = advice_data.outs_percentage or 0
            metrics.append(f"  • Outs: ~{outs} cards ({pct:.1f}% to improve)")

        # Position & Street
        context = []
        if advice_data.position:
            context.append(f"Position: {advice_data.position}")
        if advice_data.street:
            context.append(f"Street: {advice_data.street.capitalize()}")
        if context:
            metrics.append(f"  • {', '.join(context)}")

        return "\n".join(metrics)

    @staticmethod
    def _format_alternatives(advice_data: LiveAdviceData) -> str:
        """Format alternative actions and explain why they're inferior."""
        if not advice_data.alternative_actions:
            return ""

        lines = []
        for alt in advice_data.alternative_actions[:2]:  # Show max 2 alternatives
            action_name = alt.get('action', 'Unknown')
            ev_value = alt.get('ev')

            if ev_value is not None:
                ev_str = f"${ev_value:+.1f} EV"
                if ev_value < 0:
                    reason = "negative EV (loses money on average)"
                elif ev_value < advice_data.ev_call if advice_data.ev_call else 0:
                    reason = "lower EV than recommended action"
                else:
                    reason = "suboptimal compared to primary action"

                lines.append(f"  • {action_name}: {ev_str} - {reason}")
            else:
                lines.append(f"  • {action_name}: Less optimal than recommended action")

        return "\n".join(lines)


# Singleton instance for easy access
_explainer_instance: Optional[DetailedAdviceExplainer] = None


def get_detailed_explainer() -> DetailedAdviceExplainer:
    """Get singleton instance of DetailedAdviceExplainer."""
    global _explainer_instance
    if _explainer_instance is None:
        _explainer_instance = DetailedAdviceExplainer()
    return _explainer_instance
