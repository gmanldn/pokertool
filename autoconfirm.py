# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: pokertool/autoconfirm.py
# version: '20'
# last_commit: '2025-09-14T18:22:49.790966+00:00'
# fixes: []
# ---
# POKERTOOL-HEADER-END
import os, builtins
if os.getenv('AUTO_CONFIRM','1') == '1':
    builtins.input = lambda *a, **k: 'y'
