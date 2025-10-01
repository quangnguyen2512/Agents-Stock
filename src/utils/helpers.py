# src/utils/helpers.py - Clean Golden Key Helpers (Fixed Syntax)
import streamlit as st
import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import pandas as pd

logger = logging.getLogger(__name__)


def validate_stock_symbol(symbol: str) -> bool:
    """Validate Vietnamese stock symbol format"""
    if not symbol:
        return False
    
    # Vietnamese stock symbols: 3-4 characters, letters only
    pattern = r'^[A-Z]{3,4}$'
    return bool(re.match(pattern, symbol.upper().strip()))


def format_vnd_amount(amount: float) -> str:
    """Format Vietnamese currency amount"""
    if amount == 0:
        return "0"
    
    if amount >= 1000000000:  # >= 1 billion
        return f"{amount/1000000000:.1f}B"
    elif amount >= 1000000:  # >= 1 million  
        return f"{amount/1000000:.1f}M"
    elif amount >= 1000:     # >= 1 thousand
        return f"{amount/1000:.1f}K"
    else:
        return f"{amount:.0f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage with proper sign"""
    if value == 0:
        return "0.00%"
    
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def format_number(value: float, decimals: int = 2) -> str:
    """Format number with thousand separators"""
    if value == 0:
        return "0"
    
    if decimals == 0:
        return f"{value:,.0f}"
    else:
        return f"{value:,.{decimals}f}"


def get_recommendation_color(recommendation: str) -> str:
    """Get color code for recommendation badges"""
    rec_upper = recommendation.upper()
    
    if any(word in rec_upper for word in ["STRONG BUY", "MUA MẠNH"]):
        return "#28A745"  # Strong Green
    elif any(word in rec_upper for word in ["BUY", "MUA"]):
        return "#28A745"  # Green
    elif any(word in rec_upper for word in ["HOLD", "GIỮ"]):
        return "#FFC107"  # Yellow
    elif any(word in rec_upper for word in ["SELL", "BÁN"]):
        return "#DC3545"  # Red
    elif any(word in rec_upper for word in ["STRONG SELL", "BÁN MẠNH"]):
        return "#DC3545"  # Strong Red
    else:
        return "#6C757D"  # Gray for unknown


def get_confidence_level_text(confidence: int) -> str:
    """Get descriptive text for confidence level"""
    if confidence >= 90:
        return "Rất cao"
    elif confidence >= 75:
        return "Cao"
    elif confidence >= 60:
        return "Trung bình"
    elif confidence >= 40:
        return "Thấp"
    else:
        return "Rất thấp"


def safe_get_from_result(result: Any, key: str, default: Any = None) -> Any:
    """Safely get value from analysis result (handles both dict and dataclass)"""
    if result is None:
        return default
    
    # Try dataclass/object attributes first
    if hasattr(result, key):
        return getattr(result, key)
    
    # Try dictionary access
    if isinstance(result, dict):
        return result.get(key, default)
    
    # Try to access as dict anyway (some objects support dict-like access)
    try:
        return result[key]
    except (KeyError, TypeError, AttributeError):
        return default


