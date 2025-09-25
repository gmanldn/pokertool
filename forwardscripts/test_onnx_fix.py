#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: test_onnx_fix.py
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
"""
Test script to verify ONNX Runtime CoreML error fix.
This script tests the ML components without triggering the CoreML error.
"""

import os
import sys
import traceback

def test_ml_imports():
    """Test importing ML modules without ONNX Runtime conflicts."""
    print("🔍 Testing ML module imports...")
    
    try:
        # Test TensorFlow import
        print("  - Testing TensorFlow import...", end=" ")
        import tensorflow as tf
        print("✅ OK")
        
        # Test scikit-learn import
        print("  - Testing scikit-learn import...", end=" ")
        import sklearn
        print("✅ OK")
        
        # Test pandas import
        print("  - Testing pandas import...", end=" ")
        import pandas as pd
        print("✅ OK")
        
        # Test numpy import
        print("  - Testing numpy import...", end=" ")
        import numpy as np
        print("✅ OK")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        traceback.print_exc()
        return False

def test_pokertool_ml_modules():
    """Test importing pokertool ML modules."""
    print("\n🔍 Testing pokertool ML modules...")
    
    try:
        # Add src to path if not already there
        src_path = os.path.join(os.path.dirname(__file__), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        # Test ML opponent modeling import
        print("  - Testing ML opponent modeling import...", end=" ")
        from pokertool.ml_opponent_modeling import get_opponent_modeling_system
        print("✅ OK")
        
        # Test GTO solver import
        print("  - Testing GTO solver import...", end=" ")
        from pokertool.gto_solver import get_gto_solver
        print("✅ OK")
        
        # Test initializing ML system
        print("  - Testing ML system initialization...", end=" ")
        ml_system = get_opponent_modeling_system()
        print("✅ OK")
        
        # Test getting system stats
        print("  - Testing ML system stats...", end=" ")
        stats = ml_system.get_system_stats()
        print("✅ OK")
        print(f"    ML Libraries available: {stats['ml_libraries_available']}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        traceback.print_exc()
        return False

def test_environment_variables():
    """Test that environment variables are set correctly."""
    print("\n🔍 Testing environment variables...")
    
    expected_vars = {
        'OMP_NUM_THREADS': '1',
        'ONNXRUNTIME_PROVIDERS': 'CPUExecutionProvider'
    }
    
    all_good = True
    for var, expected_value in expected_vars.items():
        actual_value = os.environ.get(var)
        print(f"  - {var}: {actual_value}", end=" ")
        if actual_value == expected_value:
            print("✅ OK")
        else:
            print(f"⚠️  Expected: {expected_value}")
            all_good = False
    
    return all_good

def test_onnx_runtime_not_present():
    """Test that ONNX Runtime is not installed (to avoid conflicts)."""
    print("\n🔍 Testing ONNX Runtime absence...")
    
    try:
        import onnxruntime
        print("  - ONNX Runtime found: ⚠️  This could cause conflicts")
        return False
    except ImportError:
        print("  - ONNX Runtime not found: ✅ Good! No conflicts expected")
        return True

def create_simple_ml_model_test():
    """Create and test a simple ML model to ensure everything works."""
    print("\n🔍 Testing simple ML model creation...")
    
    try:
        import numpy as np
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        
        # Generate sample data
        print("  - Generating sample data...", end=" ")
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        print("✅ OK")
        
        # Split data
        print("  - Splitting data...", end=" ")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        print("✅ OK")
        
        # Create and train model
        print("  - Training RandomForest model...", end=" ")
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)
        print("✅ OK")
        
        # Make predictions
        print("  - Making predictions...", end=" ")
        predictions = model.predict(X_test)
        accuracy = (predictions == y_test).mean()
        print(f"✅ OK (accuracy: {accuracy:.2f})")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 ONNX Runtime CoreML Error Fix - Verification Test")
    print("=" * 60)
    
    tests = [
        ("Basic ML Library Imports", test_ml_imports),
        ("Pokertool ML Modules", test_pokertool_ml_modules),
        ("Environment Variables", test_environment_variables),
        ("ONNX Runtime Absence", test_onnx_runtime_not_present),
        ("Simple ML Model Test", create_simple_ml_model_test)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! ONNX Runtime CoreML error fix is working correctly.")
        print("Your pokertool environment is ready to use without ONNX conflicts.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the output above.")
        return 1

if __name__ == '__main__':
    exit(main())
