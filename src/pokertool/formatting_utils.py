#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Formatting Utilities for PokerTool
===================================

Provides consistent formatting for probabilities, percentages, currencies, and other values
throughout the application for improved accuracy and presentation.

Version: 64.0.0
"""

from typing import Optional, Tuple
import math


def format_percentage(
    value: float,
    decimal_places: int = 1,
    include_symbol: bool = True,
    confidence_interval: Optional[Tuple[float, float]] = None
) -> str:
    """
    Format a probability (0.0-1.0) as a percentage string.

    Args:
        value: Probability value (0.0-1.0)
        decimal_places: Number of decimal places (default 1)
        include_symbol: Whether to include % symbol (default True)
        confidence_interval: Optional (lower, upper) bounds for CI display

    Returns:
        Formatted percentage string

    Examples:
        >>> format_percentage(0.453)
        '45.3%'
        >>> format_percentage(0.453, decimal_places=2)
        '45.30%'
        >>> format_percentage(0.453, confidence_interval=(0.42, 0.48))
        '45.3% [42.0%-48.0%]'
    """
    # Clamp to valid range
    value = max(0.0, min(1.0, value))

    # Convert to percentage
    percentage = value * 100

    # Format with specified decimal places
    format_str = f"{{:.{decimal_places}f}}"
    formatted = format_str.format(percentage)

    # Add symbol if requested
    if include_symbol:
        formatted += "%"

    # Add confidence interval if provided
    if confidence_interval:
        lower, upper = confidence_interval
        lower = max(0.0, min(1.0, lower)) * 100
        upper = max(0.0, min(1.0, upper)) * 100
        lower_str = format_str.format(lower)
        upper_str = format_str.format(upper)
        formatted += f" [{lower_str}%-{upper_str}%]"

    return formatted


def format_currency(
    value: float,
    symbol: str = "$",
    decimal_places: int = 2,
    include_sign: bool = True
) -> str:
    """
    Format currency value.

    Args:
        value: Currency amount
        symbol: Currency symbol (default $)
        decimal_places: Number of decimal places
        include_sign: Whether to include + for positive values

    Returns:
        Formatted currency string

    Examples:
        >>> format_currency(123.45)
        '$123.45'
        >>> format_currency(-50.0)
        '-$50.00'
        >>> format_currency(75.5, include_sign=True)
        '+$75.50'
    """
    format_str = f"{{:.{decimal_places}f}}"
    formatted_value = format_str.format(abs(value))

    # Handle sign
    if value < 0:
        return f"-{symbol}{formatted_value}"
    elif value > 0 and include_sign:
        return f"+{symbol}{formatted_value}"
    else:
        return f"{symbol}{formatted_value}"


def format_big_blinds(
    value: float,
    decimal_places: int = 1,
    suffix: str = "BB"
) -> str:
    """
    Format value in big blinds.

    Args:
        value: Value in big blinds
        decimal_places: Number of decimal places
        suffix: Suffix to append (default BB)

    Returns:
        Formatted big blind string

    Examples:
        >>> format_big_blinds(15.5)
        '15.5BB'
        >>> format_big_blinds(-3.2)
        '-3.2BB'
    """
    format_str = f"{{:+.{decimal_places}f}}" if value != 0 else f"{{:.{decimal_places}f}}"
    formatted = format_str.format(value)
    return f"{formatted}{suffix}"


def format_odds(pot_odds: float, format_type: str = "percentage") -> str:
    """
    Format pot odds.

    Args:
        pot_odds: Pot odds as decimal (e.g., 0.333 for 3:1)
        format_type: "percentage", "ratio", or "both"

    Returns:
        Formatted odds string

    Examples:
        >>> format_odds(0.333, "percentage")
        '33.3%'
        >>> format_odds(0.333, "ratio")
        '2:1'
        >>> format_odds(0.333, "both")
        '33.3% (2:1)'
    """
    # Percentage format
    percentage = format_percentage(pot_odds, decimal_places=1)

    if format_type == "percentage":
        return percentage

    # Ratio format
    if pot_odds > 0 and pot_odds < 1:
        ratio = (1.0 / pot_odds) - 1
        ratio_str = f"{ratio:.1f}:1"
    else:
        ratio_str = "N/A"

    if format_type == "ratio":
        return ratio_str

    # Both
    return f"{percentage} ({ratio_str})"


def format_confidence_band(
    win_prob: float,
    lower: float,
    upper: float,
    style: str = "compact"
) -> str:
    """
    Format confidence interval for win probability.

    Args:
        win_prob: Win probability (0.0-1.0)
        lower: Lower bound of CI
        upper: Upper bound of CI
        style: "compact", "verbose", or "symbol"

    Returns:
        Formatted confidence band string

    Examples:
        >>> format_confidence_band(0.55, 0.52, 0.58, "compact")
        '55.0% ±3.0%'
        >>> format_confidence_band(0.55, 0.52, 0.58, "verbose")
        '55.0% (95% CI: 52.0%-58.0%)'
        >>> format_confidence_band(0.55, 0.52, 0.58, "symbol")
        '55.0% [52.0%-58.0%]'
    """
    center = format_percentage(win_prob, decimal_places=1)
    margin = (upper - lower) / 2 * 100

    if style == "compact":
        return f"{center} ±{margin:.1f}%"
    elif style == "verbose":
        lower_str = format_percentage(lower, decimal_places=1)
        upper_str = format_percentage(upper, decimal_places=1)
        return f"{center} (95% CI: {lower_str}-{upper_str})"
    else:  # symbol
        lower_str = format_percentage(lower, decimal_places=1)
        upper_str = format_percentage(upper, decimal_places=1)
        return f"{center} [{lower_str}-{upper_str}]"


def format_stack_size(stack: float, big_blind: float = 1.0) -> str:
    """
    Format stack size with appropriate scaling.

    Args:
        stack: Stack size in chips
        big_blind: Big blind size for BB conversion

    Returns:
        Formatted stack string

    Examples:
        >>> format_stack_size(1500, 10)
        '150BB ($1,500)'
        >>> format_stack_size(50000)
        '50,000BB'
    """
    bb_stack = stack / big_blind if big_blind > 0 else 0
    stack_formatted = f"{stack:,.0f}"

    if bb_stack >= 10:
        return f"{bb_stack:.0f}BB (${stack_formatted})"
    else:
        return f"${stack_formatted}"


def get_color_for_probability(
    probability: float,
    color_scheme: str = "traffic_light"
) -> str:
    """
    Get color code for probability value.

    Args:
        probability: Probability value (0.0-1.0)
        color_scheme: "traffic_light", "gradient", or "binary"

    Returns:
        Hex color code

    Examples:
        >>> get_color_for_probability(0.7, "traffic_light")
        '#00C853'  # Green
        >>> get_color_for_probability(0.3, "traffic_light")
        '#DD2C00'  # Red
    """
    probability = max(0.0, min(1.0, probability))

    if color_scheme == "traffic_light":
        if probability >= 0.6:
            return "#00C853"  # Green
        elif probability >= 0.4:
            return "#FFD600"  # Yellow
        else:
            return "#DD2C00"  # Red

    elif color_scheme == "gradient":
        # Smooth gradient from red to green
        if probability < 0.5:
            # Red to yellow
            r = 255
            g = int(255 * (probability * 2))
            b = 0
        else:
            # Yellow to green
            r = int(255 * (2 * (1 - probability)))
            g = 255
            b = 0
        return f"#{r:02x}{g:02x}{b:02x}"

    else:  # binary
        return "#00C853" if probability >= 0.5 else "#DD2C00"


def get_color_for_confidence(confidence: float) -> str:
    """
    Get color code for confidence level.

    Args:
        confidence: Confidence value (0.0-1.0)

    Returns:
        Hex color code
    """
    confidence = max(0.0, min(1.0, confidence))

    if confidence >= 0.8:
        return "#00C853"  # Very high - green
    elif confidence >= 0.6:
        return "#64DD17"  # High - light green
    elif confidence >= 0.4:
        return "#FFD600"  # Medium - yellow
    elif confidence >= 0.2:
        return "#FF6D00"  # Low - orange
    else:
        return "#DD2C00"  # Very low - red


def format_action_display(
    action: str,
    amount: Optional[float] = None,
    pot_size: Optional[float] = None
) -> str:
    """
    Format action display with optional bet sizing context.

    Args:
        action: Action string (fold, call, raise, etc.)
        amount: Bet/raise amount
        pot_size: Current pot size

    Returns:
        Formatted action string

    Examples:
        >>> format_action_display("RAISE", 50, 100)
        'RAISE $50 (50% pot)'
        >>> format_action_display("CALL", 25)
        'CALL $25'
    """
    action_upper = action.upper()

    if amount is None:
        return action_upper

    amount_str = format_currency(amount, include_sign=False)

    if pot_size and pot_size > 0 and action_upper in ("RAISE", "BET"):
        pot_percentage = (amount / pot_size) * 100
        return f"{action_upper} {amount_str} ({pot_percentage:.0f}% pot)"
    else:
        return f"{action_upper} {amount_str}"


__all__ = [
    "format_percentage",
    "format_currency",
    "format_big_blinds",
    "format_odds",
    "format_confidence_band",
    "format_stack_size",
    "get_color_for_probability",
    "get_color_for_confidence",
    "format_action_display"
]
