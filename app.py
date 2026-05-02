import streamlit as st
import plotly.graph_objects as go
from analysis import fetch_data, apply_indicators, generate_signals, get_latest_price

st.set_page_config(page_title="High-Frequency Market Analyzer", layout="wide")

st.title("High-Frequency Market Analyzer & Trading Signal")

# Sidebar
st.sidebar.header("Settings")

# Asset Selection
asset_type = st.sidebar.selectbox("Asset Type", ["Crypto", "NSE Stocks", "US Stocks"])
symbol_map = {
    "Crypto": ["BTC-USD", "ETH-USD"],
    "NSE Stocks": ["RELIANCE.NS", "TCS.NS", "INFY.NS"],
    "US Stocks": ["AAPL", "MSFT", "TSLA", "GOOGL"]
}
symbol = st.sidebar.selectbox("Symbol", symbol_map[asset_type])

# Timeframe Selection
interval = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m", "1h"])
# Period mapping based on interval
period_map = {
    "1m": "7d", # yfinance max for 1m is 7d
    "5m": "60d",
    "15m": "60d",
    "1h": "730d"
}
period = period_map[interval]

# Trade Monitor
st.sidebar.markdown("---")
st.sidebar.header("Trade Monitor")
entry_price = st.sidebar.number_input("Entry Price", value=0.0, step=0.1)

st.write(f"Fetching data for {symbol} ({interval})...")

df = fetch_data(symbol, interval, period)

if df.empty:
    st.error("Failed to fetch data. Try a different symbol or timeframe.")
else:
    df = apply_indicators(df)

    if len(df) < 30:
        st.warning("Not enough data to calculate all indicators.")
    else:
        latest_price = get_latest_price(df)
        signal = generate_signals(df)

        # Trade Monitor Logic
        if entry_price > 0:
            pnl_pct = ((latest_price - entry_price) / entry_price) * 100
            st.sidebar.write(f"Current Price: **{latest_price:.2f}**")
            st.sidebar.write(f"P&L: **{pnl_pct:.2f}%**")

            if pnl_pct >= 2.0:
                st.sidebar.success("SELL NOW! Profit hit 2% or more.")
            elif pnl_pct <= -1.0:
                st.sidebar.error("SELL NOW! Loss hit 1% or more.")

        # Signal Dashboard
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Latest Price", f"{latest_price:.2f}")
        with col2:
            signal_color = "green" if "BUY" in signal else "red" if signal == "SELL" else "gray"
            st.markdown(f"### Current Signal: <span style='color:{signal_color}'>{signal}</span>", unsafe_allow_html=True)
        with col3:
            # We suggest entry/exit based on the signal and current price
            if "BUY" in signal:
                st.metric("Suggested Entry Point", f"{latest_price:.2f}")
            elif signal == "SELL":
                st.metric("Suggested Exit Point", f"{latest_price:.2f}")
            else:
                st.metric("Suggested Action", "WAIT")

        # Visuals: Plotly Candlestick with SMAs and BB
        st.markdown("### Chart")

        fig = go.Figure()

        # Candlestick
        fig.add_trace(go.Candlestick(x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name='Price'))

        # SMAs
        sma7_col = [col for col in df.columns if 'SMA_7' in col][0]
        sma30_col = [col for col in df.columns if 'SMA_30' in col][0]

        fig.add_trace(go.Scatter(x=df.index, y=df[sma7_col], line=dict(color='orange', width=1.5), name='SMA 7 (Fast)'))
        fig.add_trace(go.Scatter(x=df.index, y=df[sma30_col], line=dict(color='blue', width=1.5), name='SMA 30 (Slow)'))

        # Bollinger Bands
        bbu_col = [col for col in df.columns if 'BBU' in col][0]
        bbl_col = [col for col in df.columns if 'BBL' in col][0]

        fig.add_trace(go.Scatter(x=df.index, y=df[bbu_col], line=dict(color='rgba(200, 200, 200, 0.5)', width=1), name='Upper BB'))
        fig.add_trace(go.Scatter(x=df.index, y=df[bbl_col], line=dict(color='rgba(200, 200, 200, 0.5)', width=1), fill='tonexty', fillcolor='rgba(200, 200, 200, 0.1)', name='Lower BB'))

        fig.update_layout(xaxis_rangeslider_visible=False, height=600, template="plotly_dark")

        st.plotly_chart(fig, width='stretch')
