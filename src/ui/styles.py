# src/ui/styles.py - Golden Key Professional Styles
import streamlit as st

def load_golden_key_css():
    """Load professional CSS styles for Golden Key Investment Dashboard"""
    
    custom_css = """
    <style>
    /* Import Professional Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    /* Golden Key Brand Colors */
    :root {
        --gk-primary: #B8860B;        /* Dark Golden */
        --gk-secondary: #FFD700;      /* Golden Yellow */
        --gk-accent: #DAA520;         /* Goldenrod */
        --gk-dark: #1C1C1C;          /* Dark Background */
        --gk-light: #F8F9FA;         /* Light Background */
        --gk-success: #28A745;        /* Success Green */
        --gk-warning: #FFC107;        /* Warning Orange */
        --gk-danger: #DC3545;         /* Danger Red */
        --gk-info: #17A2B8;          /* Info Blue */
        --gk-text-primary: #212529;   /* Primary Text */
        --gk-text-secondary: #6C757D; /* Secondary Text */
        --gk-text-light: #FFFFFF;     /* Light Text */
        --gk-border: #DEE2E6;         /* Border Color */
        --gk-shadow: rgba(184, 134, 11, 0.15); /* Golden Shadow */
        --gk-gradient: linear-gradient(135deg, var(--gk-primary) 0%, var(--gk-secondary) 100%);
        --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-heading: 'Poppins', sans-serif;
    }
    
    /* Global Styles */
    .stApp {
        font-family: var(--font-primary);
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        color: var(--gk-text-primary);
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Professional Header with Logo */
    .gk-header {
        background: var(--gk-gradient);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: var(--gk-text-light);
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px var(--gk-shadow);
        position: relative;
        overflow: hidden;
    }
    
    .gk-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .gk-logo {
        display: inline-block;
        margin-bottom: 1rem;
        cursor: pointer;
        transition: transform 0.3s ease;
    }
    
    .gk-logo:hover {
        transform: scale(1.05);
    }
    
    .gk-logo img {
        height: 60px;
        width: auto;
        border-radius: 8px;
    }
    
    .gk-title {
        font-family: var(--font-heading);
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        letter-spacing: -0.02em;
    }
    
    .gk-subtitle {
        font-size: 1.1rem;
        font-weight: 400;
        margin: 0.5rem 0 0 0;
        opacity: 0.95;
        font-style: italic;
    }
    
    .gk-tagline {
        font-size: 0.95rem;
        font-weight: 500;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        letter-spacing: 0.5px;
    }
    
    /* Professional Cards */
    .gk-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid var(--gk-border);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .gk-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 40px rgba(0,0,0,0.12);
    }
    
    .gk-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: var(--gk-gradient);
    }
    
    /* Stock Input Section */
    .gk-stock-input {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
        border-left: 6px solid var(--gk-primary);
    }
    
    .gk-stock-input h3 {
        color: var(--gk-primary);
        font-family: var(--font-heading);
        font-weight: 600;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Current PE Real Display */
    .gk-pe-display {
        background: linear-gradient(135deg, var(--gk-info) 0%, #0056b3 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(23, 162, 184, 0.3);
    }
    
    .gk-pe-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .gk-pe-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin: 0.5rem 0 0 0;
        font-weight: 500;
    }
    
    /* Professional Metrics */
    .gk-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .gk-metric {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border-left: 4px solid var(--gk-primary);
        transition: transform 0.2s ease;
    }
    
    .gk-metric:hover {
        transform: translateY(-2px);
    }
    
    .gk-metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--gk-primary);
        margin: 0;
    }
    
    .gk-metric-label {
        font-size: 0.85rem;
        color: var(--gk-text-secondary);
        font-weight: 500;
        margin: 0.25rem 0 0 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .gk-metric-change {
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0.5rem 0 0 0;
    }
    
    /* Agent Cards */
    .gk-agent-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin: 1rem 0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .gk-agent-card.technical { border-left: 6px solid #2196F3; }
    .gk-agent-card.fundamental { border-left: 6px solid #4CAF50; }
    .gk-agent-card.pe_valuation { border-left: 6px solid #FF9800; }
    .gk-agent-card.investment_advisor { border-left: 6px solid #9C27B0; }
    
    .gk-agent-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 40px rgba(0,0,0,0.12);
    }
    
    .gk-agent-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
    }
    
    .gk-agent-name {
        font-family: var(--font-heading);
        font-size: 1.3rem;
        font-weight: 600;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .gk-agent-score {
        background: var(--gk-gradient);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        box-shadow: 0 2px 8px var(--gk-shadow);
    }
    
    /* Professional Scoring System */
    .gk-score-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .gk-score-item {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        text-align: center;
        border-top: 3px solid var(--gk-primary);
    }
    
    .gk-score-number {
        font-size: 2rem;
        font-weight: 700;
        color: var(--gk-primary);
        margin: 0;
    }
    
    .gk-score-max {
        font-size: 0.8rem;
        color: var(--gk-text-secondary);
        margin: 0;
    }
    
    .gk-score-label {
        font-size: 0.85rem;
        color: var(--gk-text-secondary);
        font-weight: 500;
        margin: 0.5rem 0 0 0;
    }
    
    /* Professional Table */
    .gk-analysis-table {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin: 2rem 0;
    }
    
    .gk-analysis-table table {
        width: 100%;
        border-collapse: collapse;
        font-family: var(--font-primary);
    }
    
    .gk-analysis-table th {
        background: var(--gk-gradient);
        color: white;
        padding: 1rem;
        text-align: left;
        font-weight: 600;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .gk-analysis-table td {
        padding: 1rem;
        border-bottom: 1px solid var(--gk-border);
        font-size: 0.9rem;
    }
    
    .gk-analysis-table tr:hover {
        background: rgba(184, 134, 11, 0.05);
    }
    
    /* Recommendation Badges */
    .gk-recommendation {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 0.85rem;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .gk-rec-strong-buy {
        background: linear-gradient(135deg, #28A745, #20C997);
        color: white;
    }
    
    .gk-rec-buy {
        background: linear-gradient(135deg, #28A745, #6CB2EB);
        color: white;
    }
    
    .gk-rec-hold {
        background: linear-gradient(135deg, #FFC107, #FFB347);
        color: white;
    }
    
    .gk-rec-sell {
        background: linear-gradient(135deg, #DC3545, #E74C3C);
        color: white;
    }
    
    /* Professional Buttons */
    .stButton > button {
        background: var(--gk-gradient);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-family: var(--font-primary);
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px var(--gk-shadow);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px var(--gk-shadow);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Professional Input Fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        border: 2px solid var(--gk-border);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        font-family: var(--font-primary);
        font-size: 1rem;
        transition: all 0.3s ease;
        background: white;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: var(--gk-primary);
        box-shadow: 0 0 0 3px rgba(184, 134, 11, 0.1);
        outline: none;
    }
    
    /* Professional Progress Bars */
    .stProgress > div > div > div {
        background: var(--gk-gradient);
        border-radius: 10px;
    }
    
    .stProgress > div > div {
        background: var(--gk-border);
        border-radius: 10px;
    }
    
    /* Professional Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: white;
        border-radius: 12px;
        padding: 0.5rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border: 1px solid var(--gk-border);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-family: var(--font-primary);
        color: var(--gk-text-secondary);
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--gk-gradient);
        color: white;
        box-shadow: 0 2px 8px var(--gk-shadow);
    }
    
    /* Professional Alerts */
    .stAlert {
        border-radius: 12px;
        border: none;
        font-family: var(--font-primary);
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }
    
    .stAlert[data-baseweb="notification-success"] {
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        border-left: 6px solid var(--gk-success);
    }
    
    .stAlert[data-baseweb="notification-error"] {
        background: linear-gradient(135deg, #f8d7da, #f5c6cb);
        border-left: 6px solid var(--gk-danger);
    }
    
    .stAlert[data-baseweb="notification-warning"] {
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        border-left: 6px solid var(--gk-warning);
    }
    
    .stAlert[data-baseweb="notification-info"] {
        background: linear-gradient(135deg, #cce7ff, #b3d9ff);
        border-left: 6px solid var(--gk-info);
    }
    
    /* Professional Loading Spinner */
    .stSpinner > div {
        border-top-color: var(--gk-primary) !important;
    }
    
    /* Professional Data Tables */
    .stDataFrame {
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border-radius: 12px;
        overflow: hidden;
        border: none;
    }
    
    .stDataFrame table {
        font-family: var(--font-primary);
    }
    
    .stDataFrame th {
        background: var(--gk-gradient) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.85rem !important;
    }
    
    .stDataFrame td {
        padding: 0.75rem 1rem !important;
        border-bottom: 1px solid var(--gk-border) !important;
    }
    
    .stDataFrame tr:hover {
        background: rgba(184, 134, 11, 0.05) !important;
    }
    
    /* Professional Sidebar (if needed) */
    .css-1d391kg {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-right: 2px solid var(--gk-border);
    }
    
    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        .gk-title { font-size: 1.8rem; }
        .gk-subtitle { font-size: 1rem; }
        .gk-header { padding: 1rem; }
        .gk-card { padding: 1.5rem; }
        .gk-agent-card { padding: 1.5rem; }
        .gk-metrics { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }
        .gk-score-grid { grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); }
    }
    
    /* Professional Footer */
    .gk-footer {
        background: var(--gk-dark);
        color: var(--gk-text-light);
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        margin-top: 3rem;
        font-size: 0.9rem;
    }
    
    .gk-footer a {
        color: var(--gk-secondary);
        text-decoration: none;
        font-weight: 600;
    }
    
    .gk-footer a:hover {
        color: var(--gk-accent);
        text-decoration: underline;
    }
    
    /* Animation Classes */
    .fade-in-up {
        animation: fadeInUp 0.6s ease-out;
    }
    
    .fade-in-left {
        animation: fadeInLeft 0.6s ease-out;
    }
    
    .fade-in-right {
        animation: fadeInRight 0.6s ease-out;
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes fadeInLeft {
        from { opacity: 0; transform: translateX(-30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes fadeInRight {
        from { opacity: 0; transform: translateX(30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    /* Smooth Scrolling */
    html {
        scroll-behavior: smooth;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--gk-light);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--gk-gradient);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #9a7209, #cc9900);
    }
    </style>
    """
    
    st.markdown(custom_css, unsafe_allow_html=True)


