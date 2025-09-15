#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: tests/test_poker.py
# version: '20'
# last_updated_utc: '2025-09-15T02:05:50.037678+00:00'
# applied_improvements: [Improvement1.py]
# summary: Auto-labeled purpose for test_poker.py
# ---
# POKERTOOL-HEADER-END
__version__ = "20"


"""
Test script to verify poker modules are working correctly
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from poker_modules import Card, Suit, Position, analyse_hand, get_hand_tier, to_two_card_str
        print("✅ poker_modules imports successfully")
        return True
    except ImportError as e:
        print(f"❌ poker_modules import failed: {e}")
        return False

def test_card_creation():
    """Test card creation and basic functionality."""
    print("\nTesting card creation...")
    
    try:
        from poker_modules import Card, Suit
        
        # Test card creation
        card1 = Card('A', Suit.SPADES)
        card2 = Card('K', Suit.HEARTS)
        
        print(f"✅ Created cards: {card1}, {card2}")
        return True
    except Exception as e:
        print(f"❌ Card creation failed: {e}")
        return False

def test_hand_analysis():
    """Test hand analysis functionality."""
    print("\nTesting hand analysis...")
    
    try:
        from poker_modules import Card, Suit, analyse_hand, GameState
        
        # Create test hand
        cards = [Card('A', Suit.SPADES), Card('K', Suit.HEARTS)]
        
        # Test analysis
        game_state = GameState()
        result = analyse_hand(cards, [], game_state)
        
        print(f"✅ Hand analysis result: {result.decision}")
        return True
    except Exception as e:
        print(f"❌ Hand analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hand_tier():
    """Test hand tier classification."""
    print("\nTesting hand tier classification...")
    
    try:
        from poker_modules import Card, Suit, get_hand_tier, to_two_card_str
        
        # Test different hands
        test_hands = [
            [Card('A', Suit.SPADES), Card('A', Suit.HEARTS)],  # Pocket Aces
            [Card('K', Suit.SPADES), Card('K', Suit.HEARTS)],  # Pocket Kings
            [Card('A', Suit.SPADES), Card('K', Suit.SPADES)],  # AK suited
            [Card('2', Suit.SPADES), Card('7', Suit.HEARTS)],  # Weak hand
        ]
        
        for hand in test_hands:
            tier = get_hand_tier(hand)
            hand_str = to_two_card_str(hand)
            print(f"✅ {hand_str} -> Tier {tier}")
        
        return True
    except Exception as e:
        print(f"❌ Hand tier test failed: {e}")
        return False

def test_database():
    """Test database functionality."""
    print("\nTesting database...")
    
    try:
        from poker_init import initialise_db_if_needed, open_db
        
        # Initialize database
        initialise_db_if_needed()
        
        # Test connection
        conn = open_db()
        if conn:
            conn.close()
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_gui_imports():
    """Test GUI imports."""
    print("\nTesting GUI imports...")
    
    try:
from poker_gui_enhanced import PokerAssistantGUI
        print("✅ GUI imports successfully")
        return True
    except ImportError as e:
        print(f"❌ GUI import failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("POKER ASSISTANT TEST SUITE")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_card_creation,
        test_hand_analysis,
        test_hand_tier,
        test_database,
        test_gui_imports,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n" + "=" * 50)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 50)
    
    if passed == total:
        print("🎉 All tests passed! The poker assistant should work correctly.")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed. There may be issues with the installation.")
        return False

if __name__ == "__main__":
    main()
