#!/usr/bin/env python3
"""Tests for Currency Converter"""

import pytest
from src.pokertool.currency_converter import (
    CurrencyConverter,
    Currency,
    ConversionRecord
)


class TestCurrencyConverter:
    """Test suite for CurrencyConverter"""

    def test_initialization(self):
        """Test converter initialization"""
        converter = CurrencyConverter()
        assert converter.base_currency == Currency.USD
        assert len(converter.conversion_history) == 0
        assert converter.conversion_count == 0
        assert len(converter.exchange_rates) == 10

    def test_same_currency_conversion(self):
        """Test converting same currency returns same amount"""
        converter = CurrencyConverter()
        amount = converter.convert(100.0, Currency.USD, Currency.USD)
        assert amount == 100.0

    def test_usd_to_eur_conversion(self):
        """Test USD to EUR conversion"""
        converter = CurrencyConverter()
        amount = converter.convert(100.0, Currency.USD, Currency.EUR)

        # Should be approximately 92 EUR (based on 0.92 rate)
        assert 91.5 < amount < 92.5

    def test_eur_to_usd_conversion(self):
        """Test EUR to USD conversion"""
        converter = CurrencyConverter()
        amount = converter.convert(92.0, Currency.EUR, Currency.USD)

        # Should be approximately 100 USD
        assert 99.5 < amount < 100.5

    def test_gbp_to_jpy_conversion(self):
        """Test GBP to JPY cross conversion"""
        converter = CurrencyConverter()
        amount = converter.convert(100.0, Currency.GBP, Currency.JPY)

        # GBP is strong, JPY is weak, so should be large number
        assert amount > 15000

    def test_conversion_history_tracking(self):
        """Test that conversions are tracked"""
        converter = CurrencyConverter()

        converter.convert(100.0, Currency.USD, Currency.EUR)
        converter.convert(50.0, Currency.GBP, Currency.CAD)

        assert len(converter.conversion_history) == 2
        assert converter.conversion_count == 2

    def test_conversion_record_fields(self):
        """Test conversion record contains all fields"""
        converter = CurrencyConverter()
        converter.convert(100.0, Currency.USD, Currency.EUR)

        record = converter.conversion_history[0]
        assert record.from_currency == Currency.USD
        assert record.to_currency == Currency.EUR
        assert record.from_amount == 100.0
        assert record.to_amount > 0
        assert record.exchange_rate > 0
        assert record.conversion_id == 1

    def test_get_exchange_rate(self):
        """Test getting exchange rate"""
        converter = CurrencyConverter()
        rate = converter.get_exchange_rate(Currency.USD, Currency.EUR)

        assert rate == pytest.approx(0.92, 0.01)

    def test_get_exchange_rate_same_currency(self):
        """Test exchange rate for same currency is 1.0"""
        converter = CurrencyConverter()
        rate = converter.get_exchange_rate(Currency.USD, Currency.USD)

        assert rate == 1.0

    def test_set_exchange_rate(self):
        """Test updating exchange rate"""
        converter = CurrencyConverter()

        # Update EUR rate
        converter.set_exchange_rate(Currency.EUR, 0.95)
        assert converter.exchange_rates[Currency.EUR] == 0.95

        # Test conversion with new rate
        amount = converter.convert(100.0, Currency.USD, Currency.EUR)
        assert amount == pytest.approx(95.0, 0.01)

    def test_get_all_rates(self):
        """Test getting all exchange rates"""
        converter = CurrencyConverter()
        rates = converter.get_all_rates()

        assert len(rates) == 10
        assert rates[Currency.USD] == 1.0
        assert Currency.EUR in rates

    def test_format_amount_with_symbol(self):
        """Test formatting amount with symbol"""
        converter = CurrencyConverter()

        formatted = converter.format_amount(1234.56, Currency.USD, include_symbol=True)
        assert formatted == "$1,234.56"

        formatted_eur = converter.format_amount(1234.56, Currency.EUR, include_symbol=True)
        assert formatted_eur == "€1,234.56"

    def test_format_amount_without_symbol(self):
        """Test formatting amount without symbol"""
        converter = CurrencyConverter()

        formatted = converter.format_amount(1234.56, Currency.USD, include_symbol=False)
        assert formatted == "1,234.56 USD"

    def test_get_conversion_history(self):
        """Test retrieving conversion history"""
        converter = CurrencyConverter()

        for i in range(5):
            converter.convert(100.0 + i, Currency.USD, Currency.EUR)

        # Get all history
        all_history = converter.get_conversion_history()
        assert len(all_history) == 5

        # Get limited history
        limited = converter.get_conversion_history(limit=3)
        assert len(limited) == 3

    def test_statistics_generation(self):
        """Test statistics calculation"""
        converter = CurrencyConverter()

        converter.convert(100.0, Currency.USD, Currency.EUR)
        converter.convert(50.0, Currency.USD, Currency.GBP)
        converter.convert(75.0, Currency.EUR, Currency.USD)

        stats = converter.get_statistics()

        assert stats["total_conversions"] == 3
        assert stats["unique_currency_pairs"] == 3
        assert stats["most_common_from"] == "USD"
        assert stats["total_volume_usd"] > 0

    def test_empty_statistics(self):
        """Test statistics on empty converter"""
        converter = CurrencyConverter()
        stats = converter.get_statistics()

        assert stats["total_conversions"] == 0
        assert stats["unique_currency_pairs"] == 0
        assert stats["most_common_from"] is None
        assert stats["total_volume_usd"] == 0.0

    def test_reset_functionality(self):
        """Test converter reset"""
        converter = CurrencyConverter()

        converter.convert(100.0, Currency.USD, Currency.EUR)
        converter.convert(50.0, Currency.GBP, Currency.CAD)

        assert len(converter.conversion_history) == 2

        converter.reset()

        assert len(converter.conversion_history) == 0
        assert converter.conversion_count == 0

    def test_multiple_conversions(self):
        """Test multiple conversions maintain correct count"""
        converter = CurrencyConverter()

        for i in range(10):
            converter.convert(100.0, Currency.USD, Currency.EUR)

        assert converter.conversion_count == 10
        assert len(converter.conversion_history) == 10

    def test_all_currency_pairs(self):
        """Test conversions work for all currency pairs"""
        converter = CurrencyConverter()

        # Test USD to all others
        for currency in Currency:
            if currency != Currency.USD:
                amount = converter.convert(100.0, Currency.USD, currency)
                assert amount > 0

    def test_round_trip_conversion(self):
        """Test round trip conversion returns similar amount"""
        converter = CurrencyConverter()

        # USD -> EUR -> USD
        eur = converter.convert(100.0, Currency.USD, Currency.EUR)
        usd = converter.convert(eur, Currency.EUR, Currency.USD)

        # Should be very close to original (within 1%)
        assert abs(usd - 100.0) < 1.0

    def test_conversion_id_increment(self):
        """Test conversion IDs increment correctly"""
        converter = CurrencyConverter()

        converter.convert(100.0, Currency.USD, Currency.EUR)
        converter.convert(50.0, Currency.GBP, Currency.CAD)
        converter.convert(75.0, Currency.EUR, Currency.JPY)

        assert converter.conversion_history[0].conversion_id == 1
        assert converter.conversion_history[1].conversion_id == 2
        assert converter.conversion_history[2].conversion_id == 3

    def test_large_amount_conversion(self):
        """Test conversion of large amounts"""
        converter = CurrencyConverter()

        large_amount = 1000000.0  # 1 million
        converted = converter.convert(large_amount, Currency.USD, Currency.EUR)

        assert converted > 0
        assert converted < large_amount  # EUR is less than USD

    def test_small_amount_conversion(self):
        """Test conversion of small amounts"""
        converter = CurrencyConverter()

        small_amount = 0.01  # 1 cent
        converted = converter.convert(small_amount, Currency.USD, Currency.EUR)

        assert converted > 0
        assert converted < 0.02


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