def create_logo_header():
    """Create professional header with Golden Key logo"""
    st.markdown("""
    <div class="gk-header fade-in-up">
        <div class="gk-logo" onclick="window.open('https://goldenkey.vn', '_blank')">
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" alt="Golden Key Investment" />
        </div>
        <h1 class="gk-title">GOLDEN KEY INVESTMENT</h1>
        <p class="gk-subtitle">AI Stock Analysis Platform</p>
        <p class="gk-tagline">Minh bạch • Tận tâm • Đổi mới • Phát triển bền vững</p>
    </div>
    
    <script>
    // Handle logo click
    document.addEventListener('DOMContentLoaded', function() {
        const logo = document.querySelector('.gk-logo');
        if (logo) {
            logo.addEventListener('click', function() {
                window.open('https://goldenkey.vn', '_blank');
            });
        }
    });
    </script>
    """, unsafe_allow_html=True)


def get_recommendation_color(recommendation: str) -> str:
    """Get professional color for recommendations"""
    rec_upper = recommendation.upper()
    
    if any(word in rec_upper for word in ["STRONG BUY", "MUA MẠNH"]):
        return "gk-rec-strong-buy"
    elif any(word in rec_upper for word in ["BUY", "MUA"]):
        return "gk-rec-buy" 
    elif any(word in rec_upper for word in ["HOLD", "GIỮ"]):
        return "gk-rec-hold"
    else:
        return "gk-rec-sell"


