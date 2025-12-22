"""Python interpreter configuration management."""

import json
import os
import subprocess
from pathlib import Path
from typing import Optional
import logging

from core.paths import LOG_FILE_STR

logging.basicConfig(
    filename=LOG_FILE_STR,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Config file path
CONFIG_DIR = Path(__file__).parent.parent / "config"
PYTHON_CONFIG_FILE = CONFIG_DIR / "python.json"

DEFAULT_CONFIG = {
    "interpreter_path": "",  # Empty means use system default
    "auto_detect_venv": True,
}


class PythonConfig:
    """Manages Python interpreter configuration."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._config = None
        self._load_config()

    def _load_config(self):
        """Load config from file or create default."""
        if PYTHON_CONFIG_FILE.exists():
            try:
                with open(PYTHON_CONFIG_FILE, 'r') as f:
                    self._config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in DEFAULT_CONFIG.items():
                    if key not in self._config:
                        self._config[key] = value
                logging.info("Loaded Python config from file")
            except Exception as e:
                logging.error(f"Error loading Python config: {e}")
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
            self._save_config()

    def _save_config(self):
        """Save config to file."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(PYTHON_CONFIG_FILE, 'w') as f:
                json.dump(self._config, f, indent=2)
            logging.info("Saved Python config to file")
        except Exception as e:
            logging.error(f"Error saving Python config: {e}")

    def get_interpreter_path(self) -> str:
        """Get the configured Python interpreter path."""
        return self._config.get("interpreter_path", "")

    def set_interpreter_path(self, path: str):
        """Set the Python interpreter path."""
        self._config["interpreter_path"] = path
        self._save_config()

    def get_auto_detect_venv(self) -> bool:
        """Check if auto-detect venv is enabled."""
        return self._config.get("auto_detect_venv", True)

    def set_auto_detect_venv(self, enabled: bool):
        """Enable or disable auto-detect venv."""
        self._config["auto_detect_venv"] = enabled
        self._save_config()

    def get_effective_interpreter(self, working_dir: Optional[str] = None) -> str:
        """Get the effective Python interpreter to use.

        Priority:
        1. Configured interpreter path (if set and valid)
        2. Auto-detected venv in working directory (if enabled)
        3. System python3
        """
        # Check configured interpreter
        configured = self.get_interpreter_path()
        if configured and Path(configured).exists():
            return configured

        # Try auto-detecting venv
        if self.get_auto_detect_venv() and working_dir:
            venv_python = self._find_venv_python(working_dir)
            if venv_python:
                return venv_python

        # Fall back to system python3
        return "python3"

    def _find_venv_python(self, working_dir: str) -> Optional[str]:
        """Find Python interpreter in common venv locations."""
        venv_dirs = ["venv", ".venv", "env", ".env"]
        work_path = Path(working_dir)

        for venv_dir in venv_dirs:
            venv_path = work_path / venv_dir
            if venv_path.exists():
                # Check for Unix-style venv
                python_path = venv_path / "bin" / "python"
                if python_path.exists():
                    return str(python_path)
                # Check for Windows-style venv
                python_path = venv_path / "Scripts" / "python.exe"
                if python_path.exists():
                    return str(python_path)

        return None

    def detect_available_interpreters(self, working_dir: Optional[str] = None) -> list[dict]:
        """Detect available Python interpreters.

        Returns list of dicts with 'path', 'version', and 'label' keys.
        """
        interpreters = []

        # Check for venv in working directory
        if working_dir:
            venv_python = self._find_venv_python(working_dir)
            if venv_python:
                version = self._get_python_version(venv_python)
                interpreters.append({
                    "path": venv_python,
                    "version": version,
                    "label": f"venv ({version})" if version else "venv"
                })

        # Check system Python
        for cmd in ["python3", "python"]:
            path = self._which(cmd)
            if path and not any(i["path"] == path for i in interpreters):
                version = self._get_python_version(path)
                interpreters.append({
                    "path": path,
                    "version": version,
                    "label": f"System {cmd} ({version})" if version else f"System {cmd}"
                })

        return interpreters

    def _which(self, cmd: str) -> Optional[str]:
        """Find full path of a command."""
        try:
            result = subprocess.run(
                ["which", cmd],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _get_python_version(self, python_path: str) -> Optional[str]:
        """Get Python version string."""
        try:
            result = subprocess.run(
                [python_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Output is like "Python 3.11.0"
                return result.stdout.strip().replace("Python ", "")
        except Exception:
            pass
        return None

    def reload(self):
        """Reload config from file."""
        self._load_config()


def get_python_config() -> PythonConfig:
    """Get the singleton Python config instance."""
    return PythonConfig()
