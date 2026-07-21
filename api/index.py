import sys
import os

# Add root directory to sys.path for Vercel module resolution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
