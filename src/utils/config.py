# src/utils/config.py

import os
from pathlib import Path
from typing import Dict, Any, Optional
import json
import logging
from dataclasses import dataclass, field, asdict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class APIConfig:
    """Sửa lại để chứa một dictionary các API keys"""
    api_keys: Dict[str, str] = field(default_factory=dict)

@dataclass
class AgentConfig:
    """AI Agent configuration"""
    model_name: str = "gemini-pro"
    max_tokens: int = 2048
    temperature: float = 0.7
    conversation_memory: int = 5

@dataclass
class UIConfig:
    """UI configuration settings"""
    theme: str = "light"
    page_title: str = "Goldenkey AI Analysis"
    page_icon: str = "📈"
    layout: str = "wide"
    sidebar_state: str = "expanded"

@dataclass
class TradingConfig:
    """Trading and market configuration"""
    default_currency: str = "VND"
    market_hours_start: str = "09:00"
    market_hours_end: str = "15:00"
    trading_days: list = None
    max_position_size: float = 0.10
    max_sector_exposure: float = 0.30
    min_cash_reserve: float = 0.15

    def __post_init__(self):
        if self.trading_days is None:
            self.trading_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

@dataclass
class AppConfig:
    """Main application configuration"""
    api: APIConfig
    agents: AgentConfig
    ui: UIConfig
    trading: TradingConfig
    data_dir: str = "data"
    cache_dir: str = "data/cache"
    logs_dir: str = "logs"
    cache_duration: int = 300
    enable_caching: bool = True
    debug_mode: bool = False

class ConfigManager:
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_path()
        self.config = self._load_config()
        
    def _get_default_config_path(self) -> str:
        current_dir = Path(__file__).parent.parent.parent
        return str(current_dir / "config.json")
    
    def _load_config(self) -> AppConfig:
        default_config = {
            "api": {"api_keys": {}},
            "agents": asdict(AgentConfig()),
            "ui": asdict(UIConfig()),
            "trading": asdict(TradingConfig()),
            "data_dir": "data",
            "cache_dir": "data/cache",
            "logs_dir": "logs",
            "cache_duration": 300,
            "enable_caching": True,
            "debug_mode": False
        }
        
        file_config = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
            except Exception as e:
                logging.warning(f"Could not load config file: {e}")
        
        merged_config = self._deep_merge(default_config, file_config)
        
        try:
            return AppConfig(
                api=APIConfig(**merged_config.get("api", {})),
                agents=AgentConfig(**merged_config.get("agents", {})),
                ui=UIConfig(**merged_config.get("ui", {})),
                trading=TradingConfig(**merged_config.get("trading", {})),
                data_dir=merged_config.get("data_dir"),
                cache_dir=merged_config.get("cache_dir"),
                logs_dir=merged_config.get("logs_dir"),
                cache_duration=merged_config.get("cache_duration"),
                enable_caching=merged_config.get("enable_caching"),
                debug_mode=merged_config.get("debug_mode")
            )
        except Exception as e:
            logging.error(f"Error creating config objects: {e}")
            return AppConfig(api=APIConfig(), agents=AgentConfig(), ui=UIConfig(), trading=TradingConfig())

    def _deep_merge(self, dict1: Dict, dict2: Dict) -> Dict:
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

_config_manager = None

def load_config(config_file: Optional[str] = None) -> AppConfig:
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    # --- THAY ĐỔI CHÍNH NẰM Ở ĐÂY ---
    # Thay vì gọi phương thức không tồn tại .get_config()
    # chúng ta truy cập trực tiếp vào thuộc tính .config
    return _config_manager.config


# Enhanced Technical Analysis Settings
ENHANCED_FEATURES = {
    'USE_TALIB': True,
    'VOLUME_ANALYSIS': True,
    'DIVERGENCE_DETECTION': True,
    'PATTERN_RECOGNITION': True,
    'TECHNICAL_SCORING': True,
    'TARGET_CALCULATIONS': True
}

# Technical Score Thresholds
SCORING_THRESHOLDS = {
    'STRONG_BUY': 80,
    'BUY': 70,
    'MODERATE_BUY': 60,
    'HOLD': 45,
    'SELL': 35
}

# ATR Multipliers
ATR_SETTINGS = {
    'TARGET_MULTIPLIER': 2.0,
    'STOPLOSS_MULTIPLIER': 1.5,
    'MIN_RISK_REWARD': 2.0
}