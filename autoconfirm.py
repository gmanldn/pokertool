import os, builtins
if os.getenv('AUTO_CONFIRM','1') == '1':
    builtins.input = lambda *a, **k: 'y'
