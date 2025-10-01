"""
Golden Key AI Trading Platform - Main Entry Point

Hệ thống phân tích cổ phiếu Việt Nam với 4 AI agents chuyên biệt:
- Technical Analyst: Phân tích kỹ thuật nâng cao
- Fundamental Analyst: Phân tích cơ bản
- PE Valuation Analyst: Định giá PE
- Investment Advisor: Tư vấn tổng hợp

Usage:
    streamlit run app.py

Requirements:
    - Google Gemini API key trong .env file
    - Kết nối internet để truy cập VNStock API
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to Python path  
current_dir = Path(__file__).parent
src_path = current_dir / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def main():
    """Main application function."""
    # Page config with Golden Key branding
    st.set_page_config(
        page_title="Golden Key Investment - AI Stock Analysis",
        page_icon="🔑",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': 'https://goldenkey.vn',
            'Report a bug': "https://goldenkey.vn",
            'About': """
            # Golden Key Investment - AI Stock Analysis Platform

            **TẦM NHÌN:** Trở thành đối tác hỗ trợ tài chính bền vững
            **SỨ MỆNH:** Minh bạch, tận tâm, đổi mới, lấy khách hàng làm trung tâm

            ## 4 AI Chuyên gia:
            - 🔬 **Advanced Technical Analysis** (Volume, Divergence, Patterns)
            - 💰 **Fundamental Analysis** (Financial Statements)
            - 📊 **PE Valuation Analysis** (PE Distribution & Fair Value)  
            - 🎯 **Investment Advisory** (Consensus & Recommendations)

            © 2025 Golden Key Investment. All rights reserved.
            """
        }
    )

    try:
        # Try to import enhanced dashboard first
        try:
            from ui.enhanced_main_dashboard import EnhancedGoldenKeyDashboard
            dashboard = EnhancedGoldenKeyDashboard()
            dashboard.render()
            st.success("🚀 **Enhanced AI Analysis System Active!**")

        except ImportError:
            # Enhanced dashboard not available, use basic dashboard
            st.warning("⚠️ Enhanced dashboard not found. Using basic dashboard.")

            from ui.main_dashboard import GoldenKeyDashboard
            dashboard = GoldenKeyDashboard()
            dashboard.render()

    except Exception as e:
        st.error(f"""
        ❌ **Lỗi khởi tạo hệ thống Golden Key**

        {str(e)}

        **Vui lòng kiểm tra:**
        - API Key Google Gemini trong .env file
        - Kết nối internet
        - Cấu hình hệ thống
        """)

if __name__ == "__main__":
    main()
