# HUD Designer Developer Guide

## Overview

The HUD (Heads-Up Display) Designer provides a comprehensive interface for customizing the PokerTool overlay display. This guide covers recording, saving, and applying HUD profiles for optimal on-table performance.

## Table of Contents

- [Quick Start](#quick-start)
- [Recording a Profile](#recording-a-profile)
- [Customizing Settings](#customizing-settings)
- [Saving and Loading Profiles](#saving-and-loading-profiles)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Opening the HUD Designer

1. Launch the HUD overlay from the main PokerTool interface
2. Click the **"Customize HUD"** button in the HUD control bar
3. The HUD Designer window will open with tabbed configuration options

### Basic Workflow

```python
from pokertool.hud_overlay import HUDOverlay, HUDConfig

# Create HUD with default configuration
config = HUDConfig()
hud = HUDOverlay(config)
hud.start()

# The HUD is now running and can be customized via the GUI
```

## Recording a Profile

### Step 1: Configure Display Settings

Navigate to the **Display** tab in the HUD Designer:

- **Sections**: Toggle which information panels to show
  - Hero hole cards
  - Community board cards
  - Position indicator
  - Pot odds calculation
  - Hand strength meter
  - GTO advice
  - Opponent statistics

- **Appearance**:
  - Opacity: 0.0 (transparent) to 1.0 (opaque)
  - Font size: Integer value (typically 8-14)
  - Update interval: Seconds between refreshes (0.1-2.0)
  - Theme: `dark` or `light`

- **Window Placement**:
  - X, Y coordinates for window position
  - Width, Height for window dimensions

### Step 2: Select Statistics

Navigate to the **Stats** tab:

1. **Available Stats**: Check which stats to display in the opponent panel
   - `vpip`: Voluntarily Put $ In Pot
   - `pfr`: Pre-Flop Raise
   - `aggression`: Aggression Factor
   - `three_bet`: 3-Bet Percentage
   - `fold_to_three_bet`: Fold to 3-Bet
   - `cbet`: Continuation Bet
   - `fold_to_cbet`: Fold to C-Bet
   - `wt_sd`: Went to Showdown
   - `hands_played`: Sample Size

2. **Custom Stats**: Add new stat names
   - Enter stat name in the text field
   - Click **"Add stat"**
   - The stat will appear in the available list

### Step 3: Configure Color Conditions

Navigate to the **Color Conditions** tab to set up visual alerts:

1. **Select Stat**: Choose which stat to configure
2. **Add Condition**:
   - Operator: `>=`, `>`, `<=`, `<`, `==`
   - Threshold: Numeric value to trigger the condition
   - Color: Hex color code (e.g., `#f97316` for orange)
   - Label: Optional text label (e.g., "Loose", "Nit")

**Example Conditions**:

```python
# VPIP color coding
{
    'vpip': [
        {'operator': '>=', 'threshold': 40, 'color': '#f97316', 'label': 'Loose'},
        {'operator': '<=', 'threshold': 15, 'color': '#22d3ee', 'label': 'Nit'}
    ]
}
```

### Step 4: Configure Popup Stats

Navigate to the **Popup Stats** tab:

1. **Available** list shows all defined stats
2. **Selected** list shows stats displayed in double-click popup
3. Use **Add →** and **← Remove** buttons to manage selection
4. Use **Move Up/Down** to reorder popup display

## Customizing Settings

### Programmatic Configuration

```python
from pokertool.hud_overlay import HUDConfig

config = HUDConfig(
    position=(100, 100),
    size=(400, 300),
    opacity=0.85,
    always_on_top=True,
    show_hole_cards=True,
    show_board_cards=True,
    show_gto_advice=True,
    enabled_stats=['vpip', 'pfr', 'aggression'],
    update_interval=0.5,
    theme='dark',
    font_size=11,
    stat_color_conditions={
        'vpip': [
            {'operator': '>=', 'threshold': 35, 'color': '#ff6b6b', 'label': 'Loose'},
            {'operator': '<=', 'threshold': 18, 'color': '#51cf66', 'label': 'Tight'}
        ]
    },
    popup_stats=['hands_played', 'cbet', 'fold_to_cbet', 'three_bet'],
    profile_name='MyCustomProfile'
)

# Apply configuration
hud = HUDOverlay(config)
hud.start()
```

### Display Scaling

The HUD automatically scales based on display metrics:

```python
# Update display metrics for multi-monitor setups
metrics = {
    'scale_x': 1.5,  # 150% scaling
    'scale_y': 1.5,
    'width': 2560,
    'height': 1440
}

# Apply via game state update
hud.update_game_state({'display_metrics': metrics})
```

## Saving and Loading Profiles

### Saving a Profile

**Via GUI**:
1. Configure your desired settings in the HUD Designer
2. Click **"Apply"** to test the configuration
3. Enter profile name in the **Profiles** tab
4. Click **"Save Profile"** from the main HUD window

**Via API**:

```python
from pokertool.hud_profiles import save_hud_profile

profile_data = config.to_dict()
profile_path = save_hud_profile('TournamentProfile', profile_data)
print(f"Profile saved to: {profile_path}")
```

**Storage Location**: `~/.pokertool/hud_profiles/{profile_name}.json`

### Loading a Profile

**Via GUI**:
1. Select profile from dropdown in the HUD control bar or Profiles tab
2. Profile loads automatically and rebuilds the HUD

**Via API**:

```python
from pokertool.hud_profiles import load_hud_profile, list_hud_profiles

# List available profiles
profiles = list_hud_profiles()
print(f"Available profiles: {profiles}")

# Load specific profile
profile_data = load_hud_profile('TournamentProfile')
if profile_data:
    config = HUDConfig.from_dict(profile_data)
    hud = HUDOverlay(config)
```

### Default Profiles

PokerTool includes several pre-configured profiles:

- **Default**: Balanced display with common stats
- **Minimal**: Clean, essential information only
- **Tournament**: ICM-focused stats and positioning
- **Cash Game**: VPIP, PFR, aggression emphasis
- **Pro**: Comprehensive stat panel with color coding

## Advanced Features

### State Callbacks

Register callbacks for real-time table state changes:

```python
def on_state_change(state):
    """Called whenever game state updates."""
    print(f"New pot size: {state.get('pot')}")
    print(f"Hole cards: {state.get('hole_cards_ocr')}")

hud.register_state_callback(on_state_change)
```

### Dynamic Stat Updates

Update opponent statistics programmatically:

```python
# Update via ML opponent modeling system
from pokertool.ml_opponent_modeling import get_opponent_modeling_system

ml_system = get_opponent_modeling_system()

# Record hand action
ml_system.update_player_profile(
    player_id='seat_1',
    action='raise',
    hand_data={'position': 'BTN', 'bet_size': 50}
)

# HUD will automatically reflect updated stats on next refresh
```

### Custom Themes

Create custom color schemes:

```python
config = HUDConfig(theme='dark')

# Access theme colors in hud._configure_theme()
# Modify or extend with custom themes:
themes = {
    'dark': {
        'bg': '#2b2b2b',
        'fg': '#ffffff',
        'accent': '#4a9eff',
        'warning': '#ff6b6b',
        'success': '#51cf66'
    },
    'custom_pro': {
        'bg': '#1a1a1a',
        'fg': '#e0e0e0',
        'accent': '#00ff88',
        'warning': '#ff4444',
        'success': '#44ff44'
    }
}
```

## Troubleshooting

### HUD Not Appearing

**Check initialization**:
```python
if not hud.initialize():
    print("HUD initialization failed")
    # Check logs for specific error
```

**Common Issues**:
- tkinter not installed: `pip install tk` (some systems)
- Window off-screen: Reset position via config
- Always-on-top disabled: Set `always_on_top=True`

### Stats Not Updating

1. **Verify scraper is running**:
   ```python
   from pokertool.hud_overlay import is_hud_running
   print(f"HUD running: {is_hud_running()}")
   ```

2. **Check update interval**: Increase if too fast
   ```python
   config.update_interval = 1.0  # Update every second
   ```

3. **Verify ML system has data**:
   ```python
   ml_system = get_opponent_modeling_system()
   profile = ml_system.get_player_profile('seat_1')
   print(f"Hands observed: {profile.get('hands_observed', 0)}")
   ```

### Performance Issues

**Reduce update frequency**:
```python
config.update_interval = 1.0  # Default: 0.5
```

**Disable expensive features**:
```python
config.show_gto_advice = False  # GTO calculations can be slow
config.enabled_stats = ['vpip', 'pfr']  # Limit stat display
```

**Use opacity wisely**:
```python
config.opacity = 0.9  # Slightly less transparent = better performance
```

## Best Practices

### Profile Organization

Create profiles for different scenarios:
- **6-Max Cash**: Tailored for 6-handed cash games
- **Full Ring**: 9-handed table optimizations  
- **Tournaments**: ICM-aware stat selection
- **Zoom/Fast**: Minimal display for rapid decisions

### Stat Selection Guidelines

**Essential Stats** (always include):
- `vpip`: Player tightness/looseness
- `pfr`: Aggression preflop
- `hands_played`: Sample size reliability

**Situational Stats**:
- `cbet`: For post-flop play
- `three_bet`: For preflop adjustments
- `wt_sd`: For river decisions

### Color Coding Strategy

Use colors to quickly identify player types:

```python
stat_color_conditions = {
    'vpip': [
        {'operator': '>=', 'threshold': 40, 'color': '#f97316', 'label': 'Loose'},
        {'operator': '<=', 'threshold': 15, 'color': '#22d3ee', 'label': 'Nit'}
    ],
    'aggression': [
        {'operator': '>=', 'threshold': 3.0, 'color': '#ef4444', 'label': 'Aggressive'},
        {'operator': '<', 'threshold': 1.0, 'color': '#facc15', 'label': 'Passive'}
    ]
}
```

## API Reference

### HUDConfig Class

```python
@dataclass
class HUDConfig:
    position: Tuple[int, int] = (100, 100)
    size: Tuple[int, int] = (300, 200)
    opacity: float = 0.8
    always_on_top: bool = True
    show_hole_cards: bool = True
    show_board_cards: bool = True
    show_position: bool = True
    show_pot_odds: bool = True
    show_hand_strength: bool = True
    show_gto_advice: bool = True
    show_opponent_stats: bool = True
    update_interval: float = 0.5
    theme: str = 'dark'
    font_size: int = 10
    available_stats: List[str]
    enabled_stats: List[str]
    stat_color_conditions: Dict[str, List[Dict[str, Any]]]
    popup_stats: List[str]
    popup_enabled: bool = True
    profile_name: str = 'Default'
```

### HUDOverlay Class Methods

- `initialize()`: Create GUI window and widgets
- `start()`: Begin HUD display and update loop
- `stop()`: Shut down HUD cleanly
- `update_game_state(state)`: Update with new table data
- `register_state_callback(callback)`: Subscribe to state changes
- `save_config(filename)`: Persist configuration to file
- `load_config(filename)`: Load configuration from file

### Profile Management Functions

```python
from pokertool.hud_profiles import (
    list_hud_profiles,      # Get list of available profiles
    load_hud_profile,       # Load profile data
    save_hud_profile,       # Save profile to disk
    delete_hud_profile      # Remove profile
)
```

## Integration Examples

### Integration with Screen Scraper

```python
from pokertool.hud_overlay import start_hud_overlay, update_hud_state
from pokertool.modules.poker_screen_scraper_betfair import create_scraper

# Start HUD
hud_config = HUDConfig(profile_name='CashGame')
start_hud_overlay(hud_config)

# Start scraper with HUD updates
scraper = create_scraper()
scraper.start()

# Scraper will automatically call update_hud_state() on each detection
```

### Integration with Manual Input

```python
# Update HUD with manual game state
state = {
    'hole_cards_ocr': ['As', 'Kh'],
    'board_cards_ocr': ['Js', '9d', '2c'],
    'position': 'BTN',
    'pot': 150,
    'to_call': 30,
    'num_players': 6,
    'hole_confidence': 0.95
}

update_hud_state(state)
```

## Configuration Files

### Profile File Structure

Profiles are stored as JSON in `~/.pokertool/hud_profiles/`:

```json
{
  "profile_name": "TournamentPro",
  "position": [100, 100],
  "size": [400, 350],
  "opacity": 0.85,
  "theme": "dark",
  "font_size": 11,
  "update_interval": 0.5,
  "show_hole_cards": true,
  "show_board_cards": true,
  "show_opponent_stats": true,
  "enabled_stats": ["vpip", "pfr", "aggression", "three_bet"],
  "stat_color_conditions": {
    "vpip": [
      {"operator": ">=", "threshold": 40, "color": "#f97316", "label": "Loose"},
      {"operator": "<=", "threshold": 15, "color": "#22d3ee", "label": "Nit"}
    ]
  },
  "popup_stats": ["hands_played", "cbet", "three_bet", "wt_sd"],
  "popup_enabled": true
}
```

### Global HUD Configuration

Main HUD settings stored in `~/.pokertool/hud_config.json`:

```json
{
  "last_profile": "TournamentPro",
  "auto_start": false,
  "remember_position": true
}
```

## Advanced Usage

### Multi-Table HUD

For multi-table play, create separate HUD instances:

```python
from pokertool.hud_overlay import HUDOverlay, HUDConfig

# Create HUD for each table
huds = []
for table_id in range(4):
    config = HUDConfig(
        position=(100 + table_id * 450, 100),
        profile_name=f'Table{table_id+1}'
    )
    hud = HUDOverlay(config)
    hud.start()
    huds.append(hud)

# Update specific table
def update_table_hud(table_id, state):
    huds[table_id].update_game_state(state)
```

### Dynamic Profile Switching

Switch profiles based on game type:

```python
def switch_to_profile(hud, profile_name):
    """Switch HUD to a different profile."""
    from pokertool.hud_profiles import load_hud_profile
    
    profile_data = load_hud_profile(profile_name)
    if profile_data:
        # Merge with current config
        merged = hud.config.to_dict()
        merged.update(profile_data)
        hud.config = HUDConfig.from_dict(merged)
        hud._rebuild_widgets()

# Detect game type and switch
game_type = detect_game_type()  # Your detection logic
if game_type == 'tournament':
    switch_to_profile(hud, 'TournamentPro')
elif game_type == 'cash':
    switch_to_profile(hud, 'CashGame')
```

### Custom Stat Extraction

Extend the HUD to display custom statistics:

```python
# In hud_overlay.py, modify _extract_stat_value()
def _extract_custom_stat(profile, stat_name):
    """Extract custom stat value."""
    if stat_name == 'custom_metric':
        # Calculate your custom metric
        vpip = profile.get('vpip', 0)
        pfr = profile.get('pfr', 0)
        return f"{(vpip - pfr):.1f}", '%'
    
    # Fall back to default extraction
    return hud._extract_stat_value(profile, stat_name)
```

## Testing Your Profile

### Visual Testing

1. Load your profile in the HUD
2. Use sample game states to verify display:

```python
test_states = [
    {
        'hole_cards_ocr': ['As', 'Kh'],
        'board_cards_ocr': [],
        'position': 'BTN',
        'pot': 30,
        'to_call': 10
    },
    {
        'hole_cards_ocr': ['As', 'Kh'],
        'board_cards_ocr': ['Js', '9d', '2c'],
        'position': 'BTN',
        'pot': 150,
        'to_call': 40
    }
]

for state in test_states:
    update_hud_state(state)
    time.sleep(2)  # Observe changes
```

### Automated Testing

See [`tests/test_hud_overlay_integration.py`](../../tests/test_hud_overlay_integration.py:1) for comprehensive integration tests.

## Performance Optimization

### Recommended Settings

**For Single Table**:
- Update interval: 0.3-0.5s
- Enabled stats: 3-5 core stats
- GTO advice: Enabled

**For Multi-Table (4+ tables)**:
- Update interval: 0.8-1.0s
- Enabled stats: 2-3 essential stats only
- GTO advice: Disabled
- Opacity: 0.85+ (less transparency = better performance)

### Memory Management

```python
# Stop HUD when not needed
from pokertool.hud_overlay import stop_hud_overlay

stop_hud_overlay()  # Releases all resources

# Restart when needed
start_hud_overlay(config)
```

## See Also

- [HUD Overlay Source](../../src/pokertool/hud_overlay.py) - Implementation details
- [HUD Designer Source](../../src/pokertool/hud_designer.py) - Designer dialog code
- [HUD Profiles Module](../../src/pokertool/hud_profiles.py) - Profile management
- [Integration Tests](../../tests/test_hud_overlay_integration.py) - Testing examples
- [Installation Guide](../guides/FIRST_RUN_GUIDE.md) - Initial setup
- [Configuration Guide](../CONFIGURATION.md) - System-wide settings

## Support

For issues or questions:
- Check [Troubleshooting Guide](../TROUBLESHOOTING.md)
- Review [GitHub Issues](https://github.com/yourusername/pokertool/issues)
- Contact: support@pokertool.com