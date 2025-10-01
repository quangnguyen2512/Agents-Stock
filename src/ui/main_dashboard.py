# src/ui/main_dashboard.py - Golden Key Professional Dashboard (Fixed Session State)

import streamlit as st
import asyncio
from datetime import datetime
import logging
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional

from .styles import (
    load_golden_key_css, 
    create_logo_header, 
    get_recommendation_color,
    create_professional_metric, 
    create_score_display, 
    create_professional_footer
)

from src.core.analysis_pipeline import AnalysisPipeline
from src.utils.helpers import (
    validate_stock_symbol, 
    display_api_key_warning,
    format_vnd_amount, 
    get_confidence_level_text, 
    safe_get_from_result
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoldenKeyDashboard:
    """Golden Key Investment Professional Dashboard (Fixed Session State)"""

    def __init__(self):
        self.pipeline = None
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize session state with Golden Key defaults (FIXED)"""
        # Only set defaults if not already set - NEVER modify after widget creation
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = {}

        if 'analysis_history' not in st.session_state:
            st.session_state.analysis_history = []

        if 'user_profile' not in st.session_state:
            st.session_state.user_profile = {
                'risk_tolerance': 'moderate',
                'time_horizon': '6-12 months',
                'expected_growth': 20
            }

        if 'display_settings' not in st.session_state:
            st.session_state.display_settings = {
                'show_technical_details': False,
                'show_raw_data': False,
                'auto_refresh': False
            }

        if 'should_analyze' not in st.session_state:
            st.session_state.should_analyze = False

        if 'current_pe_real' not in st.session_state:
            st.session_state.current_pe_real = None

        if 'current_symbol' not in st.session_state:
            st.session_state.current_symbol = None

    def _initialize_pipeline(self) -> bool:
        """Initialize analysis pipeline"""
        try:
            if not self.pipeline:
                self.pipeline = AnalysisPipeline()
                logger.info("✅ Golden Key Analysis pipeline initialized")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize pipeline: {e}")
            st.error(f"""
❌ **Lỗi khởi tạo hệ thống Golden Key**

{str(e)}

**Vui lòng kiểm tra:**
- API Key Google Gemini trong config.json
- Kết nối internet
- Cấu hình hệ thống
""")
            return False

    def render_header(self):
        """Render Golden Key professional header"""
        create_logo_header()

    def render_stock_input(self) -> str:
        """Render professional stock input section (FIXED)"""
        st.markdown("""
        <div class="gk-stock-input fade-in-up">
            <h3>📈 Phân tích cổ phiếu chuyên nghiệp</h3>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([3, 2, 1])

        with col1:
            # Use widget without conflicting with session state
            symbol = st.text_input(
                "Mã cổ phiếu",
                placeholder="Nhập mã cổ phiếu (VD: VCB, VIC, FPT...)",
                help="Nhập mã cổ phiếu niêm yết trên HOSE, HNX, UPCOM",
                key="stock_input_widget"  # Use unique key
            )
            if symbol:
                symbol = symbol.upper().strip()

        with col2:
            # Fixed: Use selectbox without conflicting session state access
            analysis_options = ["Toàn diện", "Nhanh", "Technical", "Fundamental", "PE Valuation"]
            analysis_type = st.selectbox(
                "Loại phân tích",
                analysis_options,
                index=0,  # Default to comprehensive
                help="Chọn loại phân tích phù hợp với nhu cầu đầu tư",
                key="analysis_type_widget"  # Use unique key
            )

        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            analyze_button = st.button(
                "🚀 Phân tích",
                type="primary",
                use_container_width=True,
                help="Bắt đầu phân tích chuyên nghiệp với 4 AI Agents",
                key="analyze_button_widget"
            )

        # FIXED: Only modify session state in response to button click
        if analyze_button and symbol:
            # Store values only when button is clicked
            st.session_state.selected_symbol = symbol
            st.session_state.selected_analysis_type = analysis_type
            st.session_state.should_analyze = True
            st.session_state.current_symbol = symbol

            # Force rerun to process the analysis
            st.rerun()

        return symbol if analyze_button and symbol else ""

    def render_pe_real_display(self, pe_real: float):
        """Render current PE Real display"""
        if pe_real and pe_real > 0:
            st.markdown(f"""
            <div class="gk-pe-display fade-in-up">
                <p class="gk-pe-value">{pe_real:.2f}x</p>
                <p class="gk-pe-label">PE Real hiện tại</p>
            </div>
            """, unsafe_allow_html=True)

    def render_professional_metrics(self, overview_data: Dict[str, Any]):
        """Render professional metrics grid"""
        if not overview_data:
            return

        metrics = overview_data.get('quick_metrics', {})

        metrics_html = '<div class="gk-metrics">'

        # Current Price
        price = metrics.get('current_price', 0)
        change = metrics.get('change_1d', 0)
        change_str = f"{change:.2f}%" if change != 0 else "0.00%"
        change_color = "normal" if change >= 0 else "inverse"

        metrics_html += create_professional_metric(
            "Giá hiện tại", 
            f"{format_vnd_amount(price)} VND", 
            change_str, 
            change_color
        )

        # Volume
        volume = metrics.get('volume', 0)
        metrics_html += create_professional_metric(
            "Khối lượng GD", 
            f"{volume:,.0f}"
        )

        # PE Ratio
        pe = metrics.get('pe', 0)
        pe_real = metrics.get('pe_real', 0)
        pe_display = f"{pe:.1f}x" if pe > 0 else "N/A"
        pe_real_str = f"PE Real: {pe_real:.1f}x" if pe_real > 0 else None

        metrics_html += create_professional_metric(
            "PE Ratio", 
            pe_display, 
            pe_real_str
        )

        # Market Cap
        market_cap = metrics.get('market_cap', 0)
        if market_cap > 0:
            if market_cap > 1000000000000:  # > 1T
                cap_str = f"{market_cap/1000000000000:.1f}T VND"
            else:
                cap_str = f"{market_cap/1000000000:.0f}B VND"
        else:
            cap_str = "N/A"

        metrics_html += create_professional_metric(
            "Vốn hóa", 
            cap_str
        )

        metrics_html += '</div>'

        st.markdown(metrics_html, unsafe_allow_html=True)

        # Store PE Real for display
        if pe_real > 0:
            st.session_state.current_pe_real = pe_real

    async def run_analysis(self, symbol: str, analysis_type: str):
        """Run analysis with professional progress tracking"""
        try:
            user_profile = st.session_state.get('user_profile', {})

            progress_bar = st.progress(0)
            status_text = st.empty()

            if analysis_type == "Toàn diện":
                status_text.text("🤖 Khởi động 4 AI chuyên gia...")
                progress_bar.progress(10)

                result = await self.pipeline.analyze_comprehensive(symbol, user_profile)

                progress_bar.progress(100)
                status_text.text("✅ Phân tích toàn diện hoàn thành!")

            elif analysis_type == "Nhanh":
                status_text.text("⚡ Đang lấy dữ liệu nhanh...")
                progress_bar.progress(50)

                result = self.pipeline.get_quick_overview(symbol)

                progress_bar.progress(100)
                status_text.text("✅ Phân tích nhanh hoàn thành!")

            else:
                # Single agent analysis
                agent_map = {
                    "Technical": "technical",
                    "Fundamental": "fundamental", 
                    "PE Valuation": "pe_valuation"
                }

                agent_type = agent_map.get(analysis_type)
                if agent_type:
                    status_text.text(f"🤖 {analysis_type} Agent đang phân tích...")
                    progress_bar.progress(50)

                    result = await self.pipeline.analyze_single_agent(symbol, agent_type, user_profile)

                    progress_bar.progress(100)
                    status_text.text(f"✅ {analysis_type} hoàn thành!")
                else:
                    raise ValueError(f"Unknown analysis type: {analysis_type}")

            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()

            return result

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            raise e

    def render_main_analysis(self):
        """Render main analysis section (FIXED)"""
        # Stock input
        symbol = self.render_stock_input()

        # Handle analysis trigger (FIXED - check session state properly)
        if st.session_state.get('should_analyze', False):
            st.session_state.should_analyze = False  # Reset trigger

            # Get stored values
            symbol = st.session_state.get('selected_symbol', '')
            analysis_type = st.session_state.get('selected_analysis_type', 'Toàn diện')

            if not symbol:
                symbol = st.session_state.get('selected_symbol', '')

            if not validate_stock_symbol(symbol):
                st.error("❌ Mã cổ phiếu không hợp lệ. Vui lòng nhập mã 3-4 ký tự (VD: VCB, VIC, FPT)")
                return

            # Initialize pipeline
            if not self._initialize_pipeline():
                return

            try:
                with st.spinner("🤖 Đang phân tích..."):
                    result = asyncio.run(self.run_analysis(symbol, analysis_type))

                if result:
                    # Display current PE Real if available
                    if st.session_state.get('current_pe_real'):
                        self.render_pe_real_display(st.session_state.current_pe_real)

                    # Store results
                    st.session_state.analysis_results[symbol] = result

                    # Display results
                    self.render_analysis_results(symbol, result)

                    st.success(f"✅ Phân tích {symbol} hoàn thành!")

            except Exception as e:
                st.error(f"❌ Lỗi phân tích {symbol}: {str(e)}")
                logger.error(f"Analysis error for {symbol}: {e}")

    def render_analysis_results(self, symbol: str, result: dict):
        """Render analysis results professionally"""
        st.markdown(f"## 📊 Báo cáo phân tích {symbol}")

        # Quick metrics if available
        if 'quick_metrics' in result:
            self.render_professional_metrics(result)

        # Individual agent results
        if 'individual_analyses' in result:
            self.render_agent_results(result['individual_analyses'])

        # Consensus analysis
        if 'consensus' in result:
            self.render_consensus_analysis(result['consensus'])

        # Export options
        self.render_export_options(result, symbol)

        # Professional footer
        create_professional_footer()

    def render_agent_results(self, analyses: Dict[str, Any]):
        """Render professional agent analysis results"""
        st.markdown("### 🤖 Phân tích từ 4 chuyên gia AI")

        # Create professional scoring system
        scores = self.create_scoring_system(analyses)

        if scores:
            st.markdown("#### 📊 Bảng điểm chuyên nghiệp")
            score_html = create_score_display(scores)
            st.markdown(score_html, unsafe_allow_html=True)

        if analyses:
            self.render_analysis_table(analyses)

        # Individual agent details
        agent_order = ["technical", "fundamental", "pe_valuation", "investment_advisor"]
        agent_names = {
            "technical": "Phân tích Kỹ thuật",
            "fundamental": "Phân tích Cơ bản", 
            "pe_valuation": "Định giá PE",
            "investment_advisor": "Tư vấn Đầu tư"
        }

        for agent_type in agent_order:
            if agent_type in analyses:
                self.render_single_agent(agent_type, analyses[agent_type], agent_names[agent_type])

    def create_scoring_system(self, analyses: Dict[str, Any]) -> Dict[str, tuple]:
        """Create professional scoring system for each analysis"""
        scores = {}

        if 'technical' in analyses:
            tech = analyses['technical']
            if hasattr(tech, 'confidence_level'):
                tech_score = min(25, int(tech.confidence_level * 0.25))
                scores['Technical'] = (tech_score, 25)

        if 'fundamental' in analyses:
            fund = analyses['fundamental']
            if hasattr(fund, 'confidence_level'):
                fund_score = min(25, int(fund.confidence_level * 0.25))
                scores['Fundamental'] = (fund_score, 25)

        if 'pe_valuation' in analyses:
            pe_val = analyses['pe_valuation']
            if hasattr(pe_val, 'confidence_level'):
                pe_score = min(25, int(pe_val.confidence_level * 0.25))
                scores['PE Valuation'] = (pe_score, 25)

        if 'investment_advisor' in analyses:
            inv_adv = analyses['investment_advisor']
            if hasattr(inv_adv, 'confidence_level'):
                inv_score = min(25, int(inv_adv.confidence_level * 0.25))
                scores['Investment'] = (inv_score, 25)

        # Total Score (0-100)
        total_score = sum(score for score, _ in scores.values())
        scores['Tổng điểm'] = (total_score, 100)

        return scores

    def render_analysis_table(self, analyses: Dict[str, Any]):
        """Render professional analysis summary table"""
        table_data = []

        agent_names = {
            "technical": "Kỹ thuật",
            "fundamental": "Cơ bản", 
            "pe_valuation": "PE Valuation",
            "investment_advisor": "Tư vấn"
        }

        for agent_type, result in analyses.items():
            if hasattr(result, 'recommendation'):
                # Get target price if available
                target_price = "N/A"

                if hasattr(result, 'raw_data') and result.raw_data:
                    if agent_type == "pe_valuation":
                        # Try to get fair value from PE analysis
                        fair_value = result.raw_data.get('fair_value_ranges', {})
                        if 'scenarios' in fair_value and 'fair' in fair_value['scenarios']:
                            target_price = f"{fair_value['scenarios']['fair']['fair_value']:,.0f} VND"

                    elif agent_type == "technical":
                        # Try to get resistance level
                        support_resistance = result.raw_data.get('support_resistance', {})
                        if 'nearest_resistance' in support_resistance:
                            resistance = support_resistance['nearest_resistance']
                            if resistance:
                                target_price = f"{resistance:,.0f} VND"

                table_data.append({
                    "Chuyên gia": agent_names.get(agent_type, agent_type.title()),
                    "Khuyến nghị": result.recommendation,
                    "Tin cậy": f"{result.confidence_level}%",
                    "Target Price": target_price,
                    "Điểm số": f"{min(25, int(result.confidence_level * 0.25))}/25"
                })

        if table_data:
            df = pd.DataFrame(table_data)

            def style_recommendation(val):
                if any(word in val.upper() for word in ["STRONG BUY", "MUA MẠNH"]):
                    return "background-color: #28a745; color: white; font-weight: bold;"
                elif any(word in val.upper() for word in ["BUY", "MUA"]):
                    return "background-color: #28a745; color: white;"
                elif any(word in val.upper() for word in ["HOLD", "GIỮ"]):
                    return "background-color: #ffc107; color: black;"
                else:
                    return "background-color: #dc3545; color: white;"

            styled_df = df.style.map(style_recommendation, subset=['Khuyến nghị']) \
                .set_table_styles([
                    {'selector': 'th', 'props': [
                        ('background-color', '#B8860B'),
                        ('color', 'white'),
                        ('font-weight', 'bold'),
                        ('text-align', 'center'),
                        ('padding', '12px')
                    ]},
                    {'selector': 'td', 'props': [
                        ('text-align', 'center'),
                        ('padding', '8px'),
                        ('border-bottom', '1px solid #dee2e6')
                    ]},
                    {'selector': 'table', 'props': [
                        ('border-collapse', 'collapse'),
                        ('margin', '25px 0'),
                        ('font-size', '0.9em'),
                        ('font-family', '"Inter", sans-serif'),
                        ('min-width', '400px'),
                        ('border-radius', '12px'),
                        ('overflow', 'hidden'),
                        ('box-shadow', '0 4px 20px rgba(0,0,0,0.08)')
                    ]}
                ])

            st.markdown("#### 📋 Bảng tổng hợp khuyến nghị")
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

    def render_single_agent(self, agent_type: str, result: Any, display_name: str):
        """Render single agent result in professional format"""
        if not hasattr(result, 'recommendation'):
            return

        # Agent colors
        agent_colors = {
            "technical": "#2196F3",
            "fundamental": "#4CAF50", 
            "pe_valuation": "#FF9800",
            "investment_advisor": "#9C27B0"
        }
        color = agent_colors.get(agent_type, "#6C757D")

        with st.expander(f"{display_name} - {result.recommendation} ({result.confidence_level}%)", expanded=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"""
**Chuyên gia:** {result.agent_name}  
**Khuyến nghị:** {result.recommendation} ({result.confidence_level}% tin cậy)  
**Chất lượng dữ liệu:** {result.data_quality*100:.0f}%
""")

                if result.key_points:
                    st.markdown("**Điểm nổi bật:**")
                    for point in result.key_points:
                        st.markdown(f"• {point}")

            with col2:
                # Create confidence gauge
                fig = self.create_confidence_gauge(result.confidence_level, color)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            if result.concerns:
                st.markdown("**⚠️ Lưu ý:**")
                for concern in result.concerns:
                    st.markdown(f"⚠️ {concern}")

            # Detailed analysis
            with st.expander("📋 Phân tích chi tiết"):
                st.markdown(result.reasoning)

    def create_confidence_gauge(self, confidence: int, color: str) -> go.Figure:
        """Create professional confidence gauge"""
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = confidence,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Confidence", 'font': {'size': 14, 'family': '"Inter"'}},
            delta = {'reference': 70, 'position': "top"},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': color},
                'bar': {'color': color},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "#DEE2E6",
                'steps': [
                    {'range': [0, 40], 'color': '#FFCDD2'},
                    {'range': [40, 70], 'color': '#FFF3E0'},
                    {'range': [70, 100], 'color': '#E8F5E8'}
                ],
                'threshold': {
                    'line': {'color': color, 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))

        fig.update_layout(
            height=200, 
            margin=dict(l=20, r=20, t=40, b=20),
            font={'color': '#212529', 'family': '"Inter"'},
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        return fig

    def render_consensus_analysis(self, consensus: Any):
        """Render professional consensus analysis"""
        if not consensus:
            return

        st.markdown("### 🎯 Khuyến nghị tổng hợp Golden Key")

        # Extract values safely
        final_rec = safe_get_from_result(consensus, 'final_recommendation', 'N/A')
        confidence = safe_get_from_result(consensus, 'confidence_level', 0)
        target_price = safe_get_from_result(consensus, 'target_price', 0)
        time_horizon = safe_get_from_result(consensus, 'investment_horizon', '3-6 tháng')

        # Convert confidence to percentage if needed
        if isinstance(confidence, float) and confidence <= 1:
            confidence_pct = int(confidence * 100)
        else:
            confidence_pct = int(confidence)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            rec_color_class = get_recommendation_color(final_rec)
            st.markdown(f"""
            <div class="gk-metric fade-in-up" style="text-align: center;">
                <div class="gk-recommendation {rec_color_class}" style="margin-bottom: 1rem;">
                    {final_rec}
                </div>
                <p class="gk-metric-label">Khuyến nghị cuối</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            confidence_text = get_confidence_level_text(confidence_pct)
            st.markdown(f"""
            <div class="gk-metric fade-in-up" style="text-align: center;">
                <p class="gk-metric-value">{confidence_pct}%</p>
                <p class="gk-metric-label">Độ tin cậy</p>
                <p class="gk-metric-change" style="color: #B8860B">{confidence_text}</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            target_display = f"{target_price:,.0f} VND" if target_price > 0 else "Đang tính toán"
            st.markdown(f"""
            <div class="gk-metric fade-in-up" style="text-align: center;">
                <p class="gk-metric-value">{target_display}</p>
                <p class="gk-metric-label">Target Price</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="gk-metric fade-in-up" style="text-align: center;">
                <p class="gk-metric-value">{time_horizon}</p>
                <p class="gk-metric-label">Thời gian Nắm giữ</p>
            </div>
            """, unsafe_allow_html=True)

        # Detailed analysis
        reasoning = safe_get_from_result(consensus, 'reasoning', 'Đang phân tích...')
        if reasoning and len(reasoning) > 100:
            st.markdown("#### 📋 Phân tích tổng hợp")
            st.markdown(reasoning[:300] + "...")
            with st.expander("Xem phân tích đầy đủ"):
                st.markdown(reasoning)

    def render_export_options(self, result: dict, symbol: str):
        """Render professional export options"""
        st.markdown("### 💾 Tải xuống báo cáo")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📄 Export PDF", use_container_width=True):
                st.info("Tính năng export PDF đang hoàn thiện...")

        with col2:
            if st.button("📊 Export Excel", use_container_width=True):
                st.info("Tính năng export Excel đang hoàn thiện...")

        with col3:
            if result:
                import json

                # Prepare JSON data
                json_data = {}
                for key, value in result.items():
                    try:
                        if hasattr(value, '__dict__'):
                            json_data[key] = {attr: getattr(value, attr) for attr in dir(value) if not attr.startswith('_')}
                        else:
                            json_data[key] = value
                    except:
                        json_data[key] = str(value)

                json_str = json.dumps(json_data, indent=2, default=str, ensure_ascii=False)

                st.download_button(
                    "📋 Export JSON",
                    data=json_str,
                    file_name=f"GoldenKey_{symbol}_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )

    def render(self):
        """Main render method for Golden Key Dashboard (FIXED)"""
        # Check API key first
        if not display_api_key_warning():
            return

        # Load professional CSS
        load_golden_key_css()

        # Professional header
        self.render_header()

        # Main analysis section
        self.render_main_analysis()


def main():
    """Main function for testing dashboard"""
    dashboard = GoldenKeyDashboard()
    dashboard.render()


if __name__ == "__main__":
    main()
