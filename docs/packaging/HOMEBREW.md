# Homebrew Formula Guide

## Overview

This guide covers creating a Homebrew formula for PokerTool, enabling easy installation on macOS and Linux via the `brew install` command.

## What is Homebrew?

Homebrew is the most popular package manager for macOS and Linux, providing:
- Simple installation commands
- Automatic dependency management
- Easy updates and uninstalls
- Version management
- Community-maintained formulas

## Formula Structure

### Basic Formula

Create `Formula/pokertool.rb`:

```ruby
class Pokertool < Formula
  desc "AI-Powered Poker Analysis Tool"
  homepage "https://github.com/gmanldn/pokertool"
  url "https://github.com/gmanldn/pokertool/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
  license "MIT"
  head "https://github.com/gmanldn/pokertool.git", branch: "main"

  depends_on "python@3.12"
  depends_on "postgresql@15"
  depends_on "redis"

  def install
    # Create virtual environment
    venv = virtualenv_create(libexec, "python3.12")
    
    # Install Python dependencies
    system libexec/"bin/pip", "install", "--no-cache-dir", "-r", "requirements.txt"
    
    # Install application
    venv.pip_install_and_link buildpath
    
    # Install configuration
    (etc/"pokertool").install "poker_config.example.json" => "poker_config.json"
    
    # Install data files
    (share/"pokertool").install "model_calibration_data"
    (share/"pokertool").install "ranges"
    (share/"pokertool").install "assets"
  end

  def post_install
    # Create necessary directories
    (var/"log/pokertool").mkpath
    (var/"lib/pokertool").mkpath
  end

  service do
    run [opt_bin/"pokertool", "server"]
    keep_alive true
    log_path var/"log/pokertool/output.log"
    error_log_path var/"log/pokertool/error.log"
    environment_variables PATH: std_service_path_env
  end

  test do
    system bin/"pokertool", "--version"
    assert_match "PokerTool", shell_output("#{bin}/pokertool --help")
  end
end
```

## Formula Components

### Metadata

```ruby
desc "AI-Powered Poker Analysis Tool"
homepage "https://github.com/gmanldn/pokertool"
url "https://github.com/gmanldn/pokertool/archive/refs/tags/v1.0.0.tar.gz"
sha256 "1234567890abcdef..."  # SHA256 of the tarball
license "MIT"
```

### Dependencies

```ruby
# Runtime dependencies
depends_on "python@3.12"
depends_on "postgresql@15"
depends_on "redis"
depends_on "opencv"

# Build dependencies
depends_on "cmake" => :build
depends_on "pkg-config" => :build

# Optional dependencies
depends_on "tesseract" => :optional
```

### Installation

```ruby
def install
  # Install Python application
  virtualenv_install_with_resources
  
  # Or manual installation
  system "python3", "setup.py", "install", "--prefix=#{prefix}"
  
  # Install config files
  (etc/"pokertool").install "config" => "poker_config.json"
  
  # Install data files
  pkgshare.install "model_calibration_data", "ranges", "assets"
end
```

### Post-Installation

```ruby
def post_install
  # Create directories
  (var/"log/pokertool").mkpath
  (var/"lib/pokertool/data").mkpath
  
  # Set permissions
  chmod 0755, var/"log/pokertool"
end
```

### Service Configuration (launchd)

```ruby
service do
  run [opt_bin/"pokertool", "server", "--port", "8000"]
  keep_alive true
  working_dir var/"lib/pokertool"
  log_path var/"log/pokertool/output.log"
  error_log_path var/"log/pokertool/error.log"
  environment_variables PATH: std_service_path_env,
                        HOME: var/"lib/pokertool"
end
```

### Tests

```ruby
test do
  # Version check
  system bin/"pokertool", "--version"
  
  # Help text
  assert_match "PokerTool", shell_output("#{bin}/pokertool --help")
  
  # Functional test
  output = shell_output("#{bin}/pokertool config validate")
  assert_match "valid", output.downcase
end
```

## Generating SHA256

```bash
# Download release tarball
curl -L -o pokertool-1.0.0.tar.gz \
  https://github.com/gmanldn/pokertool/archive/refs/tags/v1.0.0.tar.gz

# Calculate SHA256
shasum -a 256 pokertool-1.0.0.tar.gz

# Or use Homebrew helper
brew fetch --force-bottle --deps https://github.com/gmanldn/pokertool/archive/refs/tags/v1.0.0.tar.gz
```

## Testing Formula Locally

```bash
# Install formula locally
brew install --build-from-source ./Formula/pokertool.rb

# Test formula
brew test pokertool

# Audit formula
brew audit --strict --online pokertool

# Style check
brew style pokertool

# Uninstall
brew uninstall pokertool
```

## Custom Tap

### Create Tap Repository

```bash
# Create tap repository
mkdir -p homebrew-pokertool
cd homebrew-pokertool

# Initialize git
git init
git remote add origin https://github.com/gmanldn/homebrew-pokertool.git

# Create Formula directory
mkdir -p Formula

# Add formula
cp pokertool.rb Formula/

# Commit and push
git add Formula/pokertool.rb
git commit -m "Add pokertool formula"
git push origin main
```

### Using Custom Tap

```bash
# Add tap
brew tap gmanldn/pokertool

# Install from tap
brew install gmanldn/pokertool/pokertool

# Update tap
brew update

# Remove tap
brew untap gmanldn/pokertool
```

## Submitting to Homebrew Core

### Prerequisites

1. **Stable Release**: Must have tagged release
2. **License**: Clear license specified
3. **Tests**: Working test block
4. **Documentation**: README with usage
5. **CI**: Passing GitHub Actions

### Submission Process

```bash
# Fork homebrew-core
gh repo fork Homebrew/homebrew-core

# Clone fork
git clone https://github.com/YOUR_USERNAME/homebrew-core.git
cd homebrew-core

# Create branch
git checkout -b pokertool

# Create formula
brew create https://github.com/gmanldn/pokertool/archive/refs/tags/v1.0.0.tar.gz

# Edit formula
# Edit Formula/pokertool.rb

# Test thoroughly
brew install --build-from-source ./Formula/pokertool.rb
brew test pokertool
brew audit --strict --online pokertool

# Commit
git add Formula/pokertool.rb
git commit -m "pokertool 1.0.0 (new formula)"

# Push and create PR
git push origin pokertool
gh pr create --title "pokertool 1.0.0 (new formula)" \
  --body "New formula for PokerTool - AI-Powered Poker Analysis Tool"
```

## Formula Updates

### Version Updates

```ruby
class Pokertool < Formula
  desc "AI-Powered Poker Analysis Tool"
  homepage "https://github.com/gmanldn/pokertool"
  url "https://github.com/gmanldn/pokertool/archive/refs/tags/v1.1.0.tar.gz"  # Updated
  sha256 "newsha256hash..."  # Updated
  license "MIT"
  
  # Version history
  revision 0  # Increment for formula-only changes
  
  # Deprecated/disabled
  # deprecate! date: "2025-01-01", because: "is no longer maintained"
  # disable! date: "2025-01-01", because: "does not build"
end
```

### Updating Formula

```bash
# Update to new version
brew bump-formula-pr \
  --url=https://github.com/gmanldn/pokertool/archive/refs/tags/v1.1.0.tar.gz \
  --sha256=newsha256... \
  pokertool
```

## Advanced Features

### Bottles (Pre-compiled Binaries)

```ruby
class Pokertool < Formula
  # ...
  
  bottle do
    root_url "https://github.com/gmanldn/pokertool/releases/download/v1.0.0"
    sha256 cellar: :any, ventura: "sha256hash..."
    sha256 cellar: :any, monterey: "sha256hash..."
    sha256 cellar: :any, big_sur: "sha256hash..."
  end
  
  # ...
end
```

### Build Bottles

```bash
# Build bottle
brew install --build-bottle pokertool
brew bottle pokertool

# Upload bottle
gh release upload v1.0.0 pokertool--1.0.0.*.bottle.tar.gz

# Update formula with bottle info
brew bottle --merge --write pokertool--1.0.0.*.bottle.json
```

### Multiple Versions

```ruby
# pokertool@1.rb (old version)
class PokerToolAT1 < Formula
  desc "AI-Powered Poker Analysis Tool (version 1.x)"
  homepage "https://github.com/gmanldn/pokertool"
  url "https://github.com/gmanldn/pokertool/archive/refs/tags/v1.9.9.tar.gz"
  # ...
  
  keg_only :versioned_formula
end
```

### Caveats

```ruby
def caveats
  <<~EOS
    To start pokertool:
      brew services start pokertool
    
    Configuration file:
      #{etc}/pokertool/poker_config.json
    
    Documentation:
      #{HOMEBREW_PREFIX}/share/doc/pokertool/README.md
    
    To use the Python API:
      export PYTHONPATH="#{lib}/python3.12/site-packages:$PYTHONPATH"
  EOS
end
```

## Common Patterns

### Python Application

```ruby
class Pokertool < Formula
  include Language::Python::Virtualenv
  
  def install
    virtualenv_install_with_resources
  end
end
```

### With Resources

```ruby
class Pokertool < Formula
  # Main package
  url "https://github.com/gmanldn/pokertool/archive/v1.0.0.tar.gz"
  
  # Python dependencies as resources
  resource "numpy" do
    url "https://files.pythonhosted.org/packages/.../numpy-1.24.0.tar.gz"
    sha256 "..."
  end
  
  resource "pandas" do
    url "https://files.pythonhosted.org/packages/.../pandas-2.0.0.tar.gz"
    sha256 "..."
  end
  
  def install
    virtualenv_install_with_resources
  end
end
```

### macOS-Specific

```ruby
class Pokertool < Formula
  # ...
  
  on_macos do
    depends_on "llvm" if MacOS.version >= :mojave
  end
  
  on_linux do
    depends_on "gcc"
  end
  
  def install
    if OS.mac?
      # macOS-specific installation
    else
      # Linux-specific installation
    end
  end
end
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Homebrew Test

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Homebrew
        run: |
          /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      
      - name: Test formula
        run: |
          brew install --build-from-source ./Formula/pokertool.rb
          brew test pokertool
          brew audit --strict pokertool
      
      - name: Test service
        run: |
          brew services start pokertool
          sleep 5
          curl -f http://localhost:8000/health
          brew services stop pokertool
```

## Distribution

### GitHub Releases

```bash
# Create release
gh release create v1.0.0 \
  --title "PokerTool v1.0.0" \
  --notes "Release notes here"

# Add tarball (automatically created by GitHub)
# Formula will reference:
# https://github.com/gmanldn/pokertool/archive/refs/tags/v1.0.0.tar.gz
```

### Documentation

Create `README.md` in tap repository:

```markdown
# PokerTool Homebrew Tap

## Installation

```bash
brew tap gmanldn/pokertool
brew install pokertool
```

## Usage

```bash
# Start server
pokertool server

# Or use as service
brew services start pokertool
```

## Configuration

Edit configuration file:
```bash
$EDITOR /opt/homebrew/etc/pokertool/poker_config.json
```

## Troubleshooting

View logs:
```bash
tail -f /opt/homebrew/var/log/pokertool/output.log
```
```

## Best Practices

1. **Test thoroughly** - Test on multiple macOS versions
2. **Follow conventions** - Use Homebrew style guide
3. **Provide tests** - Include meaningful test block
4. **Document caveats** - Inform users of important info
5. **Use service** - Provide launchd service when appropriate
6. **Keep updated** - Update formula for new releases
7. **Audit regularly** - Run brew audit before submitting
8. **Respond to feedback** - Address reviewer comments promptly

## Troubleshooting

### Formula Errors

```bash
# Detailed error output
brew install --verbose --debug pokertool

# Check dependencies
brew deps pokertool

# Fix linkage issues
brew link pokertool
```

### Build Failures

```bash
# Clean and retry
brew cleanup pokertool
brew install --build-from-source pokertool

# Check logs
cat ~/Library/Logs/Homebrew/pokertool/
```

## Next Steps

- Review [Chocolatey Package](CHOCOLATEY.md)
- Explore [Winget Package](WINGET.md)
- Set up [Native Installers](NATIVE_INSTALLERS.md)

## References

- [Homebrew Documentation](https://docs.brew.sh/)
- [Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Python Formulae](https://docs.brew.sh/Python-for-Formula-Authors)
- [Homebrew Style Guide](https://docs.brew.sh/Formula-Cookbook#style-guide)
- [Acceptable Formulae](https://docs.brew.sh/Acceptable-Formulae)
