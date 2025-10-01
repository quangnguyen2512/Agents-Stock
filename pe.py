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
    # 1) st.secrets
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    # 2) env
    env_key = os.getenv("GEMINI_API_KEY", "")
    if env_key:
        return env_key
    # 3) config.json
    try:
        with open("config.json", "r") as f:
            cfg = json.load(f)
            return cfg.get("GEMINI_API_KEY", "")
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

# Percentiles 25–99
PERCENTILE_LEVELS = [25,30,40,50,60,70,75,80,90,95,99]

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
    default_api_key = get_api_key()
    if not default_api_key:
        st.warning("⚠️ Chưa tìm thấy GEMINI_API_KEY (secrets/env/config.json)")

    API_KEY = st.text_input("Gemini API Key", value=default_api_key, type="password")
    model_name = "gemini-2.0-flash"

    st.markdown("---")
    symbol = st.text_input("Mã cổ phiếu (HOSE)", value="ACB").strip().upper()

    col_a, col_b = st.columns(2)
    with col_a:
        test_btn = st.button("🔍 Test dữ liệu", use_container_width=True)
    with col_b:
        run_btn = st.button("🎯 Phân tích AI", type="primary", use_container_width=True)

st.markdown("---")

# -----------------------------
# Data access
# -----------------------------
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

def percentile_table_from_stats(stats: dict, eps_ttm: float | None):
    # Bảng minh hoạ đầy đủ 25–99
    rows = []
    for p in PERCENTILE_LEVELS:
        pe_p = stats.get(f"percentile_{p}")
        if isinstance(pe_p, (int, float)):
            if isinstance(eps_ttm, (int, float)) and eps_ttm > 0:
                tp_val = pe_p * eps_ttm
                tp = f"{tp_val:,.0f}"
            else:
                tp = "N/A"
        else:
            tp = "N/A"
        rows.append({"Percentile": f"P{p}", "PE": pe_p, "Target": tp})
    return pd.DataFrame(rows)

def nearest_percentile_pe(stats: dict, current_pe: float | None) -> tuple[int, float | None]:
    
    
    current_pe = stats.get("current_pe", None)
    best_p, best_pe, best_dist = None, None, float("inf")
    for p in PERCENTILE_LEVELS:
        pe_p = stats.get(f"percentile_{p}")
        if isinstance(pe_p, (int, float)) and pd.notna(pe_p) and isinstance(current_pe, (int, float)):
            dist = abs(pe_p - current_pe)
            if dist < best_dist:
                best_p, best_pe, best_dist = p, pe_p, dist

    return best_p, best_pe

def adjacent_percentiles(base_p: int) -> tuple[int, int]:
    """
    Bear = phân vị thấp hơn liền kề trong PERCENTILE_LEVELS (biên dưới giữ 25)
    Bull = phân vị cao hơn liền kề (biên trên giữ 99)
    """
    idx = PERCENTILE_LEVELS.index(base_p) if base_p in PERCENTILE_LEVELS else PERCENTILE_LEVELS.index(50)
    bear_idx = max(0, idx - 1)
    bull_idx = min(len(PERCENTILE_LEVELS) - 1, idx + 1)
    return PERCENTILE_LEVELS[bear_idx], PERCENTILE_LEVELS[bull_idx]

