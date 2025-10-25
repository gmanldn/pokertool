#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Currency Converter
=================

Converts poker amounts between different currencies for international games.
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class Currency(str, Enum):
    """Supported currencies"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    JPY = "JPY"
    CNY = "CNY"
    INR = "INR"
    BRL = "BRL"
    MXN = "MXN"


@dataclass
class ConversionRecord:
    """Record of a currency conversion"""
    timestamp: datetime
    from_currency: Currency
    to_currency: Currency
    from_amount: float
    to_amount: float
    exchange_rate: float
    conversion_id: int


class CurrencyConverter:
    """
    Converts poker amounts between currencies.
    Uses fixed exchange rates (for production, integrate with live API).
    """

    def __init__(self, base_currency: Currency = Currency.USD):
        """
        Initialize currency converter.

        Args:
            base_currency: Base currency for conversions
        """
        self.base_currency = base_currency
        self.conversion_history: list[ConversionRecord] = []
        self.conversion_count = 0

        # Fixed exchange rates (USD as base)
        # In production, fetch from API like exchangerate-api.com
        self.exchange_rates = {
            Currency.USD: 1.0,
            Currency.EUR: 0.92,
            Currency.GBP: 0.79,
            Currency.CAD: 1.36,
            Currency.AUD: 1.52,
            Currency.JPY: 149.50,
            Currency.CNY: 7.24,
            Currency.INR: 83.12,
            Currency.BRL: 4.97,
            Currency.MXN: 17.05
        }

    def convert(
        self,
        amount: float,
        from_currency: Currency,
        to_currency: Currency
    ) -> float:
        """
        Convert amount from one currency to another.

        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency

        Returns:
            Converted amount
        """
        if from_currency == to_currency:
            return amount

        # Convert to base currency (USD)
        if from_currency != self.base_currency:
            usd_amount = amount / self.exchange_rates[from_currency]
        else:
            usd_amount = amount

        # Convert from base to target currency
        if to_currency != self.base_currency:
            converted_amount = usd_amount * self.exchange_rates[to_currency]
        else:
            converted_amount = usd_amount

        # Record conversion
        self.conversion_count += 1
        exchange_rate = self.exchange_rates[to_currency] / self.exchange_rates[from_currency]

        record = ConversionRecord(
            timestamp=datetime.now(),
            from_currency=from_currency,
            to_currency=to_currency,
            from_amount=amount,
            to_amount=converted_amount,
            exchange_rate=exchange_rate,
            conversion_id=self.conversion_count
        )
        self.conversion_history.append(record)

        logger.info(
            f"Converted {amount:.2f} {from_currency.value} → "
            f"{converted_amount:.2f} {to_currency.value} "
            f"(rate: {exchange_rate:.4f})"
        )

        return round(converted_amount, 2)

    def get_exchange_rate(
        self,
        from_currency: Currency,
        to_currency: Currency
    ) -> float:
        """
        Get exchange rate between two currencies.

        Args:
            from_currency: Source currency
            to_currency: Target currency

        Returns:
            Exchange rate
        """
        if from_currency == to_currency:
            return 1.0

        return self.exchange_rates[to_currency] / self.exchange_rates[from_currency]

    def set_exchange_rate(
        self,
        currency: Currency,
        rate_to_base: float
    ) -> None:
        """
        Update exchange rate for a currency.

        Args:
            currency: Currency to update
            rate_to_base: Rate relative to base currency
        """
        self.exchange_rates[currency] = rate_to_base
        logger.info(f"Updated {currency.value} rate to {rate_to_base:.4f}")

    def get_all_rates(self) -> Dict[Currency, float]:
        """Get all exchange rates."""
        return self.exchange_rates.copy()

    def format_amount(
        self,
        amount: float,
        currency: Currency,
        include_symbol: bool = True
    ) -> str:
        """
        Format amount with currency symbol.

        Args:
            amount: Amount to format
            currency: Currency
            include_symbol: Whether to include currency symbol

        Returns:
            Formatted string
        """
        symbols = {
            Currency.USD: "$",
            Currency.EUR: "€",
            Currency.GBP: "£",
            Currency.CAD: "C$",
            Currency.AUD: "A$",
            Currency.JPY: "¥",
            Currency.CNY: "¥",
            Currency.INR: "₹",
            Currency.BRL: "R$",
            Currency.MXN: "Mex$"
        }

        if include_symbol:
            symbol = symbols.get(currency, currency.value)
            return f"{symbol}{amount:,.2f}"
        else:
            return f"{amount:,.2f} {currency.value}"

    def get_conversion_history(
        self,
        limit: Optional[int] = None
    ) -> list[ConversionRecord]:
        """
        Get conversion history.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of conversion records
        """
        if limit:
            return self.conversion_history[-limit:]
        return self.conversion_history.copy()

    def get_statistics(self) -> Dict[str, any]:
        """
        Get conversion statistics.

        Returns:
            Dictionary with statistics
        """
        if not self.conversion_history:
            return {
                "total_conversions": 0,
                "unique_currency_pairs": 0,
                "most_common_from": None,
                "most_common_to": None,
                "total_volume_usd": 0.0
            }

        # Count currency usage
        from_currencies = {}
        to_currencies = {}
        currency_pairs = set()
        total_volume_usd = 0.0

        for record in self.conversion_history:
            # Count from currencies
            from_cur = record.from_currency.value
            from_currencies[from_cur] = from_currencies.get(from_cur, 0) + 1

            # Count to currencies
            to_cur = record.to_currency.value
            to_currencies[to_cur] = to_currencies.get(to_cur, 0) + 1

            # Track unique pairs
            currency_pairs.add((record.from_currency, record.to_currency))

            # Calculate volume in USD
            if record.from_currency == Currency.USD:
                total_volume_usd += record.from_amount
            else:
                total_volume_usd += record.from_amount / self.exchange_rates[record.from_currency]

        most_common_from = max(from_currencies, key=from_currencies.get) if from_currencies else None
        most_common_to = max(to_currencies, key=to_currencies.get) if to_currencies else None

        return {
            "total_conversions": len(self.conversion_history),
            "unique_currency_pairs": len(currency_pairs),
            "most_common_from": most_common_from,
            "most_common_to": most_common_to,
            "total_volume_usd": round(total_volume_usd, 2),
            "base_currency": self.base_currency.value
        }

    def reset(self):
        """Reset converter history."""
        self.conversion_history.clear()
        self.conversion_count = 0


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)

    converter = CurrencyConverter()

    print("Currency Converter - Example\n")

    # Convert USD to EUR
    eur_amount = converter.convert(100.0, Currency.USD, Currency.EUR)
    print(f"$100 USD = {converter.format_amount(eur_amount, Currency.EUR)}")

    # Convert GBP to JPY
    jpy_amount = converter.convert(50.0, Currency.GBP, Currency.JPY)
    print(f"£50 GBP = {converter.format_amount(jpy_amount, Currency.JPY)}")

    # Get exchange rate
    rate = converter.get_exchange_rate(Currency.USD, Currency.CAD)
    print(f"\nUSD/CAD rate: {rate:.4f}")

    stats = converter.get_statistics()
    print(f"\nStatistics:")
    print(f"  Total conversions: {stats['total_conversions']}")
    print(f"  Total volume (USD): ${stats['total_volume_usd']:,.2f}")
