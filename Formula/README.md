# Homebrew Formula for PokerTool

This directory contains the Homebrew formula for PokerTool.

## Quick Install

```bash
# Add tap (if using custom tap)
brew tap gmanldn/pokertool

# Install
brew install pokertool
```

## Formula Details

The `pokertool.rb` formula provides:
- Python 3.12 environment
- All required dependencies
- System service integration
- Automatic configuration setup

## Usage

```bash
# Start server
pokertool server

# Or use as service
brew services start pokertool

# View logs
tail -f /opt/homebrew/var/log/pokertool/output.log
```

## Development

To test formula changes locally:

```bash
# Install from local formula
brew install --build-from-source ./Formula/pokertool.rb

# Test
brew test pokertool

# Audit
brew audit --strict pokertool
```

## Updating

When releasing a new version:

1. Update version in `pokertool.rb`
2. Update `url` to new release tarball
3. Calculate and update `sha256` checksum
4. Test installation
5. Submit PR to homebrew-core (if applicable)

## See Also

- [Homebrew Documentation](../docs/packaging/HOMEBREW.md)
- [Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
