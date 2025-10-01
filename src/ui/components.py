# src/ui/components.py - FIXED Components with Proper Consensus Handling
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import numpy as np

from ..utils.helpers import (
    format_vnd_amount, format_percentage, format_number,
    get_recommendation_color, get_confidence_level_text
)


def render_header():
    """Render main dashboard header"""
    st.markdown("""
    <div class="main-header fade-in">
        <h1>🤖 AI Agent Trading Vietnam</h1>
        <p>Hệ thống 4 AI Chuyên gia - Phân tích đa chiều cổ phiếu Việt Nam</p>
    </div>
    """, unsafe_allow_html=True)


def render_stock_input() -> str:
    """Render stock input section and return selected symbol"""
    st.markdown("### 📊 Nhập mã cổ phiếu")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        symbol = st.text_input(
            "Mã cổ phiếu",
            placeholder="VCB, VIC, FPT...",
            help="Nhập mã cổ phiếu Việt Nam (VD: VCB, VIC, FPT)"
        ).upper().strip()
    
    with col2:
        analysis_type = st.selectbox(
            "Loại phân tích",
            ["Toàn diện", "Nhanh", "Technical", "Fundamental", "PE Valuation"],
            help="Chọn loại phân tích muốn thực hiện"
        )
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_button = st.button("🔍 Phân tích", type="primary", use_container_width=True)
    
    # Store in session state
    if analyze_button and symbol:
        st.session_state.selected_symbol = symbol
        st.session_state.analysis_type = analysis_type
        st.session_state.should_analyze = True
    
    return symbol if analyze_button and symbol else ""


