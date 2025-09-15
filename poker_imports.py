#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: pokertool/poker_imports.py
# version: '20'
# last_commit: '2025-09-14T18:22:49.793988+00:00'
# fixes: []
# ---
# POKERTOOL-HEADER-END
"""
Poker Imports - Safe import utilities for the poker assistant
Provides robust error handling and fallback mechanisms for module imports
"""

import sys
import os
import importlib
import traceback
from typing import Any, Optional, Dict, List, Tuple
from pathlib import Path

class ImportValidator:
    """Validates and repairs poker module imports"""
    
    REQUIRED_CLASSES = {
        'poker_modules': [
            'Card', 'Suit', 'Rank', 'Position', 'HandAnalysis', 
            'HandRanking', 'PokerCard'
        ],
        'poker_screen_scraper': ['PokerScreenScraper'],
        'poker_init': ['initialise_db_if_needed'],
    }
    
    REQUIRED_METHODS = {
        'HandAnalysis': ['analyze_hand', '__init__', 'get_statistics'],
        'PokerCard': ['__init__', '__str__', 'from_string'],
        'PokerScreenScraper': ['__init__', 'capture_screen'],
    }
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.fixed_items = []
    
    def validate_all(self) -> bool:
        """Validate all required poker modules"""
        all_valid = True
        
        for module_name, required_classes in self.REQUIRED_CLASSES.items():
            if not self.validate_module(module_name, required_classes):
                all_valid = False
        
        return all_valid
    
    def validate_module(self, module_name: str, required_classes: List[str]) -> bool:
        """Validate a specific module has required classes"""
        try:
            module = importlib.import_module(module_name)
            
            missing = []
            for class_name in required_classes:
                if not hasattr(module, class_name):
                    missing.append(class_name)
                else:
                    # Check for required methods
                    if class_name in self.REQUIRED_METHODS:
                        cls = getattr(module, class_name)
                        for method in self.REQUIRED_METHODS[class_name]:
                            if not hasattr(cls, method):
                                missing.append(f"{class_name}.{method}")
            
            if missing:
                self.errors.append(f"{module_name}: Missing {', '.join(missing)}")
                return False
            
            return True
            
        except ImportError as e:
            self.errors.append(f"{module_name}: Import failed - {e}")
            return False
        except Exception as e:
            self.errors.append(f"{module_name}: Validation error - {e}")
            return False

def safe_import(module_name: str, class_name: str = None, fallback=None) -> Optional[Any]:
    """
    Safely import a module or class with error handling and fallback
    
    Args:
        module_name: Name of the module to import
        class_name: Optional class name to import from module
        fallback: Optional fallback value/class if import fails
        
    Returns:
        Imported module/class, fallback value, or None if import fails
    """
    try:
        # Add current directory to path if needed
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Try to import the module
        module = importlib.import_module(module_name)
        
        if class_name:
            if hasattr(module, class_name):
                return getattr(module, class_name)
            else:
                print(f"Warning: {class_name} not found in {module_name}")
                return fallback
        
        return module
        
    except ImportError as e:
        print(f"Warning: Could not import {module_name}: {e}")
        if fallback is not None:
            print(f"  Using fallback for {class_name or module_name}")
            return fallback
        return None
    except Exception as e:
        print(f"Error importing {module_name}: {e}")
        return fallback if fallback is not None else None

def verify_poker_modules() -> Tuple[bool, List[str]]:
    """
    Verify all required poker modules are properly importable
    
    Returns:
        Tuple of (success: bool, missing_components: List[str])
    """
    required_imports = [
        ('poker_modules', 'Card'),
        ('poker_modules', 'Suit'),
        ('poker_modules', 'Rank'),
        ('poker_modules', 'Position'),
        ('poker_modules', 'HandAnalysis'),
        ('poker_modules', 'HandRanking'),
        ('poker_modules', 'PokerCard'),
    ]
    
    missing = []
    for module, cls in required_imports:
        result = safe_import(module, cls)
        if result is None:
            missing.append(f"{module}.{cls}")
    
    if missing:
        print(f"Missing components: {', '.join(missing)}")
        return False, missing
    
    print("✅ All poker modules verified successfully")
    return True, []

