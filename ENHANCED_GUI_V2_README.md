# PokerTool Enhanced GUI v21.0.0 - Complete Documentation

## 🎰 Overview

The Enhanced PokerTool GUI v21.0.0 is an enterprise-grade poker analysis application featuring integrated screen scraping, real-time table monitoring, and advanced hand analysis. Designed for maximum reliability, clarity, and cross-platform compatibility.

## ✨ Key Features

### 🔍 Desktop-Independent Screen Scraping
- **Cross-platform compatibility**: Works on Windows, macOS, and Linux
- **Multi-workspace support**: Detects poker windows across all virtual desktops
- **Automatic table detection**: Recognizes major poker sites automatically
- **Real-time monitoring**: Continuous capture and analysis
- **Performance optimized**: Caching and adaptive intervals

### 🎯 Hand Analysis Engine
- **Position-aware recommendations**: Adjusts strategy based on table position
- **Pot odds calculations**: Automatic calculation of pot odds and equity
- **Multi-opponent modeling**: Considers number of active opponents
- **Real-time strength evaluation**: 0-10 scale hand strength assessment
- **Board texture analysis**: Evaluates flop/turn/river dynamics

### 📊 Visual Table Representation
- **9-max table visualization**: Clear seat positions and player states
- **Card display**: Shows hole cards and board cards
- **Pot and bet tracking**: Visual representation of pot size and bets
- **Dealer button indicator**: Tracks dealer position
- **Player status**: Active/inactive players with stack sizes

### 🛠️ Professional Interface
- **Tabbed organization**: Separate tabs for scraper, manual entry, analysis, settings
- **Status indicators**: Real-time visual feedback on system status
- **Performance metrics**: Monitor capture rates, success rates, and timing
- **Error handling**: Comprehensive error detection and user-friendly messages
- **Dark theme**: Professional, eye-friendly color scheme

## 📋 Requirements

### System Requirements
- **Python**: 3.7 or higher
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 20.04+)
- **RAM**: Minimum 4GB (8GB recommended for screen scraping)
- **Display**: 1280x800 minimum resolution (1920x1080 recommended)

### Required Dependencies
```bash
tkinter          # Usually included with Python
numpy>=1.26.4
Pillow>=10.0.0
```

### Screen Scraping Dependencies
```bash
mss>=9.0.0                      # Cross-platform screen capture
opencv-python>=4.8.0            # Computer vision
pytesseract>=0.3.10            # OCR text recognition
```

### Platform-Specific Dependencies
```bash
# macOS only
pyobjc-framework-Quartz>=9.0

# Windows only
pywin32>=306

# Linux only
python-xlib>=0.33
wmctrl (system package)
```

## 🚀 Installation

### Option 1: Quick Install (Recommended)
```bash
# Clone repository
git clone https://github.com/gmanldn/pokertool.git
cd pokertool

# Install dependencies
pip install -r requirements.txt

# Run the GUI
python launch_enhanced_gui_v2.py
```

### Option 2: Development Install
```bash
# Clone repository
git clone https://github.com/gmanldn/pokertool.git
cd pokertool

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Install dependencies
pip install -r requirements.txt

# Run the GUI
python launch_enhanced_gui_v2.py
```

### Option 3: Standalone Executable (Coming Soon)
Pre-built executables will be available for Windows, macOS, and Linux.

## 📖 User Guide

### Getting Started

1. **Launch the Application**
   ```bash
   python launch_enhanced_gui_v2.py
   ```

2. **Choose Your Workflow**
   - **Screen Scraper Tab**: For automated detection and monitoring
   - **Manual Entry Tab**: For direct card input and analysis

### Screen Scraper Workflow

#### Step 1: Scan for Poker Windows
1. Click the **"🔍 Scan for Poker Windows"** button
2. Wait for the scan to complete (1-3 seconds)
3. Review detected windows in the list

#### Step 2: Select a Window
1. Click on a poker window in the list
2. The table visualization will update automatically
3. View capture details and detected elements

#### Step 3: Start Monitoring (Optional)
1. Click **"▶️ Start Monitoring"** button
2. The scraper will continuously capture and analyze selected windows
3. Click **"⏸️ Stop Monitoring"** to pause

#### Scraper Settings
- **Scan Interval**: Time between captures (default: 2.0 seconds)
- **Detection Mode**: 
  - `window_title`: Match by window title patterns
  - `process_name`: Match by process/executable name
  - `combined`: Use both methods (recommended)
  - `fuzzy_match`: Fuzzy matching for similar titles

### Manual Entry Workflow

#### Step 1: Enter Hole Cards
1. Navigate to **"✏️ Manual Entry"** tab
2. Enter your two hole cards in the format: `As`, `Kh`, etc.
   - Ranks: `A`, `K`, `Q`, `J`, `T`, `9`-`2`
   - Suits: `S` (Spades), `H` (Hearts), `D` (Diamonds), `C` (Clubs)

#### Step 2: Enter Board Cards (Post-Flop)
1. Enter up to 5 board cards in the same format
2. Leave empty if pre-flop

#### Step 3: Configure Game State
1. **Position**: Select your table position
   - Early: UTG, UTG+1, UTG+2
   - Middle: MP, MP+1, MP+2
   - Late: CO, BTN
   - Blinds: SB, BB

2. **Pot Size**: Enter current pot size in dollars

3. **To Call**: Enter amount you need to call

4. **Opponents**: Enter number of active opponents

#### Step 4: Analyze
1. Click **"⚡ ANALYZE HAND"** button
2. Review results in the right panel:
   - Hand type (e.g., ONE_PAIR, FLUSH, etc.)
   - Hand strength (0-10 scale)
   - Recommendation (FOLD, CALL, or RAISE)
   - Detailed reasoning

### Understanding Analysis Results

#### Hand Strength Scale (0-10)
- **0-3**: Very weak hands, almost always fold
- **3-5**: Weak hands, fold unless favorable conditions
- **5-6**: Marginal hands, position and pot odds critical
- **6-7**: Good hands, usually call or raise
- **7-8**: Strong hands, raise aggressively
- **8-9**: Very strong hands, always raise
- **9-10**: Monster hands, maximize value

#### Recommendations
- **FOLD**: Hand is too weak for current situation
- **CALL**: Hand has sufficient equity given pot odds
- **RAISE**: Hand is strong, increase pot size

#### Factors Considered
1. **Hand Type**: Current made hand or draw
2. **Position**: Early, middle, late, or blinds
3. **Pot Odds**: Ratio of bet to pot size
4. **Opponents**: Number of active players
5. **Board Texture**: Wet vs dry boards, paired boards

### Performance Metrics

Monitor scraper performance in the **Scraper Controls** panel:

- **Total Captures**: Number of windows captured
- **Success Rate**: Percentage of successful captures
- **Avg Time**: Average capture processing time (milliseconds)
- **Cache Hit Rate**: Percentage of cached results used
- **Detected Windows**: Number of poker windows found

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New Session |
| Ctrl+S | Scan for Windows |
| Ctrl+M | Toggle Monitoring |
| Ctrl+Q | Quit Application |

## 🔧 Advanced Configuration

### Scraper Configuration File

Create `pokertool_scraper_config.json`:

```json
{
  "scan_interval": 2.0,
  "detection_mode": "combined",
  "adaptive_intervals": true,
  "cache_ttl": 2.0,
  "poker_patterns": {
    "window_titles": [
      ".*PokerStars.*",
      ".*PartyPoker.*",
      ".*Ignition.*",
      ".*Custom Pattern.*"
    ],
    "process_names": [
      "PokerStars.exe",
      "CustomPoker.exe"
    ]
  }
}
```

### Custom Poker Site Detection

Add custom patterns to detect your poker site:

```python
from pokertool.desktop_independent_scraper import DesktopIndependentScraper

scraper = DesktopIndependentScraper()

# Add custom window title pattern
scraper.poker_patterns['window_titles'].append(r'.*MyPokerSite.*')

# Add custom process name
scraper.poker_patterns['process_names'].append('MyPokerSite.exe')
```

## 🐛 Troubleshooting

### GUI Won't Start

**Issue**: Error importing tkinter
```
Solution: Install tkinter
- Ubuntu/Debian: sudo apt-get install python3-tk
- macOS: Included with Python
- Windows: Included with Python
```

**Issue**: Missing dependencies
```
Solution: Install all requirements
pip install -r requirements.txt
```

### Screen Scraper Not Working

**Issue**: No windows detected
```
Solutions:
1. Make sure poker application is running
2. Try different detection mode (window_title, process_name, combined)
3. Check if window title contains "Poker" or similar keyword
4. Add custom pattern for your poker site
```

