import streamlit as st
from src.data.price_api import PriceAPI
from src.data.pe_api import PEAPI
from src.data.fundamental_api import Fundamental

import streamlit as st
from streamlit_gsheets import GSheetsConnection


st.title("Test VNStockAPI")

symbol = st.text_input("Symbol", value="SSI")

price = PriceAPI(symbol)
fundamental = Fundamental(symbol)
pe = PEAPI(symbol)


st.subheader("Price History")
st.dataframe(price.get_enhanced_price_history())
st.subheader("Index History")
st.dataframe(price.get_index_history())
st.subheader("Indicator")
st.dataframe(price.get_comprehensive_analysis())
st.subheader("Cash Flow")
st.dataframe(fundamental.get_cash_flow())
st.subheader("Incomestatement")
st.dataframe(fundamental.get_income_statement())
st.subheader("Ratio")
st.dataframe(fundamental.get_ratio())
st.subheader("Balance Sheet")
st.dataframe(fundamental.get_balance_sheet())

st.subheader("PE Realtime")
st.dataframe(pe.compute_pe_trailing())

st.subheader("Distribute Stats of PE Realtime")
st.dataframe(pe.calculate_pe_distribution_stats())