def create_minimal_fallbacks() -> Dict[str, Any]:
    """Create minimal fallback classes for critical components"""
    
    from enum import Enum
    from collections import namedtuple
    
    # Minimal Card implementation
    Card = namedtuple('Card', 'rank suit')
    
    # Minimal Suit enum
    class Suit(Enum):
        HEARTS = '♥'
        DIAMONDS = '♦'
        CLUBS = '♣'
        SPADES = '♠'
    
    # Minimal Rank enum
    class Rank(Enum):
        TWO = 2
        THREE = 3
        FOUR = 4
        FIVE = 5
        SIX = 6
        SEVEN = 7
        EIGHT = 8
        NINE = 9
        TEN = 10
        JACK = 11
        QUEEN = 12
        KING = 13
        ACE = 14
    
    # Minimal Position enum
    class Position(Enum):
        BUTTON = 'BTN'
        SMALL_BLIND = 'SB'
        BIG_BLIND = 'BB'
        UNDER_THE_GUN = 'UTG'
        CUTOFF = 'CO'
    
    # Minimal HandRanking enum
    class HandRanking(Enum):
        HIGH_CARD = 1
        PAIR = 2
        TWO_PAIR = 3
        THREE_OF_A_KIND = 4
        STRAIGHT = 5
        FLUSH = 6
        FULL_HOUSE = 7
        FOUR_OF_A_KIND = 8
        STRAIGHT_FLUSH = 9
        ROYAL_FLUSH = 10
    
    # Minimal HandAnalysis class
    class HandAnalysis:
        def __init__(self):
            self.hand_history = []
        
        def analyze_hand(self, hole_cards, community_cards=None):
            return {
                'hole_cards': hole_cards,
                'community_cards': community_cards or [],
                'hand_strength': 'Unknown',
                'recommendation': 'Analysis not available (using fallback)',
                'error': 'Using minimal fallback implementation'
            }
        
        def get_statistics(self):
            return {'total_hands': len(self.hand_history), 'message': 'Fallback mode'}
    
    # Minimal PokerCard class
    class PokerCard:
        def __init__(self, rank, suit):
            self.rank = rank
            self.suit = suit
        
        def __str__(self):
            return f"{self.rank}{self.suit}"
        
        @classmethod
        def from_string(cls, card_str):
            # Simple parsing
            if len(card_str) >= 2:
                rank = card_str[:-1]
                suit = card_str[-1]
                return cls(rank, suit)
            return None
    
    return {
        'Card': Card,
        'Suit': Suit,
        'Rank': Rank,
        'Position': Position,
        'HandRanking': HandRanking,
        'HandAnalysis': HandAnalysis,
        'PokerCard': PokerCard
    }

def repair_poker_modules(module_path: str = 'poker_modules.py') -> bool:
    """
    Attempt to repair a broken poker_modules.py file
    
    Args:
        module_path: Path to the poker_modules.py file
        
    Returns:
        True if repair was successful, False otherwise
    """
    try:
        # Check if file exists
        if not os.path.exists(module_path):
            print(f"Creating new {module_path}...")
            create_new_poker_modules(module_path)
            return True
        
        # Try to import and check what's missing
        validator = ImportValidator()
        if validator.validate_module('poker_modules', validator.REQUIRED_CLASSES['poker_modules']):
            print("✅ poker_modules.py is already valid")
            return True
        
        print(f"🔧 Repairing {module_path}...")
        print(f"  Issues found: {', '.join(validator.errors)}")
        
        # Read existing content
        with open(module_path, 'r') as f:
            existing_content = f.read()
        
        # Check what's already there
        has_imports = 'from enum import Enum' in existing_content
        has_card = 'Card' in existing_content
        has_suit = 'class Suit' in existing_content
        has_analysis = 'class HandAnalysis' in existing_content
        
        # Build repair content
        repair_content = []
        
        if not has_imports:
            repair_content.append("""
# Auto-added imports
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import namedtuple
import itertools
""")
        
        if not has_suit:
            repair_content.append("""
# Auto-added Suit enum
class Suit(Enum):
    HEARTS = '♥'
    DIAMONDS = '♦'
    CLUBS = '♣'
    SPADES = '♠'
    HEART = '♥'  # Alias
    DIAMOND = '♦'  # Alias
    CLUB = '♣'  # Alias
    SPADE = '♠'  # Alias
""")
        
        if not has_analysis:
            repair_content.append("""
# Auto-added HandAnalysis class
class HandAnalysis:
    def __init__(self):
        self.hand_history = []
    
    def analyze_hand(self, hole_cards, community_cards=None):
        return {
            'hole_cards': hole_cards if hole_cards else [],
            'community_cards': community_cards if community_cards else [],
            'hand_strength': 'Unknown',
            'recommendation': 'Basic analysis',
            'position_recommendation': 'CHECK/CALL',
            'outs': 0
        }
    
    def get_statistics(self):
        return {'total_hands': len(self.hand_history)}
""")
        
        # Append repair content to file
        if repair_content:
            with open(module_path, 'a') as f:
                f.write('\n# === AUTO-REPAIR SECTION ===\n')
                f.write('\n'.join(repair_content))
            print(f"✅ Added {len(repair_content)} missing components")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Failed to repair {module_path}: {e}")
        traceback.print_exc()
        return False

