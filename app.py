# app.py
# Multi-tab dashboard combining Technical, Fundamental, and PE Analysis

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

# Local imports
from src.data.price_api import PriceAPI
from src.data.fundamental_api import FundamentalAPI
from src.data.pe_api import PEAPI

from src.agents.technical_analyst import MarketContext as TechnicalMarketContext, TechnicalAnalyst
from src.agents.fundamental_analyst import MarketContext as FundamentalMarketContext, FundamentalAnalyst, AnalysisResponse
from src.agents.pe_valuation_analyst import MarketContext as PEMarketContext, PEValuationAnalyst

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

@st.cache_data(ttl=300)
def load_data_from_api(symbol: str) -> Dict[str, Any]:
    """
    Tải tất cả dữ liệu kỹ thuật cần thiết từ PriceAPI.
    """
    try:
        api = PriceAPI(symbol=symbol, source='VCI')
        price_df = api.get_enhanced_price_history()
        comprehensive_analysis = api.get_comprehensive_analysis()
        index_history = api.get_index_history()
        return {
            "price_df": price_df,
            "comprehensive_analysis": comprehensive_analysis,
            "index_history": index_history
        }
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu kỹ thuật cho mã {symbol}: {str(e)}")
        traceback.print_exc()
        return {}

@st.cache_data(ttl=300)
def load_fundamental_data(symbol: str) -> Dict[str, Any]:
    """
    Tải tất cả dữ liệu cơ bản cần thiết từ FundamentalAPI.
    """
    try:
        api = FundamentalAPI(symbol=symbol)
        return {
            'income_statement': api.get_income_statement().to_dict(orient='records'),
            'balance_sheet': api.get_balance_sheet().to_dict(orient='records'),
            'ratios': api.get_ratio().to_dict(orient='records'),
        }
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu cơ bản cho mã {symbol}: {str(e)}")
        return {}

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

def run_async(coro) -> Any:
    loop = ensure_event_loop()
    return loop.run_until_complete(coro)

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

def extract_and_parse_ai_json(ai_response) -> Dict[str, Any]:
    if not ai_response or not hasattr(ai_response, 'content'):
        return {}
    
    content = ai_response.content
    
    if isinstance(content, dict):
        if 'raw' in content:
            raw_text = content['raw']
            return parse_json_from_markdown(raw_text)
        elif 'quick_conclusion' in content or 'strategy_recommendation' in content or 'pe_valuation' in content:
            return content
    
    if isinstance(content, str):
        return parse_json_from_markdown(content)
    
    return {}

def parse_json_from_markdown(text: str) -> Dict[str, Any]:
    try:
        # Improved pattern to find JSON within triple backticks, possibly with 'json' label
        json_pattern = r'```(?:json)?\s*\n(.*?)\n```'
        match = re.search(json_pattern, text, re.DOTALL)
        
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        
        # Fallback for text that is just the JSON string without backticks
        cleaned_text = text.replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned_text)
        
    except (json.JSONDecodeError, AttributeError) as e:
        st.error(f"Lỗi parse JSON: {e}")
        st.write("Raw text:", text[:500] + "..." if len(text) > 500 else text)
        return {}

# ==============================================================================
# DASHBOARD DISPLAY FUNCTIONS (TECHNICAL)
# ==============================================================================

def show_colored_action(action: str):
    color_map = {'BUY': '#28a745', 'HOLD': '#ffc107', 'SELL': '#dc3545', 'STRONG_BUY': '#155724', 'STRONG_SELL': '#721c24'}
    color = color_map.get(action, '#6c757d')
    st.markdown(
        f"<div style='text-align: center; padding: 10px; background-color: {color}; "
        f"color: white; border-radius: 8px; font-size: 18px; font-weight: bold;'>{action}</div>",
        unsafe_allow_html=True
    )

def show_confidence_gauge(confidence: float):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta", value = confidence, domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Độ tin cậy (%)"}, delta = {'reference': 50},
        gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "darkblue"},
                 'steps': [{'range': [0, 50], 'color': "lightgray"}, {'range': [50, 85], 'color': "gray"}, {'range': [85, 100], 'color': "lightgreen"}],
                 'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 90}}))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

