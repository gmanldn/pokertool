# Betfair Poker Setup Guide

This guide keeps the Betfair poker client in a configuration that matches the reference assets (`tests/BF_TEST.jpg`) and maximises OCR/CDP accuracy inside Pokertool.

## 1. Prerequisites
- Install the Betfair desktop or web client and log in before launching Pokertool.
- Use the default dark-table theme (purple felt) so colour thresholds align with the scraper.
- Enable "Remember my seat" in Betfair so your hero position stays bottom-centre (expected by the seat-mapping logic).
- If you plan to use the Chrome DevTools (CDP) mode, launch Chrome with remote debugging (`./launch_chrome_debug.sh`) before opening Betfair.

## 2. Optimal Window Size & Placement
- Resize the table to roughly **1280×720** (or the native size of `BF_TEST.jpg`) and avoid stretching past a 16:9 aspect ratio; ROI coordinates are calibrated for that footprint.
- Position the table fully on-screen with no OS decorations overlapping the felt; align the top edge below the menu bar to prevent capture of the title area.
- Keep a single table visible when possible. If you multi-table, stagger windows so that only the active table overlaps the capture region.
- Disable operating system scaling/HiDPI downscaling for the Betfair window; run the display at 100% scaling to keep pixel ratios intact.

## 3. Recommended Table Settings
- **Seat layout**: Six-max with avatars enabled; avoid compact/minimal modes that reshuffle seat widgets.
- **Dealer button**: Leave the yellow “D” chip enabled; it is required for positional logic (BF-013/BF-014).
- **Player info**: Show stack sizes, timers and status banners. Hide chat and mission panels where possible to reduce overlapping UI text.
- **Card deck**: Use the default four-colour deck; hearts/diamonds must stay visibly red for suit detection (BF-011).
- **Pot display**: Keep both pot text and chip badge visible; the scraper cross-checks them for consistency (BF-018/BF-019).
- **HUD overlays**: If you run third-party overlays, position them outside the table surface or disable them during capture to prevent OCR collisions.

## 4. Troubleshooting Checklist
- **Stacks read as £0.00** → Verify the table is at 100% zoom and lighting is not dimmed; rerun with the Betfair-specific OCR mode enabled (`docs/BETFAIR_FIXES_SUMMARY.md`).
- **Player names truncated** → Ensure avatars are visible and no overlay (emoji, mission pop-up) covers the nameplate. Capture a screenshot and compare with `tests/BF_TEST.jpg`.
- **Dealer button missing** → Confirm the table is not in observation mode and the yellow dealer chip is visible. If multi-tabling, activate the correct window before capture.
- **Timer or VPIP badges mis-read** → Reduce window animations and wait for the timer badge to stabilise; re-run calibration scripts in `tests/` to refresh cached ROIs.
- **Mission/rocket banner interfering** → Collapse the achievements drawer or mask the top-left corner via the Pokertool UI until BF-023/BF-024 masking tasks land.

## 5. Quick Verification Workflow
1. Launch Chrome with debugging (if using CDP) and open a Betfair table with the settings above.
2. Run Pokertool’s GUI or CLI capture (`python start.py --table-watch betfair`) and confirm hero seat detection (bottom-centre) is correct.
3. Trigger a hand to ensure pot values change in both display locations; verify the HUD or logs show matching amounts.
4. Capture a diagnostic screenshot (`python test_table_capture_diagnostic.py --live --no-save`) and compare against the expected overlays listed in `docs/BETFAIR_INTEGRATION_CHALLENGES.md`.

Sticking to this setup minimises discrepancies between live tables and the calibration artefacts, helping us close out the remaining Betfair TODOs faster.
