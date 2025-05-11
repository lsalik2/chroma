import os

# Directory for storing tournament data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
TOURNAMENTS_DIR = os.path.join(DATA_DIR, 'tournaments')

# Ensure directories exist
os.makedirs(TOURNAMENTS_DIR, exist_ok=True)