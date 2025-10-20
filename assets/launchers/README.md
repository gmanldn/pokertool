# Launcher Asset Bundle

This directory contains platform starter assets referenced by the packaging TODOs.

## macOS
- `macos/AppIcon.iconset/` – Retina-ready PNG set generated from `assets/icons/icon.png`. Run `iconutil -c icns AppIcon.iconset` to create `PokerTool.icns` during packaging.
- `macos/Info.plist` – Baseline bundle manifest; update `CFBundleShortVersionString` and signing identifiers in CI packaging jobs.

## Windows
- `windows/pokertool.ico` – Multi-resolution icon (16–256px) suitable for MSI/Inno installers and shortcut creation.

## Linux
- `linux/pokertool.desktop` – Desktop entry template that launches `pokertool gui`. Update the `Exec` path when packaging an AppImage/Flatpak.

Regenerate icons via:

```bash
python3 scripts/generate_launcher_assets.py
```

See `docs/PLATFORM_SIGNING.md` for platform-specific signing workflows.
