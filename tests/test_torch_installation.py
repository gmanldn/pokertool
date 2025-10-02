# -*- coding: utf-8 -*-
"""
Test to verify that PyTorch is installed and meets version requirements.
"""

import pytest
from packaging.version import Version

def test_torch_import_and_version():
    try:
        import torch
    except ImportError:
        pytest.fail("torch is not installed")
    version = torch.__version__
    assert Version(version) >= Version("2.0.0"), f"torch version {version} is below required >=2.0.0"