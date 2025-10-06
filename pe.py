# test1.py — Golden Key | PE Percentile Valuation (AI-first) — revised with 25–99 percentiles

import os
import json
import asyncio
import traceback
import pandas as pd
import streamlit as st

# Import nội bộ
try:
    from src.data.pe_api import PEAPI
    from src.agents.pe_valuation_analyst import MarketContext, PEValuationAnalyst
    IMPORT_OK = True
except ImportError as e:
    IMPORT_OK = False
    IMPORT_ERR = str(e)

# -----------------------------
# Helpers
# -----------------------------
def get_api_key():
    
    try:
        with open("config.json", "r") as f:
            cfg = json.load(f)
            return cfg.get(f"{code}", "")
    except Exception:
        return ""

def ensure_event_loop():
    # Streamlit thường có loop sẵn, cần nest_asyncio khi chạy trong notebook/thread
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except Exception:
                pass
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

def run_async(coro):
    ensure_event_loop()
    return asyncio.run(coro)

def fmt_number(v, nd=0, default="N/A"):
    if isinstance(v, (int, float)) and pd.notna(v):
        return f"{v:,.{nd}f}"
    return default

def safe_percent(v, nd=1):
    try:
        return f"{float(v):.{nd}f}%"
    except Exception:
        return "N/A"


# -----------------------------
# UI Config
# -----------------------------
st.set_page_config(
    page_title="Golden Key - PE Percentile Valuation (AI)",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🎯 Golden Key | Định giá PE")
if not IMPORT_OK:
    st.error(f"❌ Lỗi import modules: {IMPORT_ERR}")
    st.stop()

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.header("⚙️ Cấu hình")
    code = st.text_input("Gemini API Key", value="", type="password")
    default_api_key = get_api_key()
    API_KEY = default_api_key
    model_name = "gemini-2.0-flash"

    symbol = st.text_input("Mã cổ phiếu (HOSE)", value="ACB").strip().upper()

    col_a, col_b = st.columns(2)
    with col_a:
        test_btn = st.button("🔍 Test dữ liệu", use_container_width=True)
    with col_b:
        run_btn = st.button("🎯 Phân tích AI", type="primary", use_container_width=True)


def load_core_data(sym: str):
    pe_api = PEAPI(sym)
    price_df = pe_api.get_price_history()            # descending by time
    ratio_df = pe_api.get_ratio_data()               # quarterly
    pe_df = pe_api.compute_pe_trailing()             # merged with EPS_nam + PEtrailing
    stats = pe_api.calculate_pe_distribution_stats(pe_df)  # distribution statistics
    return pe_api, price_df, ratio_df, pe_df, stats

def extract_eps_ttm(pe_df: pd.DataFrame) -> float | None:
    try:
        return float(pe_df.iloc[0]["EPS_nam"])
    except Exception:
        return None

def current_close(pe_df: pd.DataFrame) -> float | None:
    try:
        return float(pe_df.iloc[0]["close"])
    except Exception:
        return None

def current_petrailing(pe_df: pd.DataFrame) -> float | None:
    try:
        return float(pe_df.iloc[0]["PEtrailing"])
    except Exception:
        return None

def show_distribution_metrics(stats: dict, pe_df: pd.DataFrame):
    st.subheader("📊 Phân phối PE (mô tả)")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("PE hiện tại", f"{stats.get('current_pe', 'N/A')}")
    with c2:
        pct = stats.get("current_percentile")
        pct_str = f"{round(pct,1)}%" if isinstance(pct, (int,float)) else "N/A"
        st.metric("Percentile hiện tại", pct_str)
    with c3:
        st.metric("PE Median (P75)", f"{stats.get('percentile_75', 'N/A')}")
    with c4:
        cur_px = current_close(pe_df)
        st.metric("Giá hiện tại", f"{fmt_number(cur_px, 0) if cur_px is not None else 'N/A'}")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.metric("Mean", f"{stats.get('mean','N/A')}")
    with c6:
        st.metric("Std", f"{stats.get('std','N/A')}")
    with c7:
        st.metric("Z-score hiện tại", f"{stats.get('current_z_score','N/A')}")
    with c8:
        st.metric("CV", f"{stats.get('coefficient_of_variation','N/A')}")


   

if run_btn:
    if not API_KEY:
        st.error("❌ Vui lòng nhập lại code.")
        st.stop()
    if not symbol:
        st.error("❌ Vui lòng nhập mã hợp lệ.")
        st.stop()

    status = st.empty()
    try:

        pe_api, price_df, ratio_df, pe_df, stats = load_core_data(symbol)

        ctx = MarketContext(symbol=symbol)
        agent = PEValuationAnalyst(api_key=API_KEY, model=model_name)
        status.text("🎯 Phân tích định giá dựa trên phân phối PE (AI)...")
        resp = run_async(agent.analyze(ctx))
        status.text("✅ Hoàn tất phân tích")

        show_distribution_metrics(stats, pe_df)

        st.subheader(f"🧠 Kết quả phân tích cho {symbol}")
        st.write(resp.recommendation)
        
       

        st.subheader("🎯 Định giá theo các kịch bản")
        if resp.content:
                data = resp.content
                if "quick_conclusion" in data:
                    st.info(f"💡 {data['quick_conclusion']}")

                pe_val = data.get("pe_valuation", {}) or {}
                
                   


        # Raw JSON
        st.subheader("📈 Kịch bản (AI)")
        scenarios = resp.content.get("pe_valuation", {}).get("scenarios", {}) if resp.content else {}
        if scenarios:
                rows = []
                for name, sc in scenarios.items():
                    tp_val = sc.get("target_price", "N/A")
                    tp_str = fmt_number(tp_val, 0) if isinstance(tp_val, (int,float)) else str(tp_val)

                    rows.append({
                        "Kịch bản": name.title(),
                        "PE Target (AI)": sc.get("pe", "N/A"),
                        "Giá mục tiêu (AI)": tp_str,
                        "Xác suất (AI)": sc.get("probability","N/A"),
                        "Lý do (rút gọn)": sc.get("rationale","")
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True)
                st.caption("Các mốc mục tiêu, xác suất và lý do đều do AI suy luận từ phân phối PE và thống kê lịch sử.")

    except Exception as e:
        progress.empty()
        status.empty()
        st.error(f"❌ Lỗi phân tích: {e}")
        with st.expander("Chi tiết lỗi"):
            st.code(traceback.format_exc())
