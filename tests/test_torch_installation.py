# -*- coding: utf-8 -*-
"""
Test to verify that PyTorch is installed and meets version requirements.
"""

import pytest
from distutils.version import LooseVersion

def test_torch_import_and_version():
    try:
        import torch
    except ImportError:
        pytest.fail("torch is not installed")
    version = torch.__version__
    assert LooseVersion(version) >= LooseVersion("2.0.0"), f"torch version {version} is below required >=2.0.0"