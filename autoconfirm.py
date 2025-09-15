# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: autoconfirm.py
# version: '20'
# last_updated_utc: '2025-09-15T02:05:50.037678+00:00'
# applied_improvements: [Improvement1.py]
# summary: Auto-labeled purpose for autoconfirm.py
# ---
# POKERTOOL-HEADER-END
__version__ = "20"


import os, builtins
if os.getenv('AUTO_CONFIRM','1') == '1':
    builtins.input = lambda *a, **k: 'y'
