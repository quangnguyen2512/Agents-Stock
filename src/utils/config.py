"""
Configuration management for Agents Stock 2.0.
"""
import json
from pathlib import Path
from typing import Dict, Any
from functools import lru_cache

@lru_cache(maxsize=1)
def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to config.json file
        
    Returns:
        Dict containing configuration settings
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load config from {config_path}: {e}")
