"""
Custom CSS styles for Agents Stock 2.0 Dashboard.
"""
import streamlit as st


def inject_global_css():
    """Inject custom CSS cho dark theme và professional styling."""
    
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Container */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background-color: #1e2124;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #2f3136;
        border-radius: 10px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        color: #b9bbbe;
        font-weight: 500;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #5865f2;
        color: white;
    }
    
    /* Metric Cards */
    [data-testid="metric-container"] {
        background-color: #36393f;
        border: 1px solid #4f545c;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    [data-testid="metric-container"] > div {
        color: #ffffff;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #5865f2 0%, #3c4fe6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(88, 101, 242, 0.3);
    }
    
    /* Success/Warning/Error Messages */
    .stAlert {
        border-radius: 8px;
        border: none;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 600;
    }
    
    /* Rating Badges */
    .rating-buy {
        background: linear-gradient(90deg, #00d084 0%, #00a86b 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    
    .rating-sell {
        background: linear-gradient(90deg, #ed4245 0%, #c73e1d 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    
    .rating-hold {
        background: linear-gradient(90deg, #faa61a 0%, #f57c00 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Loading Spinner */
    .stSpinner > div {
        border-color: #5865f2;
    }
    
    /* Json Expander */
    .streamlit-expanderHeader {
        background-color: #36393f;
        border-radius: 8px;
    }
    
    /* Custom Progress Bars */
    .stProgress .st-bo {
        background-color: #5865f2;
    }
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)
