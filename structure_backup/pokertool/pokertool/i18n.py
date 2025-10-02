"""Internationalization utilities for PokerTool."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

# Paths
_BASE_DIR = Path(__file__).resolve().parents[2]
_LOCALE_MESSAGES_DIR = _BASE_DIR / "locales" / "messages"

# Metadata for supported locales
_LOCALE_METADATA: Dict[str, Dict[str, Any]] = {
    "en": {
        "name": "English (US)",
        "currency": "USD",
        "decimal_sep": ".",
        "thousands_sep": ",",
        "currency_symbol": "$",
        "symbol_first": True,
        "date_format": "%m/%d/%Y",
        "time_format": "%H:%M",
        "datetime_format": "%m/%d/%Y %H:%M",
    },
    "es": {
        "name": "Español (EU)",
        "currency": "EUR",
        "decimal_sep": ",",
        "thousands_sep": ".",
        "currency_symbol": "€",
        "symbol_first": False,
        "date_format": "%d/%m/%Y",
        "time_format": "%H:%M",
        "datetime_format": "%d/%m/%Y %H:%M",
    },
    "de": {
        "name": "Deutsch",
        "currency": "EUR",
        "decimal_sep": ",",
        "thousands_sep": ".",
        "currency_symbol": "€",
        "symbol_first": False,
        "date_format": "%d.%m.%Y",
        "time_format": "%H:%M",
        "datetime_format": "%d.%m.%Y %H:%M",
    },
    "zh-CN": {
        "name": "简体中文",
        "currency": "CNY",
        "decimal_sep": ".",
        "thousands_sep": ",",
        "currency_symbol": "¥",
        "symbol_first": True,
        "date_format": "%Y/%m/%d",
        "time_format": "%H:%M",
        "datetime_format": "%Y/%m/%d %H:%M",
    },
}

_CURRENCY_RATES: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.93,
    "GBP": 0.78,
    "JPY": 148.0,
    "CNY": 7.3,
    "BRL": 5.15,
}

_DEFAULT_LOCALE = "en"


@dataclass
class LocaleListener:
    """Callback container for locale change notifications."""

    callback: Callable[[str], None]
    token: int


class TranslationManager:
    """Loads and serves translation strings for the application."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._translations: Dict[str, Dict[str, str]] = {}
        self._current_locale: str = _DEFAULT_LOCALE
        self._listeners: Dict[int, LocaleListener] = {}
        self._next_listener_token = 1
        self._ensure_locale_directory()
        self._load_locale(_DEFAULT_LOCALE)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def current_locale(self) -> str:
        with self._lock:
            return self._current_locale

    def available_locales(self) -> List[Dict[str, str]]:
        locales: List[Dict[str, str]] = []
        for code, meta in _LOCALE_METADATA.items():
            locales.append({
                "code": code,
                "name": meta["name"],
                "currency": meta["currency"],
            })
        return sorted(locales, key=lambda item: item["name"].lower())

    def translate(self, key: str, default: Optional[str] = None, **kwargs: Any) -> str:
        with self._lock:
            locale = self._current_locale
            value = self._lookup(locale, key)
            if value is None and locale != _DEFAULT_LOCALE:
                value = self._lookup(_DEFAULT_LOCALE, key)
            if value is None:
                value = default if default is not None else key
        if kwargs:
            try:
                return value.format(**kwargs)
            except Exception:
                return value
        return value

    def set_locale(self, locale_code: str) -> None:
        if locale_code not in _LOCALE_METADATA:
            raise ValueError(f"Unsupported locale: {locale_code}")
        with self._lock:
            if locale_code == self._current_locale:
                return
            self._load_locale(locale_code)
            self._current_locale = locale_code
            listeners = list(self._listeners.values())
        for listener in listeners:
            try:
                listener.callback(locale_code)
            except Exception:
                continue

    def format_decimal(self, value: float, digits: int = 0, locale: Optional[str] = None) -> str:
        locale = locale or self.current_locale
        meta = _LOCALE_METADATA.get(locale, _LOCALE_METADATA[_DEFAULT_LOCALE])
        quantize_pattern = Decimal(10) ** -digits if digits > 0 else Decimal("1")
        decimal_value = Decimal(str(value)).quantize(quantize_pattern, rounding=ROUND_HALF_UP)
        formatted = f"{decimal_value:,.{digits}f}"
        if meta["thousands_sep"] != ",":
            formatted = formatted.replace(",", "␟")
        if meta["decimal_sep"] != ".":
            formatted = formatted.replace(".", "␡")
        formatted = formatted.replace("␟", meta["thousands_sep"]).replace("␡", meta["decimal_sep"])
        return formatted

    def convert_currency(self, amount_usd: float, target_currency: str) -> float:
        rate = _CURRENCY_RATES.get(target_currency.upper())
        if rate is None:
            return amount_usd
        return float(Decimal(str(amount_usd)) * Decimal(str(rate)))

    def format_currency(self, amount_usd: float, currency: Optional[str] = None, locale: Optional[str] = None) -> str:
        locale = locale or self.current_locale
        meta = _LOCALE_METADATA.get(locale, _LOCALE_METADATA[_DEFAULT_LOCALE])
        target_currency = currency or meta["currency"]
        converted = self.convert_currency(amount_usd, target_currency)
        digits = 2 if target_currency.upper() not in {"JPY"} else 0
        formatted_amount = self.format_decimal(converted, digits=digits, locale=locale)
        symbol = meta.get("currency_symbol", "$")
        if target_currency.upper() != meta["currency"]:
            symbol = self._currency_symbol(target_currency)
        if meta.get("symbol_first", True):
            return f"{symbol}{formatted_amount}"
        return f"{formatted_amount} {symbol}"

    def format_datetime(self, dt: datetime, locale: Optional[str] = None) -> str:
        locale = locale or self.current_locale
        meta = _LOCALE_METADATA.get(locale, _LOCALE_METADATA[_DEFAULT_LOCALE])
        fmt = meta.get("datetime_format", "%Y-%m-%d %H:%M")
        return dt.strftime(fmt)

    def register_listener(self, callback: Callable[[str], None]) -> int:
        with self._lock:
            token = self._next_listener_token
            self._next_listener_token += 1
            self._listeners[token] = LocaleListener(callback=callback, token=token)
        return token

    def unregister_listener(self, token: int) -> None:
        with self._lock:
            self._listeners.pop(token, None)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_locale_directory(self) -> None:
        _LOCALE_MESSAGES_DIR.mkdir(parents=True, exist_ok=True)

    def _load_locale(self, locale_code: str) -> None:
        messages_path = _LOCALE_MESSAGES_DIR / f"{locale_code}.json"
        translations: Dict[str, str] = {}
        if messages_path.exists():
            try:
                translations = json.loads(messages_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                translations = {}
        self._translations[locale_code] = translations

    def _lookup(self, locale_code: str, key: str) -> Optional[str]:
        return self._translations.get(locale_code, {}).get(key)

    def _currency_symbol(self, currency: str) -> str:
        symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥",
            "CNY": "¥",
            "BRL": "R$",
        }
        return symbols.get(currency.upper(), currency.upper())


# Global translation manager instance
_translation_manager = TranslationManager()


# Convenience API -----------------------------------------------------------

def translate(key: str, default: Optional[str] = None, **kwargs: Any) -> str:
    return _translation_manager.translate(key, default=default, **kwargs)


def set_locale(locale_code: str) -> None:
    _translation_manager.set_locale(locale_code)


def get_current_locale() -> str:
    return _translation_manager.current_locale


def available_locales() -> List[Dict[str, str]]:
    return _translation_manager.available_locales()


def format_decimal(value: float, digits: int = 0) -> str:
    return _translation_manager.format_decimal(value, digits=digits)


def format_currency(amount_usd: float, currency: Optional[str] = None) -> str:
    return _translation_manager.format_currency(amount_usd, currency=currency)


def convert_currency(amount_usd: float, target_currency: str) -> float:
    return _translation_manager.convert_currency(amount_usd, target_currency)


def format_datetime(dt: datetime) -> str:
    return _translation_manager.format_datetime(dt)


def register_locale_listener(callback: Callable[[str], None]) -> int:
    return _translation_manager.register_listener(callback)


def unregister_locale_listener(token: int) -> None:
    _translation_manager.unregister_listener(token)


__all__ = [
    "translate",
    "set_locale",
    "get_current_locale",
    "available_locales",
    "format_decimal",
    "format_currency",
    "convert_currency",
    "format_datetime",
    "register_locale_listener",
    "unregister_locale_listener",
]
