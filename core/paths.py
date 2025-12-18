"""Centralized path management for mt-code.

This module provides absolute paths to all resources, allowing the app
to be run from any directory.
"""

from pathlib import Path

# Base directory is where this file's parent's parent is (the project root)
BASE_DIR = Path(__file__).parent.parent.resolve()

# Resource paths
LOG_FILE = BASE_DIR / "editor_view.log"
HIGHLIGHT_DIR = BASE_DIR / "language_highlighting"
CSS_PATH = BASE_DIR / "config" / "app.tcss"

# Convert to strings for compatibility
LOG_FILE_STR = str(LOG_FILE)
HIGHLIGHT_DIR_STR = str(HIGHLIGHT_DIR)
CSS_PATH_STR = str(CSS_PATH)