def render_quick_overview(overview_data: Dict[str, Any]):
    """Render quick overview section"""
    if not overview_data or overview_data.get('status') != 'success':
        st.warning("⚠️ Không thể lấy dữ liệu tổng quan")
        return
    
    st.markdown("### ⚡ Tổng quan nhanh")
    
    metrics = overview_data.get('quick_metrics', {})
    data_sources = overview_data.get('data_sources', {})
    
    # Main metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        price = metrics.get('current_price', 0)
        change = metrics.get('change_1d', 0)
        delta_color = "normal" if change == 0 else "inverse" if change < 0 else "normal"
        st.metric(
            "Giá hiện tại",
            f"{format_vnd_amount(price)} VND",
            f"{change:+.2f}%" if change != 0 else None,
            delta_color=delta_color
        )
    
    with col2:
        volume = metrics.get('volume', 0)
        st.metric("Volume", format_number(volume, 0))
    
    with col3:
        pe = metrics.get('pe', 0)
        pe_real = metrics.get('pe_real', 0)
        st.metric(
            "P/E",
            f"{pe:.1f}x" if pe > 0 else "N/A",
            f"Real: {pe_real:.1f}x" if pe_real > 0 else None
        )
    
    with col4:
        rsi = metrics.get('rsi', 50)
        rsi_status = "Quá mua" if rsi > 70 else "Quá bán" if rsi < 30 else "Bình thường"
        st.metric(
            "RSI",
            f"{rsi:.1f}",
            rsi_status
        )
    
    # Data quality and signals
    col1, col2 = st.columns(2)
    
    with col1:
        quality = overview_data.get('data_quality', 0)
        quality_text = "Tốt" if quality > 0.7 else "Trung bình" if quality > 0.4 else "Kém"
        quality_color = "#4CAF50" if quality > 0.7 else "#FF9800" if quality > 0.4 else "#F44336"
        
        st.markdown(f"""
        <div style="padding: 0.5rem; background: {quality_color}20; border-left: 3px solid {quality_color}; border-radius: 4px;">
            <strong>Chất lượng dữ liệu:</strong> {quality_text} ({quality:.0%})
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        signals = overview_data.get('quick_signals', [])
        if signals:
            signals_text = " • ".join(signals[:3])
            st.markdown(f"""
            <div style="padding: 0.5rem; background: #2196F320; border-left: 3px solid #2196F3; border-radius: 4px;">
                <strong>Tín hiệu:</strong> {signals_text}
            </div>
            """, unsafe_allow_html=True)


def render_individual_agent_results(analyses: Dict[str, Any]):
    """Render results from individual agents"""
    st.markdown("### 🤖 Kết quả từng AI Agent")
    
    # Create tabs for each agent
    tab_names = []
    tab_contents = []
    
    agent_order = ['technical', 'fundamental', 'pe_valuation', 'investment_advisor']
    agent_display_names = {
        'technical': '📈 Technical Analyst',
        'fundamental': '💰 Fundamental Analyst', 
        'pe_valuation': '📊 PE Valuation',
        'investment_advisor': '🎯 Investment Advisor'
    }
    
    for agent_type in agent_order:
        if agent_type in analyses:
            tab_names.append(agent_display_names[agent_type])
            tab_contents.append((agent_type, analyses[agent_type]))
    
    if not tab_contents:
        st.warning("⚠️ Chưa có kết quả phân tích từ các agents")
        return
    
    tabs = st.tabs(tab_names)
    
    for i, (tab, (agent_type, result)) in enumerate(zip(tabs, tab_contents)):
        with tab:
            render_single_agent_result(agent_type, result)


def render_single_agent_result(agent_type: str, result: Any):
    """Render result from a single agent"""
    if hasattr(result, 'recommendation'):
        # Main recommendation card
        rec_color = get_recommendation_color(result.recommendation)
        
        # Agent color mapping
        agent_colors = {
            'technical': '#2196F3',
            'fundamental': '#4CAF50', 
            'pe_valuation': '#FF9800',
            'investment_advisor': '#9C27B0'
        }
        agent_color = agent_colors.get(agent_type, '#757575')
        
        # Agent icon mapping  
        agent_icons = {
            'technical': '📈',
            'fundamental': '💰',
            'pe_valuation': '📊', 
            'investment_advisor': '🎯'
        }
        agent_icon = agent_icons.get(agent_type, '🤖')
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            <div style="padding: 1.5rem; background: white; border-radius: 12px; 
                       border-left: 4px solid {agent_color}; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h4 style="color: {agent_color}; margin: 0 0 1rem 0; display: flex; align-items: center; gap: 0.5rem;">
                    {agent_icon} {result.agent_name}
                </h4>
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                    <span style="background: {rec_color}; color: white; padding: 0.4rem 0.8rem; 
                                border-radius: 20px; font-weight: 600; font-size: 0.9rem;">
                        {result.recommendation}
                    </span>
                    <span style="color: {agent_color}; font-weight: 500;">
                        Tin cậy: {result.confidence_level}%
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Confidence gauge
            fig_gauge = create_confidence_gauge(result.confidence_level, agent_color)
            st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
        
        # Key points and concerns
        col1, col2 = st.columns(2)
        
        with col1:
            if result.key_points:
                st.markdown("**📊 Điểm nổi bật:**")
                for point in result.key_points:
                    st.markdown(f"• {point}")
        
        with col2:
            if result.concerns:
                st.markdown("**⚠️ Lưu ý:**")
                for concern in result.concerns:
                    st.markdown(f"• {concern}")
        
        # Data quality indicator
        quality = getattr(result, 'data_quality', 0.8)
        quality_text = "Cao" if quality > 0.8 else "Trung bình" if quality > 0.5 else "Thấp"
        quality_color = "#4CAF50" if quality > 0.8 else "#FF9800" if quality > 0.5 else "#F44336"
        
        st.markdown(f"""
        <div style="margin: 1rem 0; padding: 0.5rem; background: {quality_color}20; 
                   border-left: 3px solid {quality_color}; border-radius: 4px;">
            <strong>Chất lượng dữ liệu:</strong> {quality_text} ({quality:.0%})
        </div>
        """, unsafe_allow_html=True)
        
        # Detailed analysis in expander
        with st.expander("📝 Phân tích chi tiết"):
            st.markdown(result.reasoning)
            
            # Show raw data if available
            if hasattr(result, 'raw_data') and result.raw_data:
                with st.expander("🔢 Dữ liệu thô"):
                    st.json(result.raw_data)
    else:
        st.error(f"❌ Lỗi từ {agent_type}: {result}")


def safe_get_from_result(result, key, default=None):
    """Safely get value from analysis result (handles both dict and object)"""
    if result is None:
        return default
    
    # If it's a dataclass or object with attributes
    if hasattr(result, key):
        return getattr(result, key)
    
    # If it's a dict
    if isinstance(result, dict):
        return result.get(key, default)
    
    # Try to access as dict anyway (some objects support dict-like access)
    try:
        return result[key]
    except (KeyError, TypeError):
        return default


def render_consensus_analysis(consensus_result: Any):
    """Render consensus analysis from Investment Advisor - FIXED"""
    st.markdown("### 🎯 Khuyến nghị tổng hợp")
    
    if not consensus_result:
        st.warning("⚠️ Chưa có khuyến nghị tổng hợp")
        return
    
    # Safely extract values
    final_recommendation = safe_get_from_result(consensus_result, 'final_recommendation', 'N/A')
    confidence_level = safe_get_from_result(consensus_result, 'confidence_level', 0)
    target_price = safe_get_from_result(consensus_result, 'target_price', 0)
    investment_horizon = safe_get_from_result(consensus_result, 'investment_horizon', 'N/A')
    
    # Convert confidence to percentage if needed
    if isinstance(confidence_level, float) and confidence_level <= 1:
        confidence_pct = int(confidence_level * 100)
    else:
        confidence_pct = int(confidence_level)
    
    # Main consensus metrics
    cols = st.columns(4)
    
    with cols[0]:
        rec_color = get_recommendation_color(final_recommendation)
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; border-radius: 10px; 
                   background: linear-gradient(135deg, {rec_color}22, {rec_color}11);">
            <h3 style="color: {rec_color}; margin: 0;">{final_recommendation}</h3>
            <p style="margin: 0; opacity: 0.8;">Khuyến nghị</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        conf_text = get_confidence_level_text(confidence_pct)
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; border-radius: 10px; 
                   background: linear-gradient(135deg, #2196F322, #2196F311);">
            <h3 style="color: #2196F3; margin: 0;">{confidence_pct}%</h3>
            <p style="margin: 0; opacity: 0.8;">{conf_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        if target_price and target_price > 0:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; border-radius: 10px; 
                       background: linear-gradient(135deg, #4CAF5022, #4CAF5011);">
                <h3 style="color: #4CAF50; margin: 0;">{format_vnd_amount(target_price)}</h3>
                <p style="margin: 0; opacity: 0.8;">Target Price</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; border-radius: 10px; 
                       background: linear-gradient(135deg, #75757522, #75757511);">
                <h3 style="color: #757575; margin: 0;">N/A</h3>
                <p style="margin: 0; opacity: 0.8;">Target Price</p>
            </div>
            """, unsafe_allow_html=True)
    
    with cols[3]:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; border-radius: 10px; 
                   background: linear-gradient(135deg, #FF980022, #FF980011);">
            <h3 style="color: #FF9800; margin: 0;">{investment_horizon}</h3>
            <p style="margin: 0; opacity: 0.8;">Thời gian</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed consensus analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Chi tiết phân tích")
        
        # Get reasoning
        reasoning = safe_get_from_result(consensus_result, 'reasoning', 'Không có chi tiết phân tích')
        if reasoning and len(reasoning) > 200:
            # Show truncated version
            st.markdown(reasoning[:200] + "...")
            with st.expander("Xem đầy đủ"):
                st.markdown(reasoning)
        else:
            st.markdown(reasoning)
    
    with col2:
        st.markdown("#### ⚠️ Yếu tố cần lưu ý")
        
        # Get concerns
        concerns = safe_get_from_result(consensus_result, 'concerns', [])
        if concerns:
            for concern in concerns:
                st.markdown(f"• {concern}")
        else:
            st.info("✅ Không có mối quan ngại đặc biệt")
        
        # Get key points
        key_points = safe_get_from_result(consensus_result, 'key_points', [])
        if key_points:
            st.markdown("**📊 Điểm nổi bật:**")
            for point in key_points[:3]:  # Show top 3
                st.markdown(f"• {point}")


def create_confidence_gauge(confidence: int, color: str = "#4CAF50") -> go.Figure:
    """Create confidence level gauge chart"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=confidence,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Confidence", 'font': {'size': 16}},
        delta={'reference': 75, 'position': "top"},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': '#FFCDD2'},
                {'range': [40, 70], 'color': '#FFF9C4'},
                {'range': [70, 100], 'color': '#C8E6C9'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
        font={'color': "darkblue", 'family': "Arial"}
    )
    
    return fig


def render_export_options(analysis_result: Dict[str, Any], symbol: str):
    """Render export options"""
    st.markdown("### 📥 Xuất báo cáo")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export PDF", use_container_width=True):
            st.info("Tính năng export PDF đang được phát triển")
    
    with col2:
        if st.button("📊 Export Excel", use_container_width=True):
            st.info("Tính năng export Excel đang được phát triển")
    
    with col3:
        # Export JSON
        if analysis_result:
            import json
            
            # Convert analysis result to JSON-serializable format
            json_data = {}
            for key, value in analysis_result.items():
                try:
                    # Handle dataclass objects
                    if hasattr(value, '__dict__'):
                        json_data[key] = value.__dict__
                    else:
                        json_data[key] = value
                except:
                    json_data[key] = str(value)
            
            json_str = json.dumps(json_data, indent=2, default=str, ensure_ascii=False)
            st.download_button(
                "💾 Export JSON",
                data=json_str,
                file_name=f"{symbol}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )


def render_batch_analysis_section():
    """Render batch analysis input section"""
    st.markdown("### 🔄 Phân tích hàng loạt")
    
    symbols_input = st.text_area(
        "Nhập danh sách mã cổ phiếu (cách nhau bởi dấu phẩy)",
        placeholder="VCB, VIC, FPT, MWG, VHM",
        help="Nhập tối đa 10 mã cổ phiếu, cách nhau bởi dấu phẩy"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        batch_type = st.selectbox(
            "Loại phân tích",
            ["Quick Overview", "Technical Only", "Fundamental Only", "Full Analysis"]
        )
    
    with col2:
        if st.button("🚀 Bắt đầu phân tích hàng loạt", type="primary"):
            if symbols_input:
                from ..utils.helpers import parse_stock_symbols
                symbols = parse_stock_symbols(symbols_input)
                
                if symbols:
                    st.session_state.batch_symbols = symbols
                    st.session_state.batch_type = batch_type
                    st.session_state.should_batch_analyze = True
                    st.success(f"Sẽ phân tích {len(symbols)} cổ phiếu: {', '.join(symbols)}")
                else:
                    st.error("❌ Không có mã cổ phiếu hợp lệ")


def render_settings_sidebar():
    """Render settings in sidebar"""
    with st.sidebar:
        st.markdown("### ⚙️ Cài đặt")
        
        # User profile settings
        with st.expander("👤 Hồ sơ đầu tư"):
            risk_tolerance = st.selectbox(
                "Khả năng chấp nhận rủi ro",
                ["Thấp", "Trung bình", "Cao"],
                index=1
            )
            
            time_horizon = st.selectbox(
                "Thời gian đầu tư",
                ["1-3 tháng", "3-6 tháng", "6-12 tháng", "1-2 năm", "Trên 2 năm"],
                index=2
            )
            
            expected_growth = st.slider(
                "Mức tăng trưởng kỳ vọng (%/năm)",
                min_value=5,
                max_value=50,
                value=15,
                step=5
            )
            
            # Store in session state
            st.session_state.user_profile = {
                'risk_tolerance': risk_tolerance.lower(),
                'time_horizon': time_horizon,
                'expected_growth': expected_growth
            }
        
        # Display settings
        with st.expander("🖥️ Hiển thị"):
            show_technical_details = st.checkbox("Hiện chi tiết kỹ thuật", value=False)
            show_raw_data = st.checkbox("Hiện dữ liệu thô", value=False)
            auto_refresh = st.checkbox("Tự động cập nhật", value=False)
            
            st.session_state.display_settings = {
                'show_technical_details': show_technical_details,
                'show_raw_data': show_raw_data,
                'auto_refresh': auto_refresh
            }
        
        # Cache control
        with st.expander("🔄 Cache"):
            if st.button("🗑️ Xóa cache"):
                from ..utils.helpers import reset_analysis_cache
                reset_analysis_cache()
                st.success("✅ Đã xóa cache")
            
            st.info("Cache giúp tăng tốc độ phân tích. Xóa cache nếu bạn muốn dữ liệu mới nhất.")


def show_loading_message(message: str = "Đang phân tích..."):
    """Show loading message with spinner"""
    return st.spinner(message)


def show_error_message(error: str, suggestion: str = ""):
    """Show formatted error message"""
    st.error(f"❌ {error}")
    if suggestion:
        st.info(f"💡 {suggestion}")


def show_success_message(message: str):
    """Show formatted success message"""
    st.success(f"✅ {message}")