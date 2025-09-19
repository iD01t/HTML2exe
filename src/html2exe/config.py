"""Configuration management for HTML2exe."""

import sys
from pathlib import Path
from typing import Any, Dict

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class Config:
    """Configuration manager."""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or self._get_default_config_path()
        self._data: Dict[str, Any] = {}
        self.load()

    def _get_default_config_path(self) -> Path:
        """Get default configuration file path."""
        return Path.home() / ".html2exe" / "config.toml"

    def load(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "rb") as f:
                    self._data = tomllib.load(f)
            except Exception:
                self._data = {}
        else:
            self._data = self._get_defaults()

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "window": {
                "width": 1024,
                "height": 768,
                "resizable": True,
            },
            "build": {
                "debug": False,
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        keys = key.split(".")
        value = self._data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value
