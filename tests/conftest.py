import sys
import os
from unittest.mock import MagicMock, patch

# Add the app directory to the Python path so tests can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

# Mock modules that are not installed on dev machines
sys.modules.setdefault('yt_dlp', MagicMock())
sys.modules.setdefault('requests', MagicMock())

# Patch config module's os.makedirs side-effect before any app module imports it.
# config.py calls os.makedirs at import time, which would fail on dev machines
# that don't have the /downloads directory.
with patch('os.makedirs'):
    import config