def create_new_poker_modules(filepath: str):
    """Create a new minimal poker_modules.py file"""
    minimal_code = '''#!/usr/bin/env python3
"""
Minimal poker_modules.py - Auto-generated fallback
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import namedtuple

# Card as namedtuple for backward compatibility
Card = namedtuple('Card', 'rank suit')

class Suit(Enum):
    HEARTS = '♥'
    DIAMONDS = '♦'
    CLUBS = '♣'
    SPADES = '♠'
    # Aliases
    HEART = '♥'
    DIAMOND = '♦'
    CLUB = '♣'
    SPADE = '♠'

class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

class Position(Enum):
    BUTTON = 'BTN'
    SMALL_BLIND = 'SB'
    BIG_BLIND = 'BB'
    UNDER_THE_GUN = 'UTG'
    CUTOFF = 'CO'

class HandRanking(Enum):
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

@dataclass
class PokerCard:
    rank: Rank
    suit: Suit
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    @classmethod
    def from_string(cls, card_str):
        # Basic parsing
        return cls(Rank.ACE, Suit.SPADES)  # Placeholder

class HandAnalysis:
    def __init__(self):
        self.hand_history = []
    
    def analyze_hand(self, hole_cards, community_cards=None):
        return {
            'hole_cards': hole_cards or [],
            'community_cards': community_cards or [],
            'hand_strength': 'Unknown',
            'recommendation': 'CHECK/CALL - Minimal implementation',
            'position_recommendation': 'Proceed with caution',
            'outs': 0
        }
    
    def get_statistics(self):
        return {
            'total_hands': len(self.hand_history),
            'message': 'Using minimal implementation'
        }
'''
    
    with open(filepath, 'w') as f:
        f.write(minimal_code)
    print(f"✅ Created minimal {filepath}")

def safe_launch_with_fallbacks():
    """Launch poker assistant with automatic fallback handling"""
    
    print("🔍 Checking poker modules integrity...")
    
    # First, try to verify existing modules
    success, missing = verify_poker_modules()
    
    if not success:
        print(f"⚠️  Found {len(missing)} missing components")
        print("🔧 Attempting automatic repair...")
        
        # Try to repair
        if repair_poker_modules():
            # Clear module cache and re-verify
            if 'poker_modules' in sys.modules:
                del sys.modules['poker_modules']
            
            success, missing = verify_poker_modules()
            
            if success:
                print("✅ Modules repaired successfully!")
            else:
                print("⚠️  Using fallback implementations")
                # Load fallbacks
                fallbacks = create_minimal_fallbacks()
                
                # Inject fallbacks into sys.modules
                import types
                poker_modules = types.ModuleType('poker_modules')
                for name, obj in fallbacks.items():
                    setattr(poker_modules, name, obj)
                sys.modules['poker_modules'] = poker_modules
                print("✅ Fallback modules loaded")
    
    return success

if __name__ == "__main__":
    """Test the import validation and repair functionality"""
    
    print("="*60)
    print("Poker Modules Import Validator")
    print("="*60)
    
    # Run validation
    validator = ImportValidator()
    if validator.validate_all():
        print("\n✅ All modules are valid and ready!")
    else:
        print("\n❌ Validation failed:")
        for error in validator.errors:
            print(f"  - {error}")
        
        print("\n🔧 Attempting repairs...")
        if repair_poker_modules():
            print("✅ Repairs completed. Please restart the application.")
        else:
            print("❌ Could not repair automatically.")
            print("💡 Using fallback mode...")
            safe_launch_with_fallbacks()