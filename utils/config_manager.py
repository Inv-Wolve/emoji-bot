import json
from pathlib import Path
from typing import Any, Dict, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ConfigManager:
    """Manages bot configuration from config.json and per-server settings."""
    
    def __init__(self, config_path: str = "config.json", settings_path: str = "settings.json"):
        self.config_path = Path(config_path)
        self.settings_path = Path(settings_path)
        self.config = self._load_config()
        self.settings = self._load_settings()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load global configuration from config.json."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load per-server settings from settings.json."""
        try:
            if self.settings_path.exists():
                with open(self.settings_path, 'r') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return {}
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "api": {
                "base_url": "https://emoji.gg/api",
                "cache_ttl": 3600,
                "rate_limit_per_user": 10,
                "rate_limit_window": 60
            },
            "emoji_quality": {
                "min_favorites": 0,
                "min_file_size": 100,
                "max_file_size": 256000,
                "excluded_categories": [],
                "adult_filter_enabled": True
            },
            "defaults": {
                "upload_limit": 50,
                "search_limit": 10
            }
        }
    
    def save_settings(self):
        """Save per-server settings to settings.json."""
        try:
            with open(self.settings_path, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., 'api.base_url')."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def get_server_setting(self, server_id: int, key: str, default: Any = None) -> Any:
        """Get a per-server setting."""
        server_settings = self.settings.get(str(server_id), {})
        return server_settings.get(key, default)
    
    def set_server_setting(self, server_id: int, key: str, value: Any):
        """Set a per-server setting."""
        server_id_str = str(server_id)
        if server_id_str not in self.settings:
            self.settings[server_id_str] = {}
        self.settings[server_id_str][key] = value
        self.save_settings()
    
    def can_members_add_emojis(self, server_id: int) -> bool:
        """Check if regular members can add emojis in this server."""
        return self.get_server_setting(server_id, "members_allow", False)
    
    def set_members_allow(self, server_id: int, allow: bool):
        """Set whether regular members can add emojis."""
        self.set_server_setting(server_id, "members_allow", allow)