def create_professional_metric(title: str, value: str, change: str = None, 
                              change_color: str = "normal") -> str:
    """Create professional metric card HTML"""
    change_html = ""
    if change:
        color_class = "color: #28A745;" if change_color == "normal" and "+" in change else "color: #DC3545;" if "-" in change else "color: #6C757D;"
        change_html = f'<p class="gk-metric-change" style="{color_class}">{change}</p>'
    
    return f"""
    <div class="gk-metric fade-in-up">
        <p class="gk-metric-value">{value}</p>
        <p class="gk-metric-label">{title}</p>
        {change_html}
    </div>
    """


def create_score_display(scores: dict) -> str:
    """Create professional scoring display"""
    html = '<div class="gk-score-grid fade-in-up">'
    
    for label, (score, max_score) in scores.items():
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        html += f"""
        <div class="gk-score-item">
            <p class="gk-score-number">{score}</p>
            <p class="gk-score-max">/ {max_score}</p>
            <p class="gk-score-label">{label}</p>
            <div style="width: 100%; height: 4px; background: #E9ECEF; border-radius: 2px; margin-top: 0.5rem;">
                <div style="width: {percentage}%; height: 100%; background: var(--gk-gradient); border-radius: 2px; transition: width 0.5s ease;"></div>
            </div>
        </div>
        """
    
    html += '</div>'
    return html


def create_professional_footer():
    """Create professional footer"""
    st.markdown("""
    <div class="gk-footer fade-in-up">
        <p>
            © 2025 <a href="https://goldenkey.vn" target="_blank">Golden Key Investment</a>. 
            All rights reserved. | 
            <a href="https://goldenkey.vn" target="_blank">Tư vấn đầu tư</a> | 
            <a href="https://goldenkey.vn" target="_blank">Liên hệ</a>
        </p>
        <p style="margin-top: 1rem; font-size: 0.8rem; opacity: 0.7;">
            "Tối ưu nguồn vốn, nâng tầm giá trị" - Đối tác hỗ trợ tài chính bền vững
        </p>
    </div>
    """, unsafe_allow_html=True)