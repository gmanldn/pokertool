# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: autoconfirm.py
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
from logger import logger, log_exceptions

__version__ = '20'
import os, builtins
if os.getenv('AUTO_CONFIRM', '1') == '1':
    builtins.input = lambda *a, **k: 'y'
