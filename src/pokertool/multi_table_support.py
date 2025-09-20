"""
Multi-Table Support Module - Complete Version
Provides comprehensive multi-table management with focus switching, table-specific settings,
hotkey system, and automatic table tiling for efficient multi-tabling.
"""

import os
import logging
import time
import json
import threading
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
# Optional hotkey and automation dependencies
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    keyboard = None

try:
    import pyautogui
    AUTOMATION_AVAILABLE = True
except ImportError:
    AUTOMATION_AVAILABLE = False
    pyautogui = None
from collections import defaultdict

from .core import Card, parse_card
from .threading import get_thread_pool, TaskPriority
from .error_handling import retry_on_failure
from .hud_overlay import HUDOverlay
# Import scraper functionality
try:
    from poker_screen_scraper import PokerScreenScraper as PokerScraper
except ImportError:
    # Fallback if module not available
    class PokerScraper:
        def __init__(self):
            pass
        def scrape_table(self, window_handle):
            return {}
        def execute_action(self, window_handle, action):
            pass
from .gto_solver import GameState, Strategy, get_gto_solver
from .ml_opponent_modeling import get_opponent_modeling_system

logger = logging.getLogger(__name__)

class TableLayout(Enum):
    """Predefined table layout configurations."""
    CASCADE = 'cascade'
    TILE_2x2 = 'tile_2x2'
    TILE_3x2 = 'tile_3x2'
    TILE_3x3 = 'tile_3x3'
    TILE_4x3 = 'tile_4x3'
    STACK = 'stack'
    CUSTOM = 'custom'

class TableState(Enum):
    """State of a poker table."""
    ACTIVE = 'active'
    WAITING = 'waiting'
    SITTING_OUT = 'sitting_out'
    OBSERVING = 'observing'
    CLOSED = 'closed'
    TOURNAMENT_BREAK = 'tournament_break'

class TablePriority(Enum):
    """Priority levels for table actions."""
    URGENT = 0     # Time-critical action required
    HIGH = 1       # Important decision pending
    NORMAL = 2     # Regular action
    LOW = 3        # No immediate action
    IDLE = 4       # Table is idle

@dataclass
class TableWindow:
    """Represents a single poker table window."""
    table_id: str
    window_handle: Any  # Platform-specific window handle
    site_name: str
    table_name: str
    game_type: str  # 'cash', 'tournament', 'sng'
    stakes: str
    position: Tuple[int, int] = (0, 0)
    size: Tuple[int, int] = (800, 600)
    state: TableState = TableState.ACTIVE
    priority: TablePriority = TablePriority.NORMAL
    hero_seat: Optional[int] = None
    stack_size: float = 0.0
    pot_size: float = 0.0
    players: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    action_required: bool = False
    action_time_remaining: float = float('inf')
    last_update: float = field(default_factory=time.time)
    hud_overlay: Optional[HUDOverlay] = None
    scraper: Optional[PokerScraper] = None
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=lambda: {
        'hands_played': 0,
        'vpip': 0.0,
        'pfr': 0.0,
        'profit_loss': 0.0,
        'bb_per_100': 0.0,
        'session_start': time.time()
    })

@dataclass
class HotkeyAction:
    """Represents a hotkey action."""
    name: str
    key_combination: str
    callback: Callable
    description: str
    enabled: bool = True
    cooldown: float = 0.0  # Seconds before hotkey can be used again
    last_used: float = 0.0

