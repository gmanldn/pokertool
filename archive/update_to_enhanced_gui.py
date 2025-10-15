cd /Users/georgeridout/Documents/github/pokertool && python3 << 'EOF'
import re

# Read the file
with open('src/pokertool/enhanced_gui.py', 'r') as f:
    content = f.read()

# Update version
content = re.sub(
    r"Version: 20\.1\.0\nLast Modified: 2025-09-30",
    "Version: 21.0.0\nLast Modified: 2025-10-04",
    content
)

# Update __version__
content = re.sub(
    r"__version__ = '20\.1\.0'",
    "__version__ = '21.0.0'",
    content
)

# Update changelog
content = re.sub(
    r"Change Log:\n    - v20\.1\.0 \(2025-09-30\): Added auto-start scraper",
    "Change Log:\n    - v21.0.0 (2025-10-04): Refactored to use gui_components module instead of gui module\n    - v20.1.0 (2025-09-30): Added auto-start scraper",
    content
)

# Update import from gui to gui_components
content = re.sub(
    r"from \.gui import \(\n        EnhancedPokerAssistant,\n        EnhancedPokerAssistantFrame,",
    "from .gui_components import (\n        EnhancedPokerAssistantFrame,",
    content
)

# Write back
with open('src/pokertool/enhanced_gui.py', 'w') as f:
    f.write(content)

print("✅ Enhanced GUI updated successfully")
EOF