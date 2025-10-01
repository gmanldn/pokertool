"""Unit tests for internationalization utilities."""

from __future__ import annotations

from datetime import datetime
from typing import Iterator

import pytest

from src.pokertool.i18n import (
    available_locales,
    convert_currency,
    format_currency,
    format_datetime,
    format_decimal,
    get_current_locale,
    set_locale,
    translate,
)


@pytest.fixture(autouse=True)
def restore_locale() -> Iterator[None]:
    """Ensure locale changes do not leak between tests."""
    original = get_current_locale()
    try:
        yield
    finally:
        set_locale(original)


def test_translate_default_locale() -> None:
    set_locale('en')
    assert translate('tab.autopilot').startswith('🤖')
    assert translate('autopilot.settings.site').startswith('Poker')


def test_translate_spanish_locale() -> None:
    set_locale('es')
    assert translate('actions.detect_tables') == 'Detectar mesas'
    assert 'automáticamente' in translate('autopilot.log.auto_detect').lower()


def test_available_locales_contains_metadata() -> None:
    locales = {entry['code']: entry for entry in available_locales()}
    assert 'en' in locales
    assert locales['en']['name'] == 'English (US)'
    assert locales['es']['currency'] == 'EUR'


def test_format_decimal_respects_locale() -> None:
    set_locale('de')
    assert format_decimal(1234.56, digits=2) == '1.234,56'
    set_locale('en')
    assert format_decimal(1234.56, digits=2) == '1,234.56'


def test_currency_conversion_and_formatting() -> None:
    set_locale('de')
    formatted = format_currency(100)
    assert '€' in formatted
    converted = convert_currency(100, 'JPY')
    assert pytest.approx(converted, rel=1e-3) == 14800.0


def test_format_datetime_uses_locale_pattern() -> None:
    set_locale('zh-CN')
    sample = datetime(2025, 1, 2, 15, 30)
    assert format_datetime(sample) == '2025/01/02 15:30'