def compute_prices_from_percentiles(stats: dict, eps_ttm: float | None, base_p: int, base_pe: float | None):
    """
    Tạo bộ 3 mốc: bear/base/bull dựa trên percentiles liền kề với base.
    Giá = PE × EPS_TTM.
    """
    bear_p, bull_p = adjacent_percentiles(base_p)
    pe_bear = stats.get(f"percentile_{bear_p}", None)
    pe_bull = stats.get(f"percentile_{bull_p}", None)

    def price_from_pe(pe):
        if isinstance(pe, (int, float)) and isinstance(eps_ttm, (int, float)) and eps_ttm > 0:
            return pe * eps_ttm
        return None

    return {
        "bear": {"percentile": bear_p, "pe": pe_bear, "target_price": price_from_pe(pe_bear)},
        "base": {"percentile": base_p, "pe": base_pe, "target_price": price_from_pe(base_pe)},
        "bull": {"percentile": bull_p, "pe": pe_bull, "target_price": price_from_pe(pe_bull)},
    }

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
        st.metric("PE Median (P50)", f"{stats.get('percentile_50', 'N/A')}")
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

    # Bảng percentile minh hoạ 25–99
    eps_ttm = extract_eps_ttm(pe_df)
    dfp = percentile_table_from_stats(stats, eps_ttm)
    st.dataframe(dfp, use_container_width=True)
   
# -----------------------------
# Test data flow
# -----------------------------
if test_btn:
    if not symbol:
        st.error("❌ Vui lòng nhập mã hợp lệ.")
    else:
        try:
            with st.spinner("Đang tải dữ liệu và thống kê..."):
                pe_api, price_df, ratio_df, pe_df, stats = load_core_data(symbol)
            st.success(f"✅ Dữ liệu OK — price: {len(price_df)} | ratio: {len(ratio_df)} | merged: {len(pe_df)} | metrics: {len(stats)}")
            show_distribution_metrics(stats, pe_df)
        except Exception as e:
            st.error(f"❌ Lỗi test dữ liệu: {e}")
            with st.expander("Chi tiết lỗi"):
                st.code(traceback.format_exc())

# -----------------------------
# AI Analysis flow
# -----------------------------
if run_btn:
    if not API_KEY:
        st.error("❌ Thiếu GEMINI_API_KEY.")
        st.stop()
    if not symbol:
        st.error("❌ Vui lòng nhập mã hợp lệ.")
        st.stop()

    progress = st.progress(0)
    status = st.empty()
    try:
        # B1: dữ liệu nền
        status.text("🔍 Tải dữ liệu và thống kê nền...")
        progress.progress(25)
        pe_api, price_df, ratio_df, pe_df, stats = load_core_data(symbol)

        # B2: agent
        status.text("🤖 Khởi tạo AI agent...")
        progress.progress(50)
        ctx = MarketContext(symbol=symbol)
        agent = PEValuationAnalyst(api_key=API_KEY, model=model_name)

        # B3: gọi AI
        status.text("🎯 Phân tích định giá dựa trên phân phối PE (AI)...")
        progress.progress(75)
        resp = run_async(agent.analyze(ctx))

        progress.progress(100)
        status.text("✅ Hoàn tất phân tích")

        # Nền phân phối
        st.markdown("---")
        show_distribution_metrics(stats, pe_df)

        # Minh hoạ theo phân vị 25–99 (không ghi đè kết quả AI)
    
        st.markdown("---")
        st.subheader(f"🧠 Kết quả phân tích cho {symbol}")
        st.write(resp.recommendation)
        
       
        # Chi tiết AI
        c1, c2 = st.columns([1,1])
        with c1:
            st.subheader("🎯 Định giá theo các kịch bản")
            if resp.content:
                data = resp.content
                if "quick_conclusion" in data:
                    st.info(f"💡 {data['quick_conclusion']}")

                pe_val = data.get("pe_valuation", {}) or {}
                
                   
        with c2:
            if pe_val:
                    fair_value_pe = pe_val.get("fair_value_pe", "N/A")
                    fair_value_pe = fmt_number(fair_value_pe, 0) if isinstance(fair_value_pe, (int,float)) else str(fair_value_pe)

                    st.metric( "PE hợp lý",pe_val.get("fair_value_pe"))
                    # Định dạng giá hợp lý an toàn
                    fair_price_val = pe_val.get("fair_price", "N/A")
                    fair_price_str = fmt_number(fair_price_val, 0) if isinstance(fair_price_val, (int,float)) else str(fair_price_val)
                    st.metric("Giá hợp lý (AI):", fair_price_str)

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
