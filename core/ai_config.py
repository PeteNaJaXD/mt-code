"""AI configuration management."""

import json
import os
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
AI_CONFIG_FILE = CONFIG_DIR / "ai.json"

DEFAULT_CONFIG = {
    "default_provider": "openai",
    "ai_enabled": True,
    "providers": {
        "openai": {
            "api_key": "",
            "model": "gpt-4o"
        },
        "claude": {
            "api_key": "",
            "model": "claude-sonnet-4-20250514"
        }
    }
}


class AIConfig:
    """Manages AI configuration including API keys."""

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
        if AI_CONFIG_FILE.exists():
            try:
                with open(AI_CONFIG_FILE, 'r') as f:
                    self._config = json.load(f)
                # Merge with defaults for any missing keys
                self._config = self._merge_defaults(self._config)
                logging.info("Loaded AI config from file")
            except Exception as e:
                logging.error(f"Error loading AI config: {e}")
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
            self._save_config()

    def _merge_defaults(self, config: dict) -> dict:
        """Merge loaded config with defaults for missing keys."""
        result = DEFAULT_CONFIG.copy()
        if "default_provider" in config:
            result["default_provider"] = config["default_provider"]
        if "ai_enabled" in config:
            result["ai_enabled"] = config["ai_enabled"]
        if "providers" in config:
            for provider, settings in config["providers"].items():
                if provider in result["providers"]:
                    result["providers"][provider].update(settings)
                else:
                    result["providers"][provider] = settings
        return result

    def _save_config(self):
        """Save config to file."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(AI_CONFIG_FILE, 'w') as f:
                json.dump(self._config, f, indent=2)
            logging.info("Saved AI config to file")
        except Exception as e:
            logging.error(f"Error saving AI config: {e}")

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider. Checks config first, then environment."""
        # Check config file first
        if provider in self._config.get("providers", {}):
            key = self._config["providers"][provider].get("api_key", "")
            if key:
                return key

        # Fall back to environment variables
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "claude": "ANTHROPIC_API_KEY"
        }
        env_var = env_var_map.get(provider)
        if env_var:
            return os.environ.get(env_var)

        return None

    def set_api_key(self, provider: str, api_key: str):
        """Set API key for a provider."""
        if provider not in self._config.get("providers", {}):
            self._config["providers"][provider] = {}
        self._config["providers"][provider]["api_key"] = api_key
        self._save_config()

    def get_model(self, provider: str) -> str:
        """Get model for a provider."""
        default_models = {
            "openai": "gpt-4o",
            "claude": "claude-sonnet-4-20250514"
        }
        if provider in self._config.get("providers", {}):
            return self._config["providers"][provider].get("model", default_models.get(provider, ""))
        return default_models.get(provider, "")

    def set_model(self, provider: str, model: str):
        """Set model for a provider."""
        if provider not in self._config.get("providers", {}):
            self._config["providers"][provider] = {}
        self._config["providers"][provider]["model"] = model
        self._save_config()

    def get_default_provider(self) -> str:
        """Get the default provider."""
        return self._config.get("default_provider", "openai")

    def set_default_provider(self, provider: str):
        """Set the default provider."""
        self._config["default_provider"] = provider
        self._save_config()

    def is_ai_enabled(self) -> bool:
        """Check if AI features are enabled."""
        return self._config.get("ai_enabled", True)

    def set_ai_enabled(self, enabled: bool):
        """Enable or disable AI features."""
        self._config["ai_enabled"] = enabled
        self._save_config()

    def reload(self):
        """Reload config from file."""
        self._load_config()


def get_ai_config() -> AIConfig:
    """Get the singleton AI config instance."""
    return AIConfig()
