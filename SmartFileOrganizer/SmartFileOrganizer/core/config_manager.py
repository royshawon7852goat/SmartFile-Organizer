"""Configuration Manager for Smart File Organizer.
Handles reading and writing config.json with safe defaults.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config.json"

DEFAULT_CATEGORIES: Dict[str, List[str]] = {
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx", ".csv"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Applications": [".exe", ".msi"],
    "Others": []
}

DEFAULT_CONFIG: Dict[str, Any] = {
    "theme": "dark",  # "dark", "light", "system"
    "accent_color": "blue",
    "default_directory": "",
    "last_directory": "",
    "remember_directory": True,
    "include_hidden": False,
    "recursive": False,
    "ask_before_organize": True,
    "auto_create_folders": True,
    "categories": DEFAULT_CATEGORIES
}

class ConfigManager:
    """Singleton-style or instance-based manager for application settings."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_FILE
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Loads configuration from JSON file or writes defaults if missing or corrupted."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        # Merge with defaults in case new keys were added
                        self.config = {**DEFAULT_CONFIG, **loaded}
                        # Ensure category keys exist
                        categories = self.config.get("categories", {})
                        for cat, exts in DEFAULT_CATEGORIES.items():
                            if cat not in categories:
                                categories[cat] = exts
                        self.config["categories"] = categories
                        logger.info("Configuration loaded successfully from %s", self.config_path)
                        return self.config
            except Exception as e:
                logger.error("Failed to load config from %s: %s. Reverting to defaults.", self.config_path, e)

        self.config = json.loads(json.dumps(DEFAULT_CONFIG))
        self.save_config()
        return self.config

    def save_config(self, new_config: Optional[Dict[str, Any]] = None) -> bool:
        """Saves configuration atomically to JSON file."""
        if new_config:
            self.config = new_config

        try:
            temp_path = self.config_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
            # Atomic replace
            os.replace(temp_path, self.config_path)
            logger.info("Configuration saved successfully to %s", self.config_path)
            return True
        except Exception as e:
            logger.error("Failed to save config to %s: %s", self.config_path, e)
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any, save: bool = True) -> None:
        """Sets a configuration value and optionally persists it."""
        self.config[key] = value
        if save:
            self.save_config()

    def get_category_for_ext(self, ext: str) -> str:
        """Maps a file extension (e.g. '.pdf') to its configured category name."""
        clean_ext = ext.lower().strip()
        if not clean_ext.startswith(".") and clean_ext:
            clean_ext = "." + clean_ext

        categories = self.config.get("categories", DEFAULT_CATEGORIES)
        for cat_name, ext_list in categories.items():
            if cat_name == "Others":
                continue
            # Normalize extension list for comparison
            normalized_list = [e.lower().strip() if e.startswith(".") else f".{e.lower().strip()}" for e in ext_list]
            if clean_ext in normalized_list:
                return cat_name
        return "Others"

    def get_all_categories(self) -> Dict[str, List[str]]:
        """Returns the dictionary of all categories and their extensions."""
        return self.config.get("categories", DEFAULT_CATEGORIES)

    def update_categories(self, categories: Dict[str, List[str]]) -> bool:
        """Updates category mappings."""
        self.config["categories"] = categories
        return self.save_config()

# Global default instance
config_manager = ConfigManager()
