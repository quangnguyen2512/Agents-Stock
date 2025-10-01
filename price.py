# price-fixed.py
# Streamlit application for AI-first technical analysis of HOSE stocks.
# Uses PriceAPI for data and TechnicalAnalyst (Gemini) for real AI decision-making.
# Features: Gemini API key config, single-symbol input, display real AI JSON in dashboard format, CSV/JSON export.

import asyncio
import json
import os
import re
import traceback
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Local imports (fallback to same directory if needed)

from src.data.price_api import PriceAPI  # Giả sử bạn có file price_api.py

from src.agents.technical_analyst import MarketContext, TechnicalAnalyst


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

# Hàm lấy API key (ưu tiên: secrets > env > config.json)
def get_api_key() -> Optional[str]:
    if hasattr(st, 'secrets') and 'GEMINI_API_KEY' in st.secrets:
        return st.secrets['GEMINI_API_KEY']
    env_key = os.getenv('GEMINI_API_KEY')
    if env_key:
        return env_key
    try:
        with open('config.json', 'r', encoding='utf-8') as file:
            return json.load(file).get('GEMINI_API_KEY')
    except (FileNotFoundError, json.JSONDecodeError):
        return None

# Đảm bảo event loop cho async
def ensure_event_loop() -> asyncio.AbstractEventLoop:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

# Chạy coroutine async
def run_async(coro) -> Any:
    loop = ensure_event_loop()
    return loop.run_until_complete(coro)

# Format số (an toàn, nếu không phải số thì trả string gốc)
def fmt_number(value: Any, decimals: int = 0, default: str = 'N/A') -> str:
    if value is None or pd.isna(value):
        return default
    try:
        return f"{float(value):,.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)

# ==============================================================================
# PARSE AI RESPONSE FUNCTION - FIX CHO VẤN ĐỀ N/A
# ==============================================================================

def extract_and_parse_ai_json(ai_response) -> Dict[str, Any]:
    """
    Extract và parse JSON từ AI response, xử lý cả trường hợp:
    1. ai_response.content là dict (đã parse)
    2. ai_response.content là dict có field 'raw' chứa markdown string
    3. Fallback parsing từ raw text
    """
    
    # Kiểm tra nếu response không hợp lệ
    if not ai_response or not hasattr(ai_response, 'content'):
        return {}
    
    content = ai_response.content
    
    # Case 1: Content đã là dict và có đầy đủ fields cần thiết
    if isinstance(content, dict):
        # Nếu có field 'raw' thì parse từ raw
        if 'raw' in content:
            raw_text = content['raw']
            return parse_json_from_markdown(raw_text)
        # Nếu đã có các field chính thì return luôn
        elif 'quick_conclusion' in content or 'strategy_recommendation' in content:
            return content
    
    # Case 2: Content là string, cần parse
    if isinstance(content, str):
        return parse_json_from_markdown(content)
    
    return {}

def parse_json_from_markdown(text: str) -> Dict[str, Any]:
    """
    Parse JSON từ markdown text có format ```json...```
    """
    try:
        # Tìm JSON trong markdown blocks
        json_pattern = r'```json\s*\n(.*?)\n```'
        match = re.search(json_pattern, text, re.DOTALL)
        
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        
        # Fallback: thử parse toàn bộ text
        # Loại bỏ markdown formatting nếu có
        cleaned_text = text.replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned_text)
        
    except (json.JSONDecodeError, AttributeError) as e:
        st.error(f"Lỗi parse JSON: {e}")
        st.write("Raw text:", text[:500] + "..." if len(text) > 500 else text)
        return {}

# ==============================================================================
# DASHBOARD DISPLAY FUNCTIONS
# ==============================================================================

def show_colored_action(action: str):
    """Hiển thị Action với màu sắc tương ứng"""
    color_map = {
        'BUY': '#28a745',     # Xanh lá
        'HOLD': '#ffc107',    # Vàng
        'SELL': '#dc3545',    # Đỏ
        'STRONG_BUY': '#155724',  # Xanh đậm
        'STRONG_SELL': '#721c24'  # Đỏ đậm
    }
    color = color_map.get(action, '#6c757d')  # Xám mặc định
    st.markdown(
        f"<div style='text-align: center; padding: 10px; background-color: {color}; "
        f"color: white; border-radius: 8px; font-size: 18px; font-weight: bold;'>{action}</div>",
        unsafe_allow_html=True
    )

def show_confidence_gauge(confidence: float):
    """Hiển thị confidence bằng gauge chart"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = confidence,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Độ tin cậy (%)"},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 85], 'color': "gray"},
                {'range': [85, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

def show_investment_scores(scores: dict):
    """
    Hiển thị investment scores bằng biểu đồ Radar và tính điểm trung bình.
    """
    if not scores:
        st.warning("Không có dữ liệu điểm đầu tư")
        return
    
    labels = list(scores.keys())
    values = [int(s) if isinstance(s, (int, float)) else 0 for s in scores.values()]
    
    # --- 1. Tính và hiển thị điểm trung bình ---
    if values:
        average_score = sum(values) / len(values)
    else:
        average_score = 0
    
    st.metric(label="Điểm trung bình", value=f"{average_score:.1f}/100")

    # --- 2. Tạo biểu đồ Radar ---
    fig = go.Figure()

    # Thêm trace Scatterpolar
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],  # Lặp lại điểm đầu để khép kín biểu đồ
        fill='toself',  # Tô màu cho vùng bên trong
        name='Điểm số'
    ))

    # Cập nhật layout cho biểu đồ
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]  # Đặt thang điểm từ 0 đến 100
            )
        ),
        height=450,
        showlegend=False # Ẩn chú thích (legend)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
def show_price_chart(price_df: pd.DataFrame):
    """Hiển thị biểu đồ giá với candlestick"""

    
    fig = go.Figure()
    
    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=price_df['time'],
        open=price_df['open'],
        high=price_df['high'],
        low=price_df['low'],
        close=price_df['close'],
        name='Price'
    ))
    
    # Volume subplot
    fig.add_trace(go.Bar(
        x=price_df['time'],
        y=price_df['volume'],
        name='Volume',
        yaxis='y2',
        opacity=0.3
    ))
    
    # Layout với 2 y-axis
    fig.update_layout(
        title="Biểu đồ giá và khối lượng",
        yaxis=dict(title="Giá", side="left"),
        yaxis2=dict(title="Khối lượng", side="right", overlaying="y"),
        
        height=500,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_scenarios_table(scenarios: dict):
    """Hiển thị scenarios dạng bảng"""
    if not scenarios:
        st.warning("Không có scenarios")
        return
    
    # Convert nested dict to DataFrame
    scenario_data = []
    for scenario_name, scenario_info in scenarios.items():
        if isinstance(scenario_info, dict):
            scenario_data.append({
                "Scenario": scenario_name.title(),
                "Target Price": scenario_info.get('target_price', 'N/A'),
                "Probability": scenario_info.get('probability', 'N/A'),
                "Key Drivers": ', '.join(scenario_info.get('drivers', [])) if scenario_info.get('drivers') else 'N/A'
            })
        else:
            scenario_data.append({
                "Scenario": scenario_name,
                "Description": str(scenario_info)
            })
    
    if scenario_data:
        df_scenarios = pd.DataFrame(scenario_data)
        st.table(df_scenarios)
    else:
        st.warning("Không có scenarios hợp lệ")

# ==============================================================================
# MAIN DASHBOARD FUNCTION
# ==============================================================================

def render_ai_dashboard(ai_json: dict, price_df: pd.DataFrame = None):
    """
    Render dashboard chính từ AI JSON response
    """
    
    if not ai_json:
        st.error("Không có dữ liệu AI để hiển thị")
        return
    
    
    
    # ====================== ROW 1: OVERVIEW ======================
    st.header("📊 Tổng Quan Phân Tích")
    info_col1, info_col2 = st.columns([65, 35])
    
    with info_col1:
        show_price_chart(price_history.tail(100))
    with info_col2:
        st.subheader("📊 Điểm Đánh Giá Đầu Tư")
        scores = ai_json.get('investment_scores', {})

        show_investment_scores(scores)

    
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Quick Conclusion
        quick_conclusion = ai_json.get('quick_conclusion', 'Chưa có kết luận')
        st.subheader("🎯 Kết luận nhanh")
        st.info(quick_conclusion)
    
    with col2:
        # Action
        strategy = ai_json.get('strategy_recommendation', {})
        action = strategy.get('action', 'N/A') if isinstance(strategy, dict) else 'N/A'
        st.subheader("📈 Hành động")
        show_colored_action(action)
    
    with col3:
        # Confidence - từ investment_scores.reliability_score hoặc data_quality.confidence_level
        confidence = 0
        
        # Thử lấy từ investment_scores
        inv_scores = ai_json.get('investment_scores', {})
        if isinstance(inv_scores, dict):
            confidence = inv_scores.get('reliability_score', 0)
        
        # Fallback: thử từ data_quality
        if not confidence:
            data_qual = ai_json.get('data_quality', {})
            if isinstance(data_qual, dict):
                conf_level = data_qual.get('confidence_level', 'Thấp')
                confidence = {'Cao': 85, 'Trung bình': 65, 'Thấp': 35}.get(conf_level, 0)
        
        try:
            confidence_val = float(confidence)
        except (ValueError, TypeError):
            confidence_val = 0
            
        st.subheader("🎯 Độ tin cậy")
        st.metric("Confidence", f"{confidence_val:.1f}%")
    
    # ====================== ROW 2: KEY POINTS & RISKS ======================
    st.header("📋 Điểm Chính & Rủi Ro")
    vsa = ai_json.get('vsa_seba_analysis')
    st.write(vsa['supply_demand_imbalance'])
    st.write(vsa['effort_background'])

    

    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("✅ Điểm nổi bật")
        # Thử từ key_highlights hoặc key_points
        key_points = vsa['volume_insights']
        
        for point in key_points:
                st.write(f"• {point}")
        
    
    with col_right:
        st.subheader("⚠️ Các lưu ý quan trọng")
        risk_factors = vsa['pattern_potential']
        pa = vsa['pattern_confirmation_conditions']
        for risk in risk_factors:
            st.write(f"• {risk}")
        for pa1 in pa:
            st.write(f"• {pa1}")



    # ====================== ROW 3: STRATEGY DETAILS ======================
    st.header("📑 Chi Tiết Chiến Lược")
    
    with st.container(border=True):
        strategy = ai_json.get('strategy_recommendation', {})
        tech_overview = ai_json.get('tech_overview', {})
        
        if isinstance(strategy, dict):
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.write(f"**Khung thời gian:** {strategy.get('time_horizon', 'N/A')}")
                st.write(f"**Điểm vào:** {strategy.get('entry', 'N/A')}")
                st.write(f"**Stop-loss:** {strategy.get('stop_loss', 'N/A')}")
            
            with col_b:
                st.write(f"**Take-profit:** {strategy.get('take_profit', 'N/A')}")
                for note in tech_overview.get('notes', []):
                    st.write(f" {note}")
             
            
            reasoning = strategy.get('reasoning', '')
            if reasoning:
                st.write("**Lý do:**")
                st.write(reasoning)
        else:
            st.warning("Không có thông tin strategy_recommendation hợp lệ")
    

    
    # ====================== ROW 5: SCENARIOS & ANALYSIS ======================
    st.header("📈 Kịch Bản & Phân Tích Chi Tiết")
    

    scenarios = ai_json.get('scenarios', {})
    show_scenarios_table(scenarios)
    



# ==============================================================================
# DATA LOADING FUNCTIONS
# ==============================================================================

# Cache dữ liệu riêng biệt cho từng phần (tránh recursion error)
@st.cache_data(ttl=300)
def load_price_history(symbol: str) -> pd.DataFrame:
    api = PriceAPI(symbol=symbol, source='VCI')
    return api.get_enhanced_price_history()

@st.cache_data(ttl=300)
def load_comprehensive(symbol: str) -> Dict[str, Any]:
    api = PriceAPI(symbol=symbol, source='VCI')
    return api.get_comprehensive_analysis()

@st.cache_data(ttl=300)
def load_index_history(symbol: str) -> pd.DataFrame:
    api = PriceAPI(symbol=symbol, source='VCI')
    return api.get_index_history()

# Hàm tổng hợp không cache (gọi các hàm cache trên)
def load_core_data(symbol: str) -> Dict[str, Any]:
    try:
        price_history = load_price_history(symbol)
        comprehensive = load_comprehensive(symbol)
        index_history = load_index_history(symbol)

        latest_close = comprehensive.get('technical_summary', {}).get('latest_close')
        if latest_close is None:
            latest_close = float(price_history['close'].iloc[-1]) if not price_history.empty else None

        dq = comprehensive.get('data_quality', {})
        dq_score = float(dq.get('completeness_score', 50.0))

        return {
            'price_history': price_history,
            'comprehensive_analysis': comprehensive,
            'index_history': index_history,
            'latest_close': latest_close,
            'dq_score': dq_score,
        }
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {str(e)}")
        return {}

# ==============================================================================
# MAIN APPLICATION
# ==============================================================================

# Cấu hình trang
st.set_page_config(
    page_title="Golden Key - Technical AI Analysis", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Header
st.title("🔑 Golden Key - Phân Tích Kỹ Thuật AI")
st.markdown("---")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Cấu Hình")
    
    default_key = get_api_key()
    if not default_key:
        st.warning("⚠️ GEMINI_API_KEY not found in secrets/env/config.json.")
    
    api_key = st.text_input("🔑 Gemini API Key", value=default_key or '', type="password")
    model_name = st.text_input("🤖 Model", value="gemini-2.0-flash")
    
    st.markdown("---")
    
    symbol = st.text_input("📊 Mã Cổ Phiếu HOSE", value="ACB").strip().upper()
    
    st.markdown("---")
    
    run_btn = st.button("🚀 Chạy Phân Tích AI", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    # Export options
    st.subheader("📤 Xuất dữ liệu")
    export_json = st.button("📄 Export JSON", use_container_width=True)
    export_csv = st.button("📊 Export CSV", use_container_width=True)

# Main content
if not api_key:
    st.warning("⚠️ Vui lòng nhập Gemini API Key để tiếp tục.")
    st.stop()

if not symbol:
    st.warning("⚠️ Vui lòng nhập mã cổ phiếu.")
    st.stop()

# Load data luôn (để hiển thị thông tin cơ bản)
with st.spinner("🔄 Đang tải dữ liệu..."):
    data = load_core_data(symbol)

# Hiển thị thông tin cơ bản


info_col1, info_col2= st.columns(2)
price_history = data.get('price_history', pd.DataFrame())
total_records = len(price_history)
last_volume = price_history['volume'].iloc[-1]
dq_score = data.get('dq_score', 0)
latest_price = data.get('latest_close')

    


# Chạy AI analysis khi nhấn nút
if run_btn:
    
    # Tạo context và analyst
    context = MarketContext(
        symbol=symbol, 
        current_price=latest_price, 
        market_data={
            'price_history': data['price_history'],
            'comprehensive_analysis': data['comprehensive_analysis'],
            'index_history': data['index_history'],
        }
    )
    
    analyst = TechnicalAnalyst(apikey=api_key, model=model_name)
    
    # Chạy phân tích async
    with st.spinner("🤖 Đang gọi AI để phân tích..."):
            ai_response = run_async(analyst.analyze(context))
            # FIX: Parse response đúng cách
            ai_content = extract_and_parse_ai_json(ai_response)
            
            if ai_content and isinstance(ai_content, dict):
                # Hiển thị dashboard
                render_ai_dashboard(ai_content, data['price_history'])
                
                


# Export functionality
if export_json and 'ai_analysis' in st.session_state:
    analysis_data = {
        'symbol': st.session_state['symbol'],
        'timestamp': str(st.session_state['analysis_timestamp']),
        'analysis': st.session_state['ai_analysis']
    }
    
    json_str = json.dumps(analysis_data, indent=2, ensure_ascii=False)
    
 
