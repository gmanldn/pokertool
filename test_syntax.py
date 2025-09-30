#!/usr/bin/env python3
"""Quick syntax test for main poker tool modules."""

import sys
sys.path.insert(0, '.')

def test_imports():
    """Test that all main modules import correctly."""
    print("Testing module imports...")
    print("=" * 60)
    
    modules_to_test = [
        ('src.pokertool.core', 'Core poker logic'),
        ('src.pokertool.gui', 'GUI interface'),
        ('src.pokertool.cli', 'Command-line interface'),
        ('src.pokertool.error_handling', 'Error handling'),
        ('src.pokertool.enhanced_gui', 'Enhanced GUI'),
        ('src.pokertool.api', 'API interface'),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, description in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[''])
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {description:30} ({module_name})")
            print(f"   Version: {version}")
            passed += 1
        except Exception as e:
            print(f"❌ {description:30} ({module_name})")
            print(f"   Error: {str(e)[:100]}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

def test_basic_functionality():
    """Test basic poker functionality."""
    print("\nTesting basic poker functionality...")
    print("=" * 60)
    
    try:
        from src.pokertool.core import parse_card, analyse_hand, Position
        
        # Test 1: Parse cards
        print("Test 1: Parsing cards...")
        card1 = parse_card('As')
        card2 = parse_card('Kh')
        print(f"  ✅ Parsed: {card1}, {card2}")
        
        # Test 2: Analyze hand
        print("\nTest 2: Analyzing hand...")
        hole_cards = [card1, card2]
        result = analyse_hand(
            hole_cards, 
            position=Position.BTN, 
            pot=100.0, 
            to_call=10.0
        )
        print(f"  ✅ Hand strength: {result.strength:.2f}")
        print(f"  ✅ Advice: {result.advice}")
        print(f"  ✅ Details: {result.details}")
        
        print("\n" + "=" * 60)
        print("All functionality tests passed!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n🃏 PokerTool Syntax & Functionality Test\n")
    
    import_success = test_imports()
    func_success = test_basic_functionality()
    
    if import_success and func_success:
        print("\n✅ All tests passed! Your PokerTool installation is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        sys.exit(1)