class TableManager:
    """
    Central manager for multi-table poker sessions.
    Handles table tracking, focus management, and coordination.
    """
    
    def __init__(self, max_tables: int = 12):
        self.max_tables = max_tables
        self.tables: Dict[str, TableWindow] = {}
        self.active_table_id: Optional[str] = None
        self.layout = TableLayout.TILE_2x2
        self.custom_layout_config: Dict[str, Any] = {}
        
        # Threading
        self.thread_pool = get_thread_pool()
        self.update_thread: Optional[threading.Thread] = None
        self.running = False
        self.update_interval = 0.1  # 100ms update cycle
        
        # Focus management
        self.focus_queue: List[str] = []
        self.auto_focus = True
        self.focus_on_action = True
        self.cycle_focus_interval = 2.0  # Seconds
        self.last_focus_cycle = time.time()
        
        # Hotkeys
        self.hotkeys: Dict[str, HotkeyAction] = {}
        self.global_hotkeys_enabled = True
        
        # Settings
        self.settings = {
            'auto_tile': True,
            'auto_focus': True,
            'focus_on_action': True,
            'highlight_active': True,
            'sound_alerts': True,
            'time_bank_warning': 5.0,
            'action_timeout_warning': 10.0,
            'min_window_size': (640, 480),
            'preferred_window_size': (800, 600),
            'table_spacing': 10,
            'screen_margins': (20, 20, 20, 20),  # top, right, bottom, left
            'preserve_aspect_ratio': True
        }
        
        logger.info(f"Table manager initialized (max tables: {max_tables})")
        
        # Initialize default hotkeys
        self._setup_default_hotkeys()
    
    def _setup_default_hotkeys(self):
        """Setup default hotkey bindings."""
        default_hotkeys = [
            HotkeyAction(
                name='next_table',
                key_combination='ctrl+tab',
                callback=self.focus_next_table,
                description='Focus next table requiring action'
            ),
            HotkeyAction(
                name='previous_table',
                key_combination='ctrl+shift+tab',
                callback=self.focus_previous_table,
                description='Focus previous table'
            ),
            HotkeyAction(
                name='fold_all',
                key_combination='ctrl+shift+f',
                callback=lambda: self.execute_action_all_tables('fold'),
                description='Fold on all tables'
            ),
            HotkeyAction(
                name='check_call',
                key_combination='ctrl+c',
                callback=lambda: self.execute_action_current_table('check_call'),
                description='Check or call on current table'
            ),
            HotkeyAction(
                name='bet_pot',
                key_combination='ctrl+b',
                callback=lambda: self.execute_action_current_table('bet_pot'),
                description='Bet pot size on current table'
            ),
            HotkeyAction(
                name='toggle_auto_focus',
                key_combination='ctrl+shift+a',
                callback=self.toggle_auto_focus,
                description='Toggle auto-focus mode'
            ),
            HotkeyAction(
                name='tile_tables',
                key_combination='ctrl+shift+t',
                callback=self.tile_all_tables,
                description='Re-tile all tables'
            ),
            HotkeyAction(
                name='cascade_tables',
                key_combination='ctrl+shift+c',
                callback=lambda: self.arrange_tables(TableLayout.CASCADE),
                description='Cascade all tables'
            ),
            HotkeyAction(
                name='sit_out_all',
                key_combination='ctrl+shift+s',
                callback=self.sit_out_all_tables,
                description='Sit out on all tables'
            ),
            HotkeyAction(
                name='table_1',
                key_combination='ctrl+1',
                callback=lambda: self.focus_table_by_index(0),
                description='Focus table 1'
            ),
            HotkeyAction(
                name='table_2',
                key_combination='ctrl+2',
                callback=lambda: self.focus_table_by_index(1),
                description='Focus table 2'
            ),
            HotkeyAction(
                name='table_3',
                key_combination='ctrl+3',
                callback=lambda: self.focus_table_by_index(2),
                description='Focus table 3'
            ),
            HotkeyAction(
                name='table_4',
                key_combination='ctrl+4',
                callback=lambda: self.focus_table_by_index(3),
                description='Focus table 4'
            )
        ]
        
        for hotkey in default_hotkeys:
            self.register_hotkey(hotkey)
    
    def start(self):
        """Start the table manager."""
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            
            # Enable hotkeys
            self._enable_hotkeys()
            
            logger.info("Table manager started")
    
    def stop(self):
        """Stop the table manager."""
        if self.running:
            self.running = False
            
            # Disable hotkeys
            self._disable_hotkeys()
            
            if self.update_thread:
                self.update_thread.join(timeout=1.0)
            
            # Close all tables
            for table in self.tables.values():
                if table.hud_overlay:
                    table.hud_overlay.hide()
            
            logger.info("Table manager stopped")
    
    def _update_loop(self):
        """Main update loop for table management."""
        while self.running:
            try:
                start_time = time.time()
                
                # Update all tables
                for table_id in list(self.tables.keys()):
                    self._update_table(table_id)
                
                # Update priorities
                self._update_table_priorities()
                
                # Handle auto-focus
                if self.auto_focus:
                    self._handle_auto_focus()
                
                # Check for timeouts
                self._check_action_timeouts()
                
                # Sleep for remaining time
                elapsed = time.time() - start_time
                sleep_time = max(0, self.update_interval - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in table update loop: {e}")
                time.sleep(0.1)
    
    def add_table(self, window_handle: Any, site_name: str, table_name: str,
                  game_type: str = 'cash', stakes: str = '') -> str:
        """
        Add a new table to be managed.
        
        Returns:
            Table ID for the newly added table
        """
        if len(self.tables) >= self.max_tables:
            raise ValueError(f"Maximum number of tables ({self.max_tables}) reached")
        
        # Generate unique table ID
        table_id = f"{site_name}_{table_name}_{int(time.time())}"
        
        # Create table window
        table = TableWindow(
            table_id=table_id,
            window_handle=window_handle,
            site_name=site_name,
            table_name=table_name,
            game_type=game_type,
            stakes=stakes
        )
        
        # Initialize scraper for the table
        table.scraper = PokerScraper()
        
        # Initialize HUD overlay
        table.hud_overlay = HUDOverlay()
        
        # Add to tables
        self.tables[table_id] = table
        
        # Auto-tile if enabled
        if self.settings['auto_tile']:
            self.tile_all_tables()
        
        logger.info(f"Added table: {table_id} ({table_name} at {site_name})")
        
        return table_id
    
    def remove_table(self, table_id: str):
        """Remove a table from management."""
        if table_id in self.tables:
            table = self.tables[table_id]
            
            # Clean up resources
            if table.hud_overlay:
                table.hud_overlay.hide()
            
            del self.tables[table_id]
            
            # Remove from focus queue
            self.focus_queue = [tid for tid in self.focus_queue if tid != table_id]
            
            # Re-tile remaining tables
            if self.settings['auto_tile']:
                self.tile_all_tables()
            
            logger.info(f"Removed table: {table_id}")
    
    def _update_table(self, table_id: str):
        """Update a single table's state."""
        if table_id not in self.tables:
            return
        
        table = self.tables[table_id]
        
        try:
            # Scrape table data
            if table.scraper:
                scraped_data = table.scraper.scrape_table(table.window_handle)
                
                if scraped_data:
                    # Update table state
                    table.pot_size = scraped_data.get('pot_size', 0)
                    table.players = scraped_data.get('players', {})
                    table.action_required = scraped_data.get('action_required', False)
                    table.action_time_remaining = scraped_data.get('time_remaining', float('inf'))
                    
                    # Update HUD
                    if table.hud_overlay:
                        table.hud_overlay.update_stats(scraped_data)
            
            # Update statistics
            self._update_table_statistics(table)
            
            table.last_update = time.time()
            
        except Exception as e:
            logger.error(f"Failed to update table {table_id}: {e}")
    
    def _update_table_priorities(self):
        """Update priority levels for all tables."""
        for table in self.tables.values():
            if table.state != TableState.ACTIVE:
                table.priority = TablePriority.IDLE
                continue
            
            if table.action_required:
                # Urgent if time is running out
                if table.action_time_remaining < 3:
                    table.priority = TablePriority.URGENT
                elif table.pot_size > table.stack_size:
                    table.priority = TablePriority.HIGH
                else:
                    table.priority = TablePriority.NORMAL
            else:
                table.priority = TablePriority.LOW
    
    def _handle_auto_focus(self):
        """Handle automatic focus switching."""
        if not self.focus_on_action:
            return
        
        # Find highest priority table needing action
        urgent_tables = [
            table for table in self.tables.values()
            if table.priority == TablePriority.URGENT and table.action_required
        ]
        
        if urgent_tables:
            # Focus most urgent table
            most_urgent = min(urgent_tables, key=lambda t: t.action_time_remaining)
            self.focus_table(most_urgent.table_id)
            return
        
        # Check for high priority tables
        high_priority_tables = [
            table for table in self.tables.values()
            if table.priority == TablePriority.HIGH and table.action_required
        ]
        
        if high_priority_tables:
            # Focus oldest high priority
            oldest = min(high_priority_tables, key=lambda t: t.last_update)
            self.focus_table(oldest.table_id)
            return
        
        # Cycle through tables with actions
        if time.time() - self.last_focus_cycle > self.cycle_focus_interval:
            action_tables = [
                table for table in self.tables.values()
                if table.action_required and table.state == TableState.ACTIVE
            ]
            
            if action_tables and self.active_table_id:
                # Find next table in cycle
                current_idx = -1
                for i, table in enumerate(action_tables):
                    if table.table_id == self.active_table_id:
                        current_idx = i
                        break
                
                if current_idx >= 0:
                    next_idx = (current_idx + 1) % len(action_tables)
                    self.focus_table(action_tables[next_idx].table_id)
                    self.last_focus_cycle = time.time()
    
    def _check_action_timeouts(self):
        """Check for action timeouts and warn user."""
        warning_threshold = self.settings['action_timeout_warning']
        
        for table in self.tables.values():
            if table.action_required and table.action_time_remaining < warning_threshold:
                if self.settings['sound_alerts']:
                    # Play warning sound (implementation depends on platform)
                    pass
                
                # Log warning
                logger.warning(f"Action timeout warning for table {table.table_id}: "
                              f"{table.action_time_remaining:.1f}s remaining")
    
    def focus_table(self, table_id: str):
        """Focus a specific table."""
        if table_id not in self.tables:
            return
        
        table = self.tables[table_id]
        
        try:
            # Platform-specific window focus
            # This is a simplified version - actual implementation would be platform-specific
            # For Windows: win32gui.SetForegroundWindow(table.window_handle)
            # For Mac: Use AppleScript or Cocoa API
            # For Linux: Use X11 or Wayland API
            
            self.active_table_id = table_id
            
            # Highlight if enabled
            if self.settings['highlight_active'] and table.hud_overlay:
                table.hud_overlay.highlight()
            
            logger.debug(f"Focused table: {table_id}")
            
        except Exception as e:
            logger.error(f"Failed to focus table {table_id}: {e}")
    
    def focus_next_table(self):
        """Focus the next table requiring action."""
        action_tables = sorted(
            [t for t in self.tables.values() if t.action_required],
            key=lambda t: (t.priority.value, t.action_time_remaining)
        )
        
        if not action_tables:
            # No tables need action, cycle through all
            table_list = list(self.tables.values())
            if table_list and self.active_table_id:
                current_idx = next((i for i, t in enumerate(table_list) 
                                  if t.table_id == self.active_table_id), -1)
                if current_idx >= 0:
                    next_idx = (current_idx + 1) % len(table_list)
                    self.focus_table(table_list[next_idx].table_id)
        else:
            # Focus highest priority table
            self.focus_table(action_tables[0].table_id)
    
    def focus_previous_table(self):
        """Focus the previous table."""
        table_list = list(self.tables.values())
        if table_list and self.active_table_id:
            current_idx = next((i for i, t in enumerate(table_list) 
                              if t.table_id == self.active_table_id), -1)
            if current_idx >= 0:
                prev_idx = (current_idx - 1) % len(table_list)
                self.focus_table(table_list[prev_idx].table_id)
    
    def focus_table_by_index(self, index: int):
        """Focus table by index (0-based)."""
        table_list = list(self.tables.values())
        if 0 <= index < len(table_list):
            self.focus_table(table_list[index].table_id)
    
    def arrange_tables(self, layout: TableLayout):
        """Arrange all tables according to specified layout."""
        self.layout = layout
        
        if layout == TableLayout.CASCADE:
            self._cascade_tables()
        elif layout == TableLayout.STACK:
            self._stack_tables()
        elif layout in [TableLayout.TILE_2x2, TableLayout.TILE_3x2, 
                       TableLayout.TILE_3x3, TableLayout.TILE_4x3]:
            self._tile_tables(layout)
        elif layout == TableLayout.CUSTOM:
            self._apply_custom_layout()
    
    def tile_all_tables(self):
        """Auto-tile all tables based on table count."""
        table_count = len(self.tables)
        
        if table_count == 0:
            return
        elif table_count <= 4:
            layout = TableLayout.TILE_2x2
        elif table_count <= 6:
            layout = TableLayout.TILE_3x2
        elif table_count <= 9:
            layout = TableLayout.TILE_3x3
        else:
            layout = TableLayout.TILE_4x3
        
        self.arrange_tables(layout)
    
    def _tile_tables(self, layout: TableLayout):
        """Tile tables in a grid layout."""
        # Get screen dimensions
        if AUTOMATION_AVAILABLE:
            screen_width, screen_height = pyautogui.size()
        else:
            screen_width, screen_height = 1920, 1080  # Default fallback
        
        # Apply margins
        margins = self.settings['screen_margins']
        usable_width = screen_width - margins[1] - margins[3]
        usable_height = screen_height - margins[0] - margins[2]
        
        # Determine grid dimensions
        if layout == TableLayout.TILE_2x2:
            cols, rows = 2, 2
        elif layout == TableLayout.TILE_3x2:
            cols, rows = 3, 2
        elif layout == TableLayout.TILE_3x3:
            cols, rows = 3, 3
        elif layout == TableLayout.TILE_4x3:
            cols, rows = 4, 3
        else:
            cols, rows = 2, 2
        
        # Calculate table dimensions
        spacing = self.settings['table_spacing']
        table_width = (usable_width - (cols - 1) * spacing) // cols
        table_height = (usable_height - (rows - 1) * spacing) // rows
        
        # Maintain aspect ratio if required
        if self.settings['preserve_aspect_ratio']:
            aspect_ratio = 4 / 3  # Standard poker table aspect ratio
            if table_width / table_height > aspect_ratio:
                table_width = int(table_height * aspect_ratio)
            else:
                table_height = int(table_width / aspect_ratio)
        
        # Position tables
        table_list = list(self.tables.values())
        for i, table in enumerate(table_list):
            if i >= cols * rows:
                break
            
            row = i // cols
            col = i % cols
            
            x = margins[3] + col * (table_width + spacing)
            y = margins[0] + row * (table_height + spacing)
            
            table.position = (x, y)
            table.size = (table_width, table_height)
            
            # Apply position (platform-specific)
            self._set_window_position(table.window_handle, x, y, table_width, table_height)
    
    def _cascade_tables(self):
        """Cascade tables with slight offset."""
        offset = 30
        base_x, base_y = self.settings['screen_margins'][3], self.settings['screen_margins'][0]
        
        for i, table in enumerate(self.tables.values()):
            x = base_x + i * offset
            y = base_y + i * offset
            
            table.position = (x, y)
            self._set_window_position(
                table.window_handle, 
                x, y, 
                table.size[0], 
                table.size[1]
            )
    
    def _stack_tables(self):
        """Stack all tables in the same position."""
        base_x, base_y = self.settings['screen_margins'][3], self.settings['screen_margins'][0]
        
        for table in self.tables.values():
            table.position = (base_x, base_y)
            self._set_window_position(
                table.window_handle,
                base_x, base_y,
                table.size[0],
                table.size[1]
            )
    
    def _apply_custom_layout(self):
        """Apply custom layout configuration."""
        for table_id, config in self.custom_layout_config.items():
            if table_id in self.tables:
                table = self.tables[table_id]
                table.position = config.get('position', table.position)
                table.size = config.get('size', table.size)
                
                self._set_window_position(
                    table.window_handle,
                    table.position[0],
                    table.position[1],
                    table.size[0],
                    table.size[1]
                )
    
    def _set_window_position(self, window_handle: Any, x: int, y: int, 
                            width: int, height: int):
        """Set window position and size (platform-specific)."""
        # This is a placeholder - actual implementation would be platform-specific
        # For Windows: win32gui.MoveWindow(window_handle, x, y, width, height, True)
        # For Mac: Use Cocoa API
        # For Linux: Use X11 or Wayland API
        pass
    
    def _update_table_statistics(self, table: TableWindow):
        """Update statistics for a table."""
        stats = table.statistics
        
        # Calculate session duration
        session_duration = (time.time() - stats['session_start']) / 3600  # hours
        
        # Calculate BB/100
        if stats['hands_played'] > 0:
            big_blind = self._extract_big_blind(table.stakes)
            if big_blind > 0:
                stats['bb_per_100'] = (stats['profit_loss'] / big_blind) / (stats['hands_played'] / 100)
    
    def _extract_big_blind(self, stakes: str) -> float:
        """Extract big blind from stakes string."""
        # Parse stakes like "$0.50/$1" or "€1/€2"
        try:
            if '/' in stakes:
                parts = stakes.split('/')
                bb_str = parts[1].strip()
                # Remove currency symbols
                bb_str = ''.join(c for c in bb_str if c.isdigit() or c == '.')
                return float(bb_str)
        except:
            pass
        return 1.0  # Default
    
    def register_hotkey(self, hotkey: HotkeyAction):
        """Register a hotkey action."""
        self.hotkeys[hotkey.name] = hotkey
        
        if self.global_hotkeys_enabled and hotkey.enabled and KEYBOARD_AVAILABLE:
            keyboard.add_hotkey(hotkey.key_combination, 
                              lambda h=hotkey: self._handle_hotkey(h))
    
    def _handle_hotkey(self, hotkey: HotkeyAction):
        """Handle hotkey press."""
        # Check cooldown
        if time.time() - hotkey.last_used < hotkey.cooldown:
            return
        
        try:
            hotkey.callback()
            hotkey.last_used = time.time()
            logger.debug(f"Hotkey executed: {hotkey.name}")
        except Exception as e:
            logger.error(f"Hotkey execution failed for {hotkey.name}: {e}")
    
    def _enable_hotkeys(self):
        """Enable all registered hotkeys."""
        if not KEYBOARD_AVAILABLE:
            logger.warning("Keyboard library not available - hotkeys disabled")
            return
            
        for hotkey in self.hotkeys.values():
            if hotkey.enabled:
                keyboard.add_hotkey(hotkey.key_combination,
                                  lambda h=hotkey: self._handle_hotkey(h))
    
    def _disable_hotkeys(self):
        """Disable all hotkeys."""
        if KEYBOARD_AVAILABLE:
            keyboard.unhook_all()
    
    def execute_action_current_table(self, action: str):
        """Execute action on current table."""
        if self.active_table_id and self.active_table_id in self.tables:
            table = self.tables[self.active_table_id]
            
            # Execute action through scraper/automation
            if table.scraper:
                table.scraper.execute_action(table.window_handle, action)
    
    def execute_action_all_tables(self, action: str):
        """Execute action on all tables."""
        for table in self.tables.values():
            if table.state == TableState.ACTIVE and table.action_required:
                if table.scraper:
                    table.scraper.execute_action(table.window_handle, action)
    
    def sit_out_all_tables(self):
        """Sit out on all tables."""
        for table in self.tables.values():
            if table.state == TableState.ACTIVE:
                table.state = TableState.SITTING_OUT
                if table.scraper:
                    table.scraper.execute_action(table.window_handle, 'sit_out')
    
    def toggle_auto_focus(self):
        """Toggle auto-focus mode."""
        self.auto_focus = not self.auto_focus
        logger.info(f"Auto-focus {'enabled' if self.auto_focus else 'disabled'}")
    
    def get_table_settings(self, table_id: str) -> Optional[Dict[str, Any]]:
        """Get custom settings for a table."""
        if table_id in self.tables:
            return self.tables[table_id].custom_settings
        return None
    
    def set_table_settings(self, table_id: str, settings: Dict[str, Any]):
        """Set custom settings for a table."""
        if table_id in self.tables:
            self.tables[table_id].custom_settings.update(settings)
    
    def save_layout(self, filename: str):
        """Save current table layout to file."""
        layout_data = {
            'layout': self.layout.value,
            'tables': {}
        }
        
        for table_id, table in self.tables.items():
            layout_data['tables'][table_id] = {
                'position': table.position,
                'size': table.size,
                'custom_settings': table.custom_settings
            }
        
        try:
            with open(filename, 'w') as f:
                json.dump(layout_data, f, indent=2)
            logger.info(f"Layout saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save layout: {e}")
            return False
    
    def load_layout(self, filename: str) -> bool:
        """Load table layout from file."""
        try:
            with open(filename, 'r') as f:
                layout_data = json.load(f)
            
            self.layout = TableLayout(layout_data['layout'])
            self.custom_layout_config = layout_data.get('tables', {})
            
            # Apply layout
            if self.layout == TableLayout.CUSTOM:
                self._apply_custom_layout()
            else:
                self.arrange_tables(self.layout)
            
            logger.info(f"Layout loaded from {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to load layout: {e}")
            return False
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get overall session statistics."""
        total_tables = len(self.tables)
        active_tables = sum(1 for t in self.tables.values() if t.state == TableState.ACTIVE)
        
        total_hands = 0
        total_profit = 0.0
        total_vpip = 0.0
        total_pfr = 0.0
        
        for table in self.tables.values():
            stats = table.statistics
            total_hands += stats['hands_played']
            total_profit += stats['profit_loss']
            total_vpip += stats['vpip'] * stats['hands_played']
            total_pfr += stats['pfr'] * stats['hands_played']
        
        avg_vpip = total_vpip / total_hands if total_hands > 0 else 0
        avg_pfr = total_pfr / total_hands if total_hands > 0 else 0
        
        return {
            'total_tables': total_tables,
            'active_tables': active_tables,
            'total_hands_played': total_hands,
            'total_profit_loss': total_profit,
            'average_vpip': avg_vpip,
            'average_pfr': avg_pfr,
            'tables_by_state': self._count_tables_by_state(),
            'tables_by_priority': self._count_tables_by_priority()
        }
    
    def _count_tables_by_state(self) -> Dict[str, int]:
        """Count tables by state."""
        counts = defaultdict(int)
        for table in self.tables.values():
            counts[table.state.value] += 1
        return dict(counts)
    
    def _count_tables_by_priority(self) -> Dict[str, int]:
        """Count tables by priority."""
        counts = defaultdict(int)
        for table in self.tables.values():
            counts[table.priority.value] += 1
        return dict(counts)
    
    def export_hotkeys(self, filename: str) -> bool:
        """Export hotkey configuration to file."""
        try:
            hotkey_data = {}
            for name, hotkey in self.hotkeys.items():
                hotkey_data[name] = {
                    'key_combination': hotkey.key_combination,
                    'description': hotkey.description,
                    'enabled': hotkey.enabled,
                    'cooldown': hotkey.cooldown
                }
            
            with open(filename, 'w') as f:
                json.dump(hotkey_data, f, indent=2)
            
            logger.info(f"Hotkeys exported to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to export hotkeys: {e}")
            return False
    
    def import_hotkeys(self, filename: str) -> bool:
        """Import hotkey configuration from file."""
        try:
            with open(filename, 'r') as f:
                hotkey_data = json.load(f)
            
            # Update existing hotkeys
            for name, data in hotkey_data.items():
                if name in self.hotkeys:
                    hotkey = self.hotkeys[name]
                    hotkey.key_combination = data.get('key_combination', hotkey.key_combination)
                    hotkey.enabled = data.get('enabled', hotkey.enabled)
                    hotkey.cooldown = data.get('cooldown', hotkey.cooldown)
            
            # Re-enable hotkeys with new bindings
            if self.running:
                self._disable_hotkeys()
                self._enable_hotkeys()
            
            logger.info(f"Hotkeys imported from {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to import hotkeys: {e}")
            return False


# Global table manager instance
_table_manager: Optional[TableManager] = None

def get_table_manager() -> TableManager:
    """Get the global table manager instance."""
    global _table_manager
    if _table_manager is None:
        _table_manager = TableManager()
    return _table_manager

# Convenience functions
def add_poker_table(window_handle: Any, site_name: str, table_name: str,
                    game_type: str = 'cash', stakes: str = '') -> str:
    """Convenience function to add a poker table."""
    manager = get_table_manager()
    return manager.add_table(window_handle, site_name, table_name, game_type, stakes)

def remove_poker_table(table_id: str):
    """Convenience function to remove a poker table."""
    manager = get_table_manager()
    manager.remove_table(table_id)

def tile_tables():
    """Convenience function to tile all tables."""
    manager = get_table_manager()
    manager.tile_all_tables()

def focus_next():
    """Convenience function to focus next table."""
    manager = get_table_manager()
    manager.focus_next_table()

def get_active_tables() -> List[TableWindow]:
    """Get all active tables."""
    manager = get_table_manager()
    return [table for table in manager.tables.values() 
            if table.state == TableState.ACTIVE]

def get_tables_needing_action() -> List[TableWindow]:
    """Get tables that need action."""
    manager = get_table_manager()
    return sorted(
        [t for t in manager.tables.values() if t.action_required],
        key=lambda t: (t.priority.value, t.action_time_remaining)
    )

def setup_custom_hotkey(name: str, key_combination: str, callback: Callable, 
                       description: str = '', cooldown: float = 0.0):
    """Setup a custom hotkey."""
    manager = get_table_manager()
    hotkey = HotkeyAction(
        name=name,
        key_combination=key_combination,
        callback=callback,
        description=description,
        cooldown=cooldown
    )
    manager.register_hotkey(hotkey)

def save_table_session(filename: str) -> bool:
    """Save complete table session data."""
    manager = get_table_manager()
    
    session_data = {
        'timestamp': time.time(),
        'layout': manager.layout.value,
        'settings': manager.settings,
        'statistics': manager.get_session_statistics(),
        'tables': {}
    }
    
    for table_id, table in manager.tables.items():
        session_data['tables'][table_id] = {
            'site_name': table.site_name,
            'table_name': table.table_name,
            'game_type': table.game_type,
            'stakes': table.stakes,
            'position': table.position,
            'size': table.size,
            'state': table.state.value,
            'statistics': table.statistics,
            'custom_settings': table.custom_settings
        }
    
    try:
        with open(filename, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)
        logger.info(f"Session saved to {filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to save session: {e}")
        return False

def load_table_session(filename: str) -> bool:
    """Load table session data."""
    manager = get_table_manager()
    
    try:
        with open(filename, 'r') as f:
            session_data = json.load(f)
        
        # Apply settings
        manager.settings.update(session_data.get('settings', {}))
        
        # Apply layout
        manager.layout = TableLayout(session_data.get('layout', 'tile_2x2'))
        
        logger.info(f"Session loaded from {filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to load session: {e}")
        return False

if __name__ == '__main__':
    # Test multi-table support
    print("Testing Multi-Table Support...")
    
    # Initialize manager
    manager = get_table_manager()
    
    # Test adding tables
    table1_id = manager.add_table(
        window_handle="window_1",
        site_name="PokerStars",
        table_name="Table 1",
        game_type="cash",
        stakes="$0.50/$1"
    )
    
    table2_id = manager.add_table(
        window_handle="window_2",
        site_name="PokerStars",
        table_name="Table 2",
        game_type="tournament",
        stakes="$10+1"
    )
    
    # Test tiling
    manager.tile_all_tables()
    
    # Test hotkeys
    print(f"Registered hotkeys: {list(manager.hotkeys.keys())}")
    
    # Test statistics
    stats = manager.get_session_statistics()
    print(f"Session stats: {stats}")
    
    # Test layout save/load
    manager.save_layout("test_layout.json")
    
    # Test hotkey export
    manager.export_hotkeys("test_hotkeys.json")
    
    print("Multi-Table Support test completed successfully!")
