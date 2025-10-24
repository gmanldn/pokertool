# Multi-Currency Support

PokerTool supports multiple currencies for international poker play.

## Supported Currencies

- USD ($) - US Dollar
- EUR (€) - Euro
- GBP (£) - British Pound
- CAD ($) - Canadian Dollar
- AUD ($) - Australian Dollar
- JPY (¥) - Japanese Yen
- CNY (¥) - Chinese Yuan
- BTC - Bitcoin
- ETH - Ethereum

## Currency Detection

The system automatically detects currency symbols in bet amounts using OCR and regex patterns.

## Configuration

Set your default currency in config:
```python
{
    "currency": "USD",
    "currency_symbol": "$",
    "decimal_places": 2
}
```

## Exchange Rates

Exchange rates are fetched from external APIs and cached for 1 hour. All internal calculations use USD as the base currency for normalization.

## Implementation

Implemented in task #13. See `src/pokertool/currency_converter.py` for details.
