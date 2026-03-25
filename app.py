import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from data_fetch import get_prices, get_volume_dollar, get_market_caps, format_money, ASSET_CLASSES, TICKER_NAMES
import datetime
import pandas as pd

st.set_page_config(page_title="Global Asset Liquidity & Flows Dashboard", layout="wide")

st.title("🌍 Global Asset Class Liquidity & Flows Dashboard")
st.markdown("Daily refresh using free yfinance data • Focus: where money is moving")

# Sidebar
st.sidebar.header("Controls")
start_date = st.sidebar.date_input("Start Date", datetime.date(2025, 1, 1))
refresh = st.sidebar.button("🔄 Refresh Data")

# Initialize session state safely
if 'data' not in st.session_state:
    st.session_state.data = {}

if refresh or not st.session_state.data:
    st.cache_data.clear()
    with st.spinner("Fetching latest market data from Yahoo Finance..."):
        prices = get_prices(start_date=start_date)
        liquidity = get_volume_dollar(start_date=start_date.strftime("%Y-%m-%d"))
        market_caps = get_market_caps()
        
        st.session_state.data = {
            'prices': prices,
            'liquidity': liquidity,
            'market_caps': market_caps
        }

data = st.session_state.data

tab1, tab2, tab3, tab4 = st.tabs(["📈 Prices & Trends", "💰 Liquidity (Dollar Volume)", "Flows & Rotations", "🏦 Market Cap"])

# TAB 1: Prices (unchanged - already good)
with tab1:
    st.subheader("Price Trends by Asset Class")
    for cls, df in data['prices'].items():
        if not df.empty:
            st.write(f"**{cls}**")
            fig = px.line(df, title=f"{cls} Price Trends")
            if cls == 'Bitcoin':
                fig = go.Figure()
                for col in df.columns:
                    if 'Bitcoin USD' in col:
                        fig.add_trace(go.Scatter(x=df.index, y=df[col], name=col, mode='lines'))
                    else:
                        fig.add_trace(go.Scatter(x=df.index, y=df[col], name=col, mode='lines', yaxis='y2'))
                fig.update_layout(
                    yaxis=dict(title='Bitcoin Price (USD)'),
                    yaxis2=dict(title='IBIT Price (USD)', overlaying='y', side='right'),
                    height=500
                )
            st.plotly_chart(fig, width='stretch')

# TAB 2: Liquidity - FIXED
with tab2:
    st.subheader("Daily Liquidity Proxy (Dollar Volume Traded)")
    liq_df = data['liquidity'].tail(90)
    liq_billions = liq_df / 1e9

    fig = px.line(liq_billions, title="Liquidity Trends – Higher = More Money Moving")
    fig.update_layout(yaxis_title="Dollar Volume (Billions USD)", height=600)
    fig.update_yaxes(tickformat="$,.2f")
    for trace in fig.data:
        trace.update(hovertemplate="%{y:$,.2f}B<extra></extra>")

    st.plotly_chart(fig, width='stretch')

    # Clean & Complete Table
    st.subheader("Latest Daily Liquidity by Asset Class")
    latest = liq_df.iloc[-1]
    latest_billions = latest / 1e9

    latest_df = pd.DataFrame({
        "Asset Class": [name.replace("_liquidity", "") for name in latest.index],
        "Dollar Volume (Billions)": [round(v, 2) for v in latest_billions.values],
        "Scaled": [format_money(v) for v in latest.values]
    }).sort_values("Dollar Volume (Billions)", ascending=False)

    st.dataframe(latest_df, width='stretch', hide_index=True)

# TAB 3 & TAB 4 remain the same as before (Flows placeholder + Market Cap)

with tab3:
    st.subheader("Flows & Rotations (MVP – expanding soon)")
    st.write("Next step: Add real weekly ICI net flows + ETF shares-outstanding tracking.")

with tab4:
    st.subheader("Latest Market Capitalization")
    for cls, caps in data.get('market_caps', {}).items():
        if caps:
            df = pd.DataFrame(list(caps.items()), columns=["Asset", "Market Cap"])
            df["Market Cap (Billions)"] = (df["Market Cap"] / 1e9).round(2)
            df["Scaled"] = df["Market Cap"].apply(format_money)
            st.write(f"**{cls}**")
            st.dataframe(df[["Asset", "Market Cap (Billions)", "Scaled"]].sort_values("Market Cap (Billions)", ascending=False),
                         width='stretch', hide_index=True)

st.markdown("---")
st.caption("Data: yfinance (free) • Bitcoin often shows highest liquidity due to 24/7 trading & ETF activity")