**Issue**: Captures are slow or timing out
```
Solutions:
1. Increase scan interval in settings
2. Reduce number of monitored windows
3. Disable adaptive intervals
4. Close other resource-intensive applications
```

**Issue**: OCR not recognizing text
```
Solutions:
1. Install tesseract-ocr system package
2. Verify pytesseract is installed
3. Check if poker table has clear, readable text
4. Increase window size for better OCR accuracy
```

### Platform-Specific Issues

#### macOS
**Issue**: Permission denied for screen capture
```
Solution: Grant Screen Recording permission
1. System Preferences > Security & Privacy > Privacy
2. Select "Screen Recording"
3. Add Terminal or Python to allowed apps
4. Restart application
```

#### Windows
**Issue**: pywin32 installation fails
```
Solution: Install Visual C++ redistributables
Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
```

#### Linux
**Issue**: wmctrl not found
```
Solution: Install wmctrl
sudo apt-get install wmctrl  # Debian/Ubuntu
sudo yum install wmctrl      # RedHat/Fedora
```

## 📊 Performance Optimization

### Best Practices

1. **Scan Interval**
   - Fast tables: 1.0-1.5 seconds
   - Normal tables: 2.0-3.0 seconds  
   - Slow tables: 3.0-5.0 seconds

2. **Detection Mode**
   - Use `combined` for best results
   - Use `window_title` if process name is unknown
   - Use `fuzzy_match` for maximum coverage

3. **Monitoring**
   - Monitor only active tables
   - Stop monitoring when not playing
   - Use adaptive intervals for automatic adjustment

4. **Resource Usage**
   - Close unused tabs in GUI
   - Limit number of simultaneous captures
   - Enable caching for repeated analyses

## 🧪 Testing

### Run Unit Tests
```bash
# Run all tests
python -m pytest tests/test_gui_enhanced_v2.py -v

# Run specific test class
python -m pytest tests/test_gui_enhanced_v2.py::TestScreenScraperIntegration -v

# Run with coverage
python -m pytest tests/test_gui_enhanced_v2.py --cov=pokertool --cov-report=html
```

### Manual Testing Checklist

- [ ] GUI launches successfully
- [ ] All tabs are accessible
- [ ] Screen scraper detects poker windows
- [ ] Manual card entry works correctly
- [ ] Hand analysis produces results
- [ ] Table visualization updates correctly
- [ ] Monitoring can be started and stopped
- [ ] Performance metrics are displayed
- [ ] Error messages are clear and helpful
- [ ] Application closes cleanly

## 📝 Version History

### v21.0.0 (2025-10-12) - Current Version
- ✨ Complete GUI rework with integrated screen scraping
- ✨ Real-time poker table detection and monitoring
- ✨ Enhanced visual feedback and status indicators
- ✨ Comprehensive error handling and reliability improvements
- ✨ Cross-platform desktop-independent scraping integration
- ✨ Professional dark theme UI
- ✨ Tabbed interface for organized workflow
- ✨ Performance metrics dashboard
- ✨ Comprehensive unit test coverage

### Previous Versions
See CHANGELOG.md for complete version history.

## 🤝 Contributing

We welcome contributions! Please see CONTRIBUTING.md for guidelines.

### Development Setup
```bash
# Clone repository
git clone https://github.com/gmanldn/pokertool.git
cd pokertool

# Create development environment
python -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/ -v

# Run GUI
python launch_enhanced_gui_v2.py
```

## 📄 License

MIT License - see LICENSE file for details.

## 👥 Authors

- **George Ridout** - Project Maintainer
- **PokerTool Development Team**

## 🙏 Acknowledgments

- Anthropic Claude for development assistance
- Open source community for dependencies
- Poker community for feedback and testing

## 📧 Support

- **Issues**: https://github.com/gmanldn/pokertool/issues
- **Discussions**: https://github.com/gmanldn/pokertool/discussions
- **Email**: support@pokertool.dev (if configured)

## 🔗 Links

- **Repository**: https://github.com/gmanldn/pokertool
- **Documentation**: https://pokertool.readthedocs.io (coming soon)
- **Website**: https://pokertool.dev (coming soon)

---

**Happy Poker Playing! 🎰♠️♥️♦️♣️**