def show_investment_scores(scores: dict):
    if not scores:
        st.warning("Không có dữ liệu điểm đầu tư")
        return
    
    labels = list(scores.keys())
    values = [int(s) if isinstance(s, (int, float)) else 0 for s in scores.values()]
    average_score = sum(values) / len(values) if values else 0
    st.metric(label="Điểm trung bình", value=f"{average_score:.1f}/100")
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=labels + [labels[0]], fill='toself', name='Điểm số'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=450, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
def show_price_chart(price_df: pd.DataFrame):
    price_df = price_df.tail(100)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=price_df['time'], open=price_df['open'], high=price_df['high'], low=price_df['low'], close=price_df['close'], name='Price'))
    fig.add_trace(go.Bar(x=price_df['time'], y=price_df['volume'], name='Volume', yaxis='y2', opacity=0.3))
    fig.update_layout(title="Biểu đồ giá và khối lượng", yaxis=dict(title="Giá", side="left"), yaxis2=dict(title="Khối lượng", side="right", overlaying="y"), height=450, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

def show_scenarios_table(scenarios: dict):
    if not scenarios:
        st.warning("Không có scenarios")
        return
    
    scenario_data = []
    for scenario_name, scenario_info in scenarios.items():
        if isinstance(scenario_info, dict):
            scenario_data.append({"Scenario": scenario_name.title(), "Target Price": scenario_info.get('target_price', 'N/A'), "Probability": scenario_info.get('probability', 'N/A'), "Key Drivers": ', '.join(scenario_info.get('drivers', [])) if scenario_info.get('drivers') else 'N/A'})
        else:
            scenario_data.append({"Scenario": scenario_name, "Description": str(scenario_info)})
    
    if scenario_data:
        df_scenarios = pd.DataFrame(scenario_data)
        st.table(df_scenarios)
    else:
        st.warning("Không có scenarios hợp lệ")

# ==============================================================================
# DISPLAY FUNCTION (FUNDAMENTAL)
# ==============================================================================
def show_unified_analysis(analysis_data: Dict[str, Any], dupont_components: List[Dict[str, Any]]):
    """Hiển thị toàn bộ phân tích cơ bản trong một tab duy nhất, chuyên nghiệp."""
    st.header("Phân tích cơ bản chuyên sâu theo phương pháp DuPont")

    # Tóm tắt & khuyến nghị
    st.subheader("Tóm tắt phân tích và Khuyến nghị hành động")
    quick_conclusion = analysis_data.get('quick_conclusion', 'Không có kết luận')
    st.markdown(f"**Kết luận nhanh:** {quick_conclusion}")

    strat = analysis_data.get('strategy_recommendation', {})
    action = strat.get('action', 'N/A')
    st.markdown("**Khuyến nghị hành động:** ")
    color_map = {
        'BUY': '#28a745', 'HOLD': '#ffc107', 'SELL': '#dc3545',
        'STRONG_BUY': '#155724', 'STRONG_SELL': '#721c24'
    }
    color = color_map.get(action, '#6c757d')  # Xám mặc định
    st.markdown(f"<span style='font-size: 1.2em; color:{color}; font-weight:bold'>{action}</span>", unsafe_allow_html=True)

    st.markdown(f"**Lý do:** {strat.get('reasoning', 'N/A')}")
    st.markdown(f"**Thời gian đầu tư:** {strat.get('time_horizon', 'N/A')}")

    scores = analysis_data.get('investment_scores', {})
    st.markdown("**Điểm số đầu tư:**")
    st.markdown(f"- Chất lượng ROE: {fmt_number(scores.get('roe_quality'))}/100")
    st.markdown(f"- Mức rủi ro: {fmt_number(scores.get('risk_level'))}/100")
    st.markdown(f"- Tổng điểm: {fmt_number(scores.get('summary_score'))}/100")

    # Phân tích DuPont chi tiết
    st.subheader("Phân tích DuPont chi tiết")
    dupont = analysis_data.get('dupont_analysis', {})
    st.markdown(f"**Xu hướng lợi nhuận biên:** {dupont.get('profit_margin_trend', 'N/A')}")
    st.markdown(f"**Xu hướng hiệu quả sử dụng tài sản:** {dupont.get('asset_turnover_trend', 'N/A')}")
    st.markdown(f"**Xu hướng đòn bẩy tài chính:** {dupont.get('equity_multiplier_trend', 'N/A')}")
    st.markdown(f"**Tổng thể ROE:** {dupont.get('roe_overall', 'N/A')}")

    st.markdown(f"**Nhận định chuyên môn:** {analysis_data.get('professional_insight', 'N/A')}")

    # Bảng dữ liệu DuPont
    if dupont_components:
        df = pd.DataFrame(dupont_components)
        st.subheader("Dữ liệu thành phần DuPont")
        # Rename columns for display if they exist
        rename_map = {'year': 'Năm', 'profit_margin': 'Biên lợi nhuận (%)', 'asset_turnover': 'Vòng quay tài sản', 'equity_multiplier': 'Đòn bẩy TC', 'roe': 'ROE (%)'}
        df_display = df.rename(columns=rename_map)
        
        # Format columns for display
        st.dataframe(df_display.style.format({
            'Biên lợi nhuận (%)': '{:.2%}',
            'Vòng quay tài sản': '{:.2f}',
            'Đòn bẩy TC': '{:.2f}',
            'ROE (%)': '{:.2%}'
        }), use_container_width=True)


        # Biểu đồ xu hướng ROE
        st.subheader("Biểu đồ xu hướng ROE")
        if 'Năm' in df_display.columns and 'ROE (%)' in df_display.columns:
            fig = px.line(df_display, x='Năm', y='ROE (%)', title='Xu hướng ROE theo thời gian', markers=True)
            fig.update_layout(yaxis_title='ROE (%)', xaxis_title='Năm')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Không đủ dữ liệu ('Năm', 'ROE (%)') để vẽ biểu đồ.")


    # Các kịch bản đầu tư
    st.subheader("Các kịch bản đầu tư")
    scenarios = analysis_data.get('scenarios', {})
    for scen in ['bull', 'neutral', 'bear']:
        sc = scenarios.get(scen, {})
        st.markdown(f"#### Kịch bản {scen.capitalize()}")
        st.markdown(f"- **Giá mục tiêu:** {fmt_number(sc.get('target_price'), 0)}")
        st.markdown(f"- **Xác suất:** {fmt_number(sc.get('probability', 0) * 100, 2)}%")
        st.markdown("- **Yếu tố thúc đẩy:**")
        for d in sc.get('drivers', []):
            st.markdown(f"  - {d}")

    # Điểm nhấn và rủi ro
    st.subheader("Điểm nhấn và Rủi ro")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Điểm nhấn chính:**")
        for point in analysis_data.get('key_highlights', []):
            st.markdown(f"- {point}")
    with col2:
        st.markdown("**Yếu tố rủi ro:**")
        for risk in analysis_data.get('risk_factors', []):
            st.markdown(f"- {risk}")

# ==============================================================================
# DISPLAY FUNCTION (PE VALUATION HELPERS)
# ==============================================================================
def current_close(pe_df: pd.DataFrame) -> float | None:
    try:
        return float(pe_df.iloc[0]["close"])
    except (IndexError, TypeError, KeyError):
        return None

def show_distribution_metrics(stats: dict, pe_df: pd.DataFrame):
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("PE hiện tại", fmt_number(stats.get('current_pe'), 2, "N/A"))
    with c2:
        pct = stats.get("current_percentile")
        pct_str = f"{round(pct,1)}%" if isinstance(pct, (int,float)) else "N/A"
        st.metric("Percentile hiện tại", pct_str)
    with c3:
        st.metric("PE Median (P50)", fmt_number(stats.get('median'), 2, "N/A"))
    with c4:
        cur_px = current_close(pe_df)
        st.metric("Giá hiện tại", fmt_number(cur_px, 0, "N/A"))


# ==============================================================================
# MAIN DASHBOARD FUNCTION (TECHNICAL)
# ==============================================================================

def render_ai_dashboard(ai_json: dict, price_df: pd.DataFrame = None):
    if not ai_json:
        st.error("Không có dữ liệu AI để hiển thị")
        return
    
    st.header("📊 Đánh Giá Đầu Tư")
    sub1, sub2= st.columns([2, 1])
    
    with sub1:
        if price_df is not None and not price_df.empty:
            show_price_chart(price_df)
    
    with sub2:
        scores = ai_json.get('investment_scores', {})
        show_investment_scores(scores)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        quick_conclusion = ai_json.get('quick_conclusion', 'Chưa có kết luận')
        st.subheader("🎯 Kết luận nhanh")
        st.info(quick_conclusion)
    
    with col2:
        strategy = ai_json.get('strategy_recommendation', {})
        action = strategy.get('action', 'N/A') if isinstance(strategy, dict) else 'N/A'
        st.subheader("📈 Hành động")
        show_colored_action(action)
    
    with col3:
        confidence = 0
        inv_scores = ai_json.get('investment_scores', {})
        if isinstance(inv_scores, dict):
            confidence = inv_scores.get('reliability_score', 0)
        
        try:
            confidence_val = float(confidence)
        except (ValueError, TypeError):
            confidence_val = 0
            
        st.subheader("🎯 Độ tin cậy")
        st.metric("Confidence", f"{confidence_val:.1f}%")
    
    st.header("📋 Điểm Chính & Rủi Ro")
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("✅ Điểm nổi bật")
        key_highlights = ai_json.get('key_highlights', [])
        for point in key_highlights:
            st.write(f"• {point}")
    
    with col_right:
        st.subheader("⚠️ Các rủi ro")
        risk_factors = ai_json.get('risk_factors', [])
        for risk in risk_factors:
            st.write(f"• {risk}")

    st.header("📑 Chi Tiết Chiến Lược")
    
    with st.container(border=True):
        strategy = ai_json.get('strategy_recommendation', {})
        if isinstance(strategy, dict):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Khung thời gian:** {strategy.get('time_horizon', 'N/A')}")
                st.write(f"**Điểm vào:** {strategy.get('entry', 'N/A')}")
            with col_b:
                st.write(f"**Stop-loss:** {strategy.get('stop_loss', 'N/A')}")
                st.write(f"**Take-profit:** {strategy.get('take_profit', 'N/A')}")
            reasoning = strategy.get('reasoning', '')
            if reasoning:
                st.write("**Lý do:**")
                st.write(reasoning)
        else:
            st.warning("Không có thông tin strategy_recommendation hợp lệ")
    
    st.header("📈 Kịch Bản & Phân Tích Chi Tiết")
    scenarios = ai_json.get('scenarios', {})
    show_scenarios_table(scenarios)

# ==============================================================================
# MAIN APPLICATION FLOW
# ==============================================================================

def main():
    st.set_page_config(page_title="Multi-Analysis Dashboard", layout="wide")
    st.title("🏢 GOLDEN KEY INVEST")
    
    with st.sidebar:
        st.header("⚙️ Cấu hình")
        code = st.text_input("Vui lòng nhập code từ GOLDEN KEY", value="", type="password")
        with open("config.json", "r") as f:
            cfg = json.load(f)
            api_key = cfg.get(f"{code}", "")

        
        symbol = st.text_input("Mã cổ phiếu", value="HPG").upper().strip()
        run_analysis = st.button("🚀 Chạy phân tích", type="primary", use_container_width=True)

    if not run_analysis:
        st.info("👈 Nhập thông tin trong thanh bên và nhấn 'Chạy phân tích' để bắt đầu.")
        return

    if not code:
        st.error("❌ Vui lòng nhập lại Code")
        return
    if not symbol:
        st.error("❌ Vui lòng nhập mã cổ phiếu")
        return


    with st.spinner(f"AI Agents đang phân tích {symbol}... Vui lòng đợi trong giây lát."):

        try:
            # --- 1. Phân tích kỹ thuật (Technical Analysis) ---
            core_data = load_data_from_api(symbol)
            technical_ai_content = {}
            if core_data and not core_data.get("price_df", pd.DataFrame()).empty:
                price_df = core_data["price_df"]
                latest_price = price_df['close'].iloc[-1]
                tech_context = TechnicalMarketContext(
                    symbol=symbol, current_price=latest_price, market_data=core_data
                )
                technical_analyst = TechnicalAnalyst(apikey=api_key)
                technical_ai_response = run_async(technical_analyst.analyze(tech_context))
                technical_ai_content = extract_and_parse_ai_json(technical_ai_response)

            # --- 2. Phân tích cơ bản (Fundamental Analysis) ---
            fundamental_data = load_fundamental_data(symbol)
            fundamental_ai_content = {}
            if fundamental_data:
                fundamental_context = FundamentalMarketContext(symbol=symbol, market_data=fundamental_data)
                fundamental_analyst = FundamentalAnalyst(api_key=api_key)
                fundamental_ai_response = run_async(fundamental_analyst.analyze(fundamental_context))
                fundamental_ai_content = extract_and_parse_ai_json(fundamental_ai_response)
            
            # --- 3. Phân tích định giá PE (PE Valuation) ---
            pe_df, stats, resp = None, {}, None
            try:
                # Data loading for PE
                pe_api = PEAPI(symbol)
                pe_df = pe_api.compute_pe_trailing()
                stats = pe_api.calculate_pe_distribution_stats(pe_df)
                
                # AI Analysis for PE
                ctx = PEMarketContext(symbol=symbol)
                agent = PEValuationAnalyst(api_key=api_key)
                resp = run_async(agent.analyze(ctx))
            except Exception as pe_error:
                st.warning(f"Lỗi trong quá trình phân tích PE: {pe_error}")


            # --- Render kết quả ra các tab ---
            tab1, tab2, tab3 = st.tabs(["📈 Technical", "📊 Fundamental", "🎯 PE Valuation"])

            with tab1:
                st.header(f"Phân Tích Kỹ Thuật cho {symbol}")
                if technical_ai_content:
                    render_ai_dashboard(technical_ai_content, core_data.get("price_df"))
                else:
                    st.error("Không thể phân tích phản hồi kỹ thuật từ AI. Vui lòng thử lại.")

            with tab2:
                st.header(f"Phân Tích Cơ Bản cho {symbol}")
                if fundamental_ai_content:
                    dupont_components = fundamental_ai_content.get('dupont_components', [])
                    show_unified_analysis(fundamental_ai_content, dupont_components)
                else:
                    st.error("Không thể phân tích phản hồi cơ bản từ AI hoặc không có dữ liệu.")

            with tab3:
                st.header(f"🧠 📊 Phân phối PE {symbol}")
                if resp and stats and pe_df is not None:
                    # Display logic from pe.py, now directly in the tab
                    show_distribution_metrics(stats, pe_df)

                    st.subheader(f"🧠 Kết quả phân tích cho {symbol}")
                    st.write(resp.recommendation)
                    
                    st.subheader("🎯 Định giá theo các kịch bản")
                    if resp.content:
                        data = resp.content
                        if "quick_conclusion" in data:
                            st.info(f"💡 {data['quick_conclusion']}")
                    
                    st.subheader("📈 Kịch bản (AI)")
                    scenarios = resp.content.get("pe_valuation", {}).get("scenarios", {}) if resp.content else {}
                    if scenarios:
                        rows = []
                        for name, sc in scenarios.items():
                            tp_val = sc.get("target_price", "N/A")
                            tp_str = fmt_number(tp_val, 0)
                            prob_val = sc.get("probability", "N/A")
                            prob_str = f"{prob_val:.0%}" if isinstance(prob_val, float) else str(prob_val)

                            rows.append({
                                "Kịch bản": name.title(),
                                "PE Target (AI)": sc.get("pe", "N/A"),
                                "Giá mục tiêu (AI)": tp_str,
                                "Xác suất (AI)": prob_str,
                                "Lý do (rút gọn)": sc.get("rationale","")
                            })
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    else:
                        st.warning("Không có dữ liệu kịch bản từ AI.")
                else:
                    st.error("Không thể thực hiện hoặc hiển thị phân tích định giá PE. Dữ liệu có thể không có sẵn.")

        except Exception as e:
            st.error("Đã xảy ra lỗi không mong muốn trong quá trình phân tích.")
            st.exception(e)

if __name__ == "__main__":
    main()