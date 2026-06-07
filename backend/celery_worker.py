import os
import sys

# Add the workspace root to sys.path to allow running as script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import create_app
from backend.app.extensions import celery

# Create flask app context for celery tasks
app = create_app()
app.app_context().push()
