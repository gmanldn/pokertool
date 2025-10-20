# HUD Designer Developer Guide

Last updated: 2025-10-19

This guide explains how to record, save, and apply HUD overlay profiles in PokerTool.

Overview
- Profiles define layout, stats, and styles for the on-table HUD.
- Profiles can be recorded from a live table or composed from presets.
- Saved profiles are portable JSON files stored under `exports/` by default.

Record a Profile
- Open the HUD Designer in the UI.
- Enable “Record Positions”, then move/resize widgets on the table overlay.
- Click “Save Profile” when satisfied; provide a name and optional notes.

Apply a Profile
- Open HUD settings and select a saved profile from the list.
- Click “Apply” to switch the active overlay.
- Profile changes take effect on the next table detection refresh.

Organize Profiles
- Profiles are saved as JSON. Keep them in `exports/hud/` to sync with backups.
- Use semantic names, e.g., `hud_6max_aggressive.json`, `hud_9max_passive.json`.

Profile JSON Structure (excerpt)
- `name`: Human-readable name
- `widgets`: Array of widgets with `id`, `type`, `x`, `y`, `w`, `h`
- `stats`: Per-widget stat configuration (e.g., VPIP, PFR, 3Bet)
- `theme`: Colors, fonts, and density

Tips
- Create separate profiles per site/theme if table dimensions differ.
- Use the “Snap to Seats” option for consistent alignment.
- Export frequently used profiles to share across machines.

Troubleshooting
- If widgets drift, recalibrate table bounds in Settings → Table Detection.
- If a profile fails to load, validate JSON and check console logs.

