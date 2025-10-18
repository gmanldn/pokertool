# Betfair Integration Challenges

## Context
- Betfair poker tables use a distinctive dark purple felt with high-contrast overlays.
- The reference capture (`tests/BF_TEST.jpg`) shows a six-max tournament table at the river with mixed player states (active, sitting out, empty).
- Several UX elements (mission banner, action panels, stat badges) sit close to core gameplay data, making OCR extraction sensitive to layout shifts.

## UI Layout Differences
- **Seat Geometry**: Six fixed positions (top-left/centre/right and bottom-left/centre/right) with hero typically bottom-centre, requiring precise ROI mapping for each seat.
- **Dual Pot Displays**: Pot amount appears both as `"Pot: £X.XX"` text and as a chips badge (`"£X.XX"`) near the centre of the felt; both must stay in sync.
- **Overlay Density**: Hamburger menu, rocket badge and “Sit Out Options” panel crowd the top-left and bottom-left corners, overlapping potential OCR regions if not masked.
- **Action Indicators**: Dealer button (yellow “D”), time bank countdown and optional VPIP/AF stat badges are rendered adjacent to avatars, so positional logic must account for these adornments.
- **Tournament Branding**: Large banner text (e.g. *ELITE SERIES XL ULTIMATE EDITION*) and date strings sit across the table background and must be filtered from gameplay parsing.

## Text Formatting Quirks
- **Mixed Case & Alphanumeric Names**: Usernames such as `FourBoysUnited`, `ThelongbluevEin` and `GmanLDN` mix case and numerals, demanding relaxed OCR post-processing that still rejects table-branded text.
- **Currency Formatting**: Stack, pot and chip values always include the pound symbol (`£`) with two decimal places (`£0.08`, `£2.62`); sitting-out seats display `£0.00`.
- **Status Labels**: Seats can show `"SIT OUT"` overlays or `"Empty"` labels, which must map cleanly to player state without colliding with name detection.
- **Timer Strings**: Active decision timers follow the `"Time: NN"` pattern on a translucent badge near the acting player and should be associated with the correct seat.

## Visual & Theme Considerations
- **Colour Palette**: Bright white text on dark backgrounds means OCR preprocessing must invert or threshold carefully; red suits and yellow dealer chips require tuned HSV ranges.
- **Transparency & Glow Effects**: Many overlays include drop shadows or gradient fills, so binarisation should preserve glyph edges without amplifying noise.
- **Badge Variability**: VPIP/AF badges may appear or vanish per player, and multi-pot scenarios can introduce additional chip stacks that resemble currency labels.

## Known Limitations
- Robust seat-to-position mapping, hero seat confirmation and dealer button correlation remain outstanding (tracked as BF-025, BF-026, BF-014).
- UI masking for navigation menus, mission icons and action panels (BF-023, BF-024) is pending to prevent false positives.
- Multi-table awareness, simultaneous window handling and regression-grade Betfair scraping tests (BF-029 to BF-033) are not yet implemented.
- Colour-tuned OCR workflows for dark theme optimisation and card suit validation (BF-027, BF-011) still require calibration against broader screenshot sets.

## Related Assets
- `docs/BETFAIR_FIXES_SUMMARY.md` documents completed OCR adjustments and diagnostic scripts.
- `tests/BF_TEST.jpg` provides the canonical screenshot for validating preprocessing and recognition improvements.
- `src/pokertool/modules/poker_screen_scraper_betfair.py` hosts the current Betfair scraping pipeline referenced throughout these tasks.
