# Platform Signing & Notarization Guide

This guide captures the release engineering steps required to ship signed PokerTool binaries on macOS and Windows. It pairs with the launcher asset bundle in `assets/launchers/`.

## macOS (Notarized .app or .dmg)

1. **Prerequisites**
   - Apple Developer ID Application certificate installed locally (`Keychain Access > Certificates`).
   - App-specific Apple ID credentials for `notarytool`.
   - Generated `AppIcon.icns` via `iconutil -c icns assets/launchers/macos/AppIcon.iconset`.

2. **Bundle Metadata**
   - Copy `assets/launchers/macos/Info.plist` into `<app>.app/Contents/Info.plist`.
   - Update `CFBundleIdentifier`, `CFBundleShortVersionString`, and `CFBundleVersion` to match the release tag.

3. **Code Signing**
   ```bash
   codesign --deep --force --options runtime \
     --sign "Developer ID Application: <Team Name> (<Team ID>)" \
     PokerTool.app
   ```

4. **Notarization**
   ```bash
   xcrun notarytool submit PokerTool.zip \
     --apple-id "<apple_id>" \
     --team-id "<team_id>" \
     --password "<app-specific-password>" \
     --wait
   ```

5. **Stapling**
   ```bash
   xcrun stapler staple PokerTool.app
   ```

6. **Verification**
   ```bash
   spctl --assess --verbose PokerTool.app
   ```

## Windows (Code-Signed Installer)

1. **Prerequisites**
   - Extended Validation (EV) or Organisation Code Signing certificate installed (typically on an HSM/USB token).
   - Generated `assets/launchers/windows/pokertool.ico`.
   - Built `.msi` or `.exe` installer.

2. **Timestamped Signing**
   ```powershell
   signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 `
     /a /v PokerToolSetup.exe
   ```

3. **Verification**
   ```powershell
   signtool verify /pa /v PokerToolSetup.exe
   ```

4. **SmartScreen Reputation**
   - Upload first release to Microsoft Partner Center for reputation seeding.

## CI Integration Notes

- Store signing credentials in secure CI secrets (GitHub Actions OIDC, Azure Key Vault, etc.).
- Parameterise version numbers to avoid manual edits in `Info.plist` or installer manifests.
- Run `scripts/generate_launcher_assets.py` as part of packaging to keep icon variants fresh.
