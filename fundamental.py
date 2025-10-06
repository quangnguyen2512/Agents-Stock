# fundamental.py
# Streamlit application for AI-first fundamental analysis of HOSE stocks using DuPont method.
# Uses fundamental_api for data and FundamentalAnalyst (Gemini) for real AI decision-making.
# Features: Gemini API key config, single-symbol input, display real AI JSON in dashboard format, CSV/JSON export.
# Updated: Merged all content into a single unified tab for a more professional look.

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

# Local imports (adjust paths if needed)
from src.data.fundamental_api import FundamentalAPI  # Assuming fundamental_api.py is in the same directory
from src.agents.fundamental_analyst import MarketContext, FundamentalAnalyst, AnalysisResponse  # Assuming fundamental_analyst.py is in the same directory

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
# PARSE AI RESPONSE FUNCTION
# ==============================================================================
def extract_and_parse_ai_json(ai_response: AnalysisResponse) -> Dict[str, Any]:
    """Extract và parse JSON từ AI response, xử lý các trường hợp khác nhau."""
    if not ai_response or not hasattr(ai_response, 'content'):
        return {}
    content = ai_response.content
    if isinstance(content, dict):
        if 'raw' in content:
            raw_text = content['raw']
            return parse_json_from_markdown(raw_text)
        if 'quick_conclusion' in content or 'strategy_recommendation' in content:
            return content
    if isinstance(content, str):
        return parse_json_from_markdown(content)
    return {}

def parse_json_from_markdown(text: str) -> Dict[str, Any]:
    """Parse JSON từ markdown text có format ``````"""
    try:
        json_pattern = r'``````'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        cleaned_text = text.replace('``````', '').strip()
        return json.loads(cleaned_text)
    except (json.JSONDecodeError, AttributeError) as e:
        st.error(f"Lỗi parse JSON: {e}")
        st.write("Raw text:", text[:500] + "..." if len(text) > 500 else text)
        return {}

# ==============================================================================
# UNIFIED DISPLAY FUNCTION
# ==============================================================================
def show_unified_analysis(analysis_data: Dict[str, Any], market_data: Dict[str, Any], dupont_components: List[Dict[str, Any]]):
    """Hiển thị toàn bộ phân tích trong một tab duy nhất, chuyên nghiệp."""
    st.header("Phân tích cơ bản chuyên sâu theo phương pháp DuPont")

    # Tóm tắt & khuyến nghị
    st.subheader("Tóm tắt phân tích và Khuyến nghị hành động")
    quick_conclusion = analysis_data.get('quick_conclusion', 'Không có kết luận')
    st.markdown(f"**Kết luận nhanh:** {quick_conclusion}")

    strat = analysis_data.get('strategy_recommendation', {})
    action = strat.get('action', 'N/A')
    st.markdown("**Khuyến nghị hành động:** ")
    color_map = {
        'BUY': '#28a745',  # Xanh lá
        'HOLD': '#ffc107',  # Vàng
        'SELL': '#dc3545',  # Đỏ
        'STRONG_BUY': '#155724',  # Xanh đậm
        'STRONG_SELL': '#721c24'  # Đỏ đậm
    }
    color = color_map.get(action, '#6c757d')  # Xám mặc định
    st.markdown(f"<span style='color:{color}; font-weight:bold'>{action}</span>", unsafe_allow_html=True)

    st.markdown(f"**Lý do:** {strat.get('reasoning', 'N/A')}")
    st.markdown(f"**Thời gian đầu tư:** {strat.get('time_horizon', 'N/A')}")

    scores = analysis_data.get('investment_scores', {})
    st.markdown("**Điểm số đầu tư:**")
    st.markdown(f"- Chất lượng ROE: {fmt_number(scores.get('roe_quality'))}")
    st.markdown(f"- Mức rủi ro: {fmt_number(scores.get('risk_level'))}")
    st.markdown(f"- Tổng điểm: {fmt_number(scores.get('summary_score'))}")

    # Phân tích DuPont chi tiết
    st.subheader("Phân tích DuPont chi tiết")
    dupont = analysis_data.get('dupont_analysis', {})
    st.markdown(f"**Xu hướng lợi nhuận biên:** {dupont.get('profit_margin_trend', 'N/A')}")
    st.markdown(f"**Xu hướng hiệu quả sử dụng tài sản:** {dupont.get('asset_turnover_trend', 'N/A')}")
    st.markdown(f"**Xu hướng đòn bẩy tài chính:** {dupont.get('equity_multiplier_trend', 'N/A')}")
    st.markdown(f"**Tổng thể ROE:** {dupont.get('roe_overall', 'N/A')}")

    st.markdown("**Nhận định chuyên môn:** {analysis_data.get('professional_insight', 'N/A')}")

    # Bảng dữ liệu DuPont
    if dupont_components:
        df = pd.DataFrame(dupont_components)
        st.subheader("Dữ liệu thành phần DuPont")
        st.dataframe(df.style.format({
            'profit_margin': '{:.2f}%',
            'asset_turnover': '{:.2f}',
            'equity_multiplier': '{:.2f}',
            'roe': '{:.2f}%'
        }))

        # Biểu đồ xu hướng ROE
        st.subheader("Biểu đồ xu hướng ROE")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Năm'], y=df['roe'], mode='lines+markers', name='ROE %'))
        fig.update_layout(title='Xu hướng ROE theo thời gian', xaxis_title='Năm', yaxis_title='ROE (%)')
        st.plotly_chart(fig, use_container_width=True)

    # Các kịch bản đầu tư
    st.subheader("Các kịch bản đầu tư")
    scenarios = analysis_data.get('scenarios', {})
    for scen in ['bull', 'neutral', 'bear']:
        sc = scenarios.get(scen, {})
        st.markdown(f"#### Kịch bản {scen.capitalize()}")
        st.markdown(f"- Giá mục tiêu: {fmt_number(sc.get('target_price'), 0)}")
        st.markdown(f"- Xác suất: {fmt_number(sc.get('probability', 0) * 100, 2)}%")
        st.markdown("- Yếu tố thúc đẩy:")
        for d in sc.get('drivers', []):
            st.markdown(f"  - {d}")
        st.markdown(f"- Điều kiện vô hiệu: {sc.get('invalidations', 'N/A')}")

    # Điểm nhấn và rủi ro
    st.subheader("Điểm nhấn và Rủi ro")
    st.markdown("**Điểm nhấn chính:**")
    for point in analysis_data.get('key_highlights', []):
        st.markdown(f"- {point}")
    st.markdown("**Yếu tố rủi ro:**")
    for risk in analysis_data.get('risk_factors', []):
        st.markdown(f"- {risk}")

 

# ==============================================================================
# MAIN APP
# ==============================================================================
def main():
    st.set_page_config(page_title="AI Fundamental Analysis Dashboard", layout="wide")
    st.title("AI Fundamental Analysis Dashboard - Phân tích cơ bản theo DuPont")

    # Sidebar
    with st.sidebar:
        st.header("Cấu hình")
        symbol = st.text_input("Mã cổ phiếu (HOSE)", value="VNM").upper().strip()
        api_key = st.text_input("Gemini API Key", value=get_api_key() or "", type="password")
        if not api_key:
            st.warning("Vui lòng nhập Gemini API Key để tiếp tục.")
            return

        analyze_button = st.button("Phân tích")

    if analyze_button:
        with st.spinner("Đang lấy dữ liệu và phân tích..."):
            try:
                # Khởi tạo API và Analyst
                fundamental_api = FundamentalAPI(symbol)
                analyst = FundamentalAnalyst(api_key=api_key)

                # Lấy dữ liệu thị trường (tương tự MarketContext)
                market_data = {
                    'symbol': symbol,
                    'income_statement': fundamental_api.get_income_statement().to_dict(orient='records'),
                    'balance_sheet': fundamental_api.get_balance_sheet().to_dict(orient='records'),
                    'ratios': fundamental_api.get_ratio().to_dict(orient='records'),
                    # Gọi compact để lấy DuPont (nếu cần, nhưng analyst sẽ xử lý)
                }

                context = MarketContext(symbol=symbol, market_data=market_data)
                ai_response = run_async(analyst.analyze(context))

                # Parse JSON từ response
                analysis_data = extract_and_parse_ai_json(ai_response)

                # Lấy dupont_components từ market_data hoặc analysis
                dupont_components = market_data.get('dupont_components', analysis_data.get('dupont_components', []))

                # Hiển thị thống nhất trong một tab
                show_unified_analysis(analysis_data, market_data, dupont_components)

            except Exception as e:
                st.error(f"Lỗi: {str(e)}")
                st.write(traceback.format_exc())

if __name__ == "__main__":
    main()
