#!/usr/bin/env python3
"""Test numpy import reliability."""

import sys
import warnings

def test_numpy_import():
    """Test that numpy imports without warnings."""
    print("Testing numpy import...")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Import numpy
        import numpy as np
        
        # Check for warnings
        if w:
            print(f"\n⚠️  WARNING: {len(w)} warning(s) detected during numpy import:")
            for warning in w:
                print(f"  - {warning.category.__name__}: {warning.message}")
                print(f"    File: {warning.filename}:{warning.lineno}")
            return False
        else:
            print("\n✅ SUCCESS: numpy imported cleanly without warnings")
            print(f"   NumPy version: {np.__version__}")
            print(f"   NumPy location: {np.__file__}")
            return True

if __name__ == "__main__":
    success = test_numpy_import()
    sys.exit(0 if success else 1)
