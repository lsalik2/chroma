import json
import os
from typing import Dict, Optional, Any

# Directory for storing configuration data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
CONFIG_DIR = os.path.join(DATA_DIR, 'config')

# Ensure directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)