"""
Vercel serverless function wrapper for TideWise Flask app
"""
import sys
import os

# Add parent directory to path so we can import from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app
from web_dashboard import app

# Vercel will serve this 'app' object
# No need to run app.run() - Vercel handles that
