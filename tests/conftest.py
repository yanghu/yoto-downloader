import sys
import os
from unittest.mock import MagicMock

# Add the app directory to the Python path so tests can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

# Mock modules that are not installed on dev machines
sys.modules.setdefault('yt_dlp', MagicMock())
sys.modules.setdefault('requests', MagicMock())

# Prevent ensure_dirs() from trying to create /downloads at import time.
# main.py calls ensure_dirs() at module level; without this the CI runner
# (which has no permission to write to /) raises PermissionError on import.
import config
config.ensure_dirs = lambda: None
