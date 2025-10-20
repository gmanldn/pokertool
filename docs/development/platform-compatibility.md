# Platform Compatibility Matrix

PokerTool targets multiple poker sites with different levels of native support. The table below summarises the current posture, enforced compliance rules, and data pathways. This document is backed by `src/pokertool/platform_compatibility.py`, so both code and docs stay aligned.

| Site | Tier | Detection | HUD | Tracking | Hand Histories | Restricted Features |
| --- | --- | --- | --- | --- | --- | --- |
| Betfair | Tier 1 | Specialised Betfair detector with Chrome DevTools fast-path fallback. | Enabled | Enabled | Live capture via OCR/CDP (no raw hand import yet). | automated_play, real_time_advice |
| Americas Cardroom | Tier 2 | Universal detector with aggressive multi-table tuning. | Enabled | Enabled | Supported via HandConverter (text import). | automated_play |
| PartyPoker | Tier 2 | Universal detector with colour heuristics + OCR. | Enabled | Enabled | Supported via HandConverter (text import). | automated_play |
| PokerStars | Tier 2 | Universal detector with SmartPokerDetector prioritisation. | Disabled by compliance | Enabled | Supported via HandConverter (text import). | automated_play, real_time_advice |
| 888poker | Fallback | Universal detector with compliance-restricted OCR usage. | Disabled by compliance | Enabled | Supported via HandConverter (text import). | automated_play, ocr, real_time_advice |
| GGPoker | Fallback | Universal detector (screen OCR only, HUD disabled). | Disabled by compliance | Disabled by compliance | Supported via HandConverter (text import). | automated_play, hud_overlay, real_time_advice, screen_scraping |
| Winamax | Fallback | Universal detector with OCR heuristics. | Enabled | Enabled | Supported via HandConverter (text import). | automated_play, real_time_advice |

## Site Notes and Adaptations

### Betfair
- Specialised capture path (`src/pokertool/modules/poker_screen_scraper_betfair.py`) with ROI tuning in `src/pokertool/modules/betfair_accuracy_improvements.py`.
- Chrome DevTools integration (`src/pokertool/modules/chrome_devtools_scraper.py`) gives rapid state extraction; recommended when remote debugging is available.
- Compliance allows full HUD/analytics usage; defaults enforce `max_tables=12` from `src/pokertool/compliance.py`.
- Hand histories are gathered live; no raw text import yet, so archival requires CDP or screenshot archiving.

### PokerStars
- Uses the universal detector (`src/pokertool/modules/poker_screen_scraper_betfair.py`) plus prioritisation from `src/pokertool/smart_poker_detector.py`.
- Hand histories import seamlessly through `src/pokertool/hand_converter.py`.
- Compliance disables real-time HUD overlays; analytics are limited to post-session review (`src/pokertool/compliance.py`).

### PartyPoker
- Universal detector plus colour heuristics handle tables without site-specific tuning.
- Imports supported through `src/pokertool/hand_converter.py`; multi-table presets live in `src/pokertool/multi_table_support.py`.
- Compliance permits HUD/tracking but still blocks automated play.

### GGPoker
- Runs via the universal detector (OCR-only) with compliance denying HUD/tracking in real time.
- Approved usage focuses on post-session analytics; live insights should stay disabled according to `src/pokertool/compliance.py`.
- Hand histories import through `src/pokertool/hand_converter.py`.

### 888poker
- Universal detector operates in a restricted OCR mode because the site forbids deep OCR sweeps (`src/pokertool/compliance.py`).
- Hand histories import via `src/pokertool/hand_converter.py`; consider reduced polling to stay within ToS.

### Winamax
- Universal detection path with OCR heuristics; hand histories import via `src/pokertool/hand_converter.py`.
- HUD/tracking remain enabled but automated play is blocked by compliance defaults.

### Americas Cardroom
- Universal detector with aggressive multi-table presets from `src/pokertool/multi_table_support.py`.
- Hand histories import via `src/pokertool/hand_converter.py`; HUD/tracking enabled with a 24-table compliance cap.

## Keeping Docs and Code in Sync

- Update `src/pokertool/platform_compatibility.py` when support status or compliance rules change.
- Regenerate the Markdown table via `PYTHONPATH=src python3 -m pokertool.platform_compatibility --format markdown`.
- Tests in `tests/test_platform_compatibility.py` fail if required metadata is missing or compliance flags fall out of sync.