def display_api_key_warning() -> bool:
    """Display API key warning if not configured"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        gemini_key = config.get('gemini', '')
        
        if not gemini_key or gemini_key == "YOUR_GEMINI_API_KEY_HERE":
            st.error("""
            🔑 **Cần cấu hình API Key**
            
            Để sử dụng Golden Key AI Analysis Platform, vui lòng:
            
            1. Lấy **Google Gemini API Key** tại: https://makersuite.google.com/app/apikey
            2. Mở file `config.json`
            3. Thay thế `"YOUR_GEMINI_API_KEY_HERE"` bằng API key của bạn
            4. Lưu file và khởi động lại ứng dụng
            
            **Ví dụ config.json:**
            ```json
            {
                "gemini": "AIzaSyC...",
                "database_url": "sqlite:///golden_key.db"
            }
            ```
            """)
            return False
        
        return True
        
    except FileNotFoundError:
        st.error("""
        📋 **Thiếu file cấu hình**
        
        Không tìm thấy file `config.json`. Vui lòng tạo file với nội dung:
        
        ```json
        {
            "gemini": "YOUR_GEMINI_API_KEY_HERE",
            "database_url": "sqlite:///golden_key.db"
        }
        ```
        
        Sau đó thay thế `YOUR_GEMINI_API_KEY_HERE` bằng Google Gemini API Key của bạn.
        """)
        return False
    except json.JSONDecodeError:
        st.error("""
        ❌ **Lỗi cấu hình**
        
        File `config.json` có lỗi định dạng. Vui lòng kiểm tra syntax JSON.
        """)
        return False


def log_analysis_request(symbol: str, analysis_type: str):
    """Log analysis request for monitoring"""
    try:
        logger.info(f"📊 Golden Key Analysis Request: {symbol} - {analysis_type} - {datetime.now()}")
    except Exception as e:
        logger.warning(f"Failed to log analysis request: {e}")


def create_error_message(error: Exception, context: str = "") -> str:
    """Create user-friendly error messages"""
    error_str = str(error).lower()
    
    if "api" in error_str or "key" in error_str:
        return f"Lỗi API Key. Vui lòng kiểm tra cấu hình Google Gemini API."
    elif "network" in error_str or "connection" in error_str:
        return f"Lỗi kết nối mạng. Vui lòng kiểm tra internet và thử lại."
    elif "timeout" in error_str:
        return f"Quá thời gian chờ. Vui lòng thử lại sau."
    elif "permission" in error_str:
        return f"Lỗi quyền truy cập. Vui lòng kiểm tra cấu hình hệ thống."
    else:
        return f"Lỗi {context}: {str(error)}"


def parse_stock_symbols(symbols_text: str) -> List[str]:
    """Parse comma-separated stock symbols"""
    if not symbols_text:
        return []
    
    symbols = []
    for symbol in symbols_text.split(','):
        symbol = symbol.strip().upper()
        if validate_stock_symbol(symbol):
            symbols.append(symbol)
    
    return list(set(symbols))  # Remove duplicates


def reset_analysis_cache():
    """Reset analysis cache in session state"""
    try:
        cache_keys = ['analysis_results', 'current_pe_real', 'current_symbol']
        for key in cache_keys:
            if key in st.session_state:
                if key == 'analysis_results':
                    st.session_state[key] = {}
                else:
                    st.session_state[key] = None
                    
        logger.info("✅ Analysis cache reset successfully")
    except Exception as e:
        logger.warning(f"Failed to reset cache: {e}")


def format_agent_name(agent_type: str) -> str:
    """Format agent type to display name"""
    agent_names = {
        'technical': 'Chuyên gia Kỹ thuật',
        'fundamental': 'Chuyên gia Cơ bản',
        'pe_valuation': 'Chuyên gia Định giá PE',
        'investment_advisor': 'Cố vấn Đầu tư'
    }
    return agent_names.get(agent_type, agent_type.title())


def get_agent_emoji(agent_type: str) -> str:
    """Get emoji for agent type"""
    emojis = {
        'technical': '📈',
        'fundamental': '💰', 
        'pe_valuation': '📊',
        'investment_advisor': '🎯'
    }
    return emojis.get(agent_type, '🤖')


def create_recommendation_badge(recommendation: str) -> str:
    """Create HTML for recommendation badge"""
    color = get_recommendation_color(recommendation)
    return f"""
    <span style="
        background-color: {color};
        color: white;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    ">{recommendation}</span>
    """


def format_currency_vnd(amount: float) -> str:
    """Format amount as Vietnamese currency"""
    if amount == 0:
        return "0 VND"
    
    formatted = format_vnd_amount(amount)
    return f"{formatted} VND"


def calculate_percentage_change(current: float, previous: float) -> float:
    """Calculate percentage change between two values"""
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100


def get_market_status() -> str:
    """Get current market status"""
    now = datetime.now()
    hour = now.hour
    weekday = now.weekday()
    
    # Vietnamese stock market hours: 9:00-11:30, 13:00-14:45, Mon-Fri
    if weekday >= 5:  # Weekend
        return "CLOSED"
    elif (9 <= hour < 11) or (11 == hour and now.minute <= 30) or (13 <= hour < 14) or (14 == hour and now.minute <= 45):
        return "OPEN"
    else:
        return "CLOSED"


def create_professional_alert(message: str, alert_type: str = "info") -> str:
    """Create professional alert HTML"""
    colors = {
        "success": "#28A745",
        "warning": "#FFC107", 
        "danger": "#DC3545",
        "info": "#17A2B8"
    }
    
    icons = {
        "success": "✅",
        "warning": "⚠️",
        "danger": "❌", 
        "info": "ℹ️"
    }
    
    color = colors.get(alert_type, colors["info"])
    icon = icons.get(alert_type, icons["info"])
    
    return f"""
    <div style="
        background: linear-gradient(135deg, {color}20, {color}10);
        border-left: 4px solid {color};
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-family: 'Inter', sans-serif;
    ">
        <strong>{icon} {message}</strong>
    </div>
    """


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"
    
    return filename


def get_vietnamese_month_name(month: int) -> str:
    """Get Vietnamese month name"""
    months = {
        1: "Tháng 1", 2: "Tháng 2", 3: "Tháng 3",
        4: "Tháng 4", 5: "Tháng 5", 6: "Tháng 6",
        7: "Tháng 7", 8: "Tháng 8", 9: "Tháng 9", 
        10: "Tháng 10", 11: "Tháng 11", 12: "Tháng 12"
    }
    return months.get(month, f"Tháng {month}")


def create_progress_html(percentage: float, color: str = "#B8860B") -> str:
    """Create professional progress bar HTML"""
    return f"""
    <div style="
        width: 100%;
        height: 8px;
        background: #E9ECEF;
        border-radius: 4px;
        overflow: hidden;
        margin: 0.5rem 0;
    ">
        <div style="
            width: {percentage}%;
            height: 100%;
            background: linear-gradient(135deg, {color}, {color}CC);
            border-radius: 4px;
            transition: width 0.6s ease-in-out;
        "></div>
    </div>
    """


def validate_pe_value(pe: float) -> bool:
    """Validate PE value is reasonable"""
    return 0 < pe < 1000  # Reasonable PE range


def format_time_vietnamese(dt: datetime) -> str:
    """Format datetime in Vietnamese format"""
    return dt.strftime("%d/%m/%Y %H:%M")


def get_trading_session() -> str:
    """Get current trading session"""
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    current_time = hour * 60 + minute
    
    morning_start = 9 * 60      # 9:00
    morning_end = 11 * 60 + 30  # 11:30
    afternoon_start = 13 * 60   # 13:00
    afternoon_end = 14 * 60 + 45  # 14:45
    
    if morning_start <= current_time <= morning_end:
        return "Phiên sáng"
    elif afternoon_start <= current_time <= afternoon_end:
        return "Phiên chiều"
    else:
        return "Ngoài giờ giao dịch"


def create_metric_card_html(title: str, value: str, change: str = "", 
                           change_positive: bool = True) -> str:
    """Create professional metric card HTML"""
    change_color = "#28A745" if change_positive else "#DC3545"
    change_html = ""
    
    if change:
        change_html = f"""
        <div style="color: {change_color}; font-size: 0.9rem; font-weight: 500; margin-top: 0.25rem;">
            {change}
        </div>
        """
    
    return f"""
    <div style="
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border-left: 4px solid #B8860B;
        margin: 0.5rem 0;
        transition: transform 0.2s ease;
    " onmouseover="this.style.transform='translateY(-2px)'" 
       onmouseout="this.style.transform='translateY(0)'">
        <div style="font-size: 1.8rem; font-weight: 700; color: #B8860B; margin: 0;">
            {value}
        </div>
        <div style="font-size: 0.85rem; color: #6C757D; font-weight: 500; 
                   margin: 0.25rem 0 0 0; text-transform: uppercase; letter-spacing: 0.5px;">
            {title}
        </div>
        {change_html}
    </div>
    """


def extract_pe_real_from_data(data: Dict[str, Any]) -> Optional[float]:
    """Extract PE Real value from analysis data"""
    try:
        # Try different possible locations for PE Real
        if 'pe_valuation' in data:
            pe_val = data['pe_valuation']
            if hasattr(pe_val, 'raw_data') and pe_val.raw_data:
                pe_analysis = pe_val.raw_data.get('pe_analysis', {})
                if 'current_pe' in pe_analysis:
                    return float(pe_analysis['current_pe'])
        
        # Try quick metrics
        if 'quick_metrics' in data:
            pe_real = data['quick_metrics'].get('pe_real')
            if pe_real and validate_pe_value(float(pe_real)):
                return float(pe_real)
        
        return None
    except (ValueError, TypeError, AttributeError):
        return None


def create_loading_spinner_html(text: str = "Đang xử lý...") -> str:
    """Create professional loading spinner HTML"""
    return f"""
    <div style="
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        font-family: 'Inter', sans-serif;
        color: #B8860B;
    ">
        <div style="
            width: 20px;
            height: 20px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #B8860B;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 0.5rem;
        "></div>
        <span style="font-weight: 500;">{text}</span>
    </div>
    
    <style>
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """


def is_market_open() -> bool:
    """Check if Vietnamese stock market is currently open"""
    return get_market_status() == "OPEN"


def get_next_trading_day() -> str:
    """Get next trading day information"""
    now = datetime.now()
    weekday = now.weekday()
    
    if weekday == 4:  # Friday
        return "Thứ Hai tuần sau"
    elif weekday == 5:  # Saturday  
        return "Thứ Hai"
    elif weekday == 6:  # Sunday
        return "Ngày mai"
    else:
        return "Ngày mai"


def create_simple_metric_html(title: str, value: str, subtitle: str = "") -> str:
    """Create simple metric display"""
    subtitle_html = f'<p style="font-size: 0.8rem; color: #666; margin: 0.25rem 0 0 0;">{subtitle}</p>' if subtitle else ""
    
    return f"""
    <div style="
        text-align: center;
        padding: 1rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    ">
        <h3 style="color: #B8860B; margin: 0; font-size: 1.5rem;">{value}</h3>
        <p style="margin: 0.25rem 0 0 0; font-size: 0.9rem; color: #333; font-weight: 500;">{title}</p>
        {subtitle_html}
    </div>
    """