import streamlit as st
import pandas as pd
import krakenex
import os
import numpy as np
import plotly.express as px
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# --- 1. INITIALIZATION ---
st.set_page_config(page_title="Sentinel V5.57 | Command & SOP", layout="wide")
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
k = krakenex.API(key=os.getenv('KRAKEN_API_KEY'), secret=os.getenv('KRAKEN_API_SECRET'))

# --- 2. CONFIGURATION ---
BENCHMARKS = {'RENDER': 1.777, 'TAO': 258.39, 'ETH': 2325.6}
TARGETS = {'RENDER': 65.0, 'TAO': 17.5, 'ETH': 17.5}
ASSET_MAP = {'RENDER': 'RENDER', 'TAO': 'TAO', 'XETH': 'ETH', 'ZUSD': 'CASH'}
LEVELS = {
    'RENDER': {'support': 1.66, 'resistance': 1.93},
    'TAO': {'support': 259.00, 'resistance': 288.00},
    'ETH': {'support': 2250.00, 'resistance': 2750.00}
}

# --- 3. PERSISTENT STORAGE PATHING ---
BASE_DIR = Path(__file__).resolve().parent
HWM_FILE = BASE_DIR / "hwm_record.txt"
JOURNAL_FILE = BASE_DIR / "trade_journal.csv"

def log_trade(asset, price, action):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame([[timestamp, asset, action, price]], columns=['Timestamp', 'Asset', 'Action', 'Price'])
    df.to_csv(JOURNAL_FILE, mode='a', header=not os.path.exists(JOURNAL_FILE), index=False)

def get_persistent_hwm(current_val):
    if not os.path.exists(HWM_FILE):
        try:
            with open(HWM_FILE, "w") as f:
                f.write(str(current_val))
            return current_val
        except Exception as e:
            st.error(f"Storage Error: {e}")
            return current_val
    
    with open(HWM_FILE, "r") as f:
        try:
            content = f.read().strip()
            saved_hwm = float(content) if content else current_val
        except:
            saved_hwm = current_val
            
    if current_val > saved_hwm:
        with open(HWM_FILE, "w") as f:
            f.write(str(current_val))
        return current_val
    
    return saved_hwm

# --- 4. DATA ENGINE ---
@st.cache_data(ttl=60)
def fetch_intelligence():
    try:
        balance = k.query_private('Balance')['result']
        ticker = k.query_public('Ticker', {'pair': 'RENDERUSD,TAOUSD,ETHUSD'})['result']
        portfolio, stats = {}, {}
        for k_name, name in ASSET_MAP.items():
            if name == 'CASH': continue
            t_key = 'XETHZUSD' if name == 'ETH' else f"{name}USD"
            t_data = ticker[t_key]
            price = float(t_data['c'][0])
            qty = float(balance.get(k_name, 0))
            portfolio[name] = {'price': price, 'val': qty * price, 'qty': qty}
            stats[name] = {'hi': float(t_data['h'][1]), 'lo': float(t_data['l'][1])}
        return portfolio, float(balance.get('ZUSD', 0)), stats
    except: return None, 0.0, None

# --- 5. UI RENDER ---
st.title("🛡️ SENTINEL V5.57 | COMMAND & SOP")

portfolio, cash, stats = fetch_intelligence()

if portfolio:
    total_val = sum(v['val'] for v in portfolio.values()) + cash
    hwm = get_persistent_hwm(total_val)
    drawdown = ((total_val - hwm) / hwm) * 100 if hwm > 0 else 0

    # --- ROW 1: CORE METRICS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PORTFOLIO VALUE", f"${total_val:,.2f}", delta=f"{drawdown:.2f}% vs Peak", delta_color="inverse")
    m2.metric("HIGH WATER MARK", f"${hwm:,.2f}")
    m3.metric("95% VaR (Daily)", f"${total_val * 0.027:,.2f}")
    m4.metric("BETA", "0.27")

    # --- ROW 2: ASSET TRACKER & HEATMAP ---
    st.divider()
    dist_col1, dist_col2 = st.columns([1, 1])
    with dist_col1:
        st.subheader("📊 ASSET DISTRIBUTION")
        dist_data = {asset: data['val'] for asset, data in portfolio.items()}
        dist_data['CASH'] = cash
        df_dist = pd.DataFrame(list(dist_data.items()), columns=['Asset', 'Value'])
        fig = px.pie(df_dist, values='Value', names='Asset', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    with dist_col2:
        st.subheader("🌡️ % P&L HEATMAP")
        for asset in TARGETS.keys():
            pct_change = ((portfolio[asset]['price'] - BENCHMARKS[asset]) / BENCHMARKS[asset]) * 100
            color = "#2ecc71" if pct_change > 0 else "#e74c3c"
            st.markdown(f"""<div style="background-color:{color}; padding:12px; border-radius:5px; margin-bottom:8px; color:white; text-align:center;">
                <strong>{asset}: {pct_change:+.2f}%</strong></div>""", unsafe_allow_html=True)

    # --- ROW 3: FINANCIAL PERFORMANCE LEDGER ---
    st.subheader("💰 FINANCIAL PERFORMANCE LEDGER")
    perf_rows = []
    for asset in TARGETS.keys():
        p, cost = portfolio[asset]['price'], BENCHMARKS[asset]
        pnl_val = (p - cost) * portfolio[asset]['qty']
        pnl_pct = ((p - cost) / cost) * 100
        perf_rows.append({"Asset": asset, "Price": f"${p:,.2f}", "Avg Cost": f"${cost:,.2f}", "Unrealized P&L": f"${pnl_val:,.2f}", "% P&L": f"{pnl_pct:+.2f}%"})
    st.table(pd.DataFrame(perf_rows))

    # --- ROW 4: REBALANCING & DRIFT ---
    st.divider()
    st.subheader("⚖️ REBALANCING & DRIFT LEDGER")
    drift_data = []
    for asset, target in TARGETS.items():
        v = portfolio[asset]['val']
        curr_alloc = (v / total_val) * 100
        drift_data.append({"Asset": asset, "Target %": f"{target}%", "Current %": f"{curr_alloc:.2f}%", "Drift %": f"{curr_alloc - target:+.2f}%", "Rebalance Amt": f"${(total_val*(target/100))-v:,.2f}"})
    st.table(pd.DataFrame(drift_data))

    # --- ROW 5: ASSET RATINGS & DYNAMIC ENTRY ---
    st.divider()
    st.subheader("🎯 ASSET RATINGS & DYNAMIC ENTRY TARGETS")
    strat_data = []
    for asset, target in TARGETS.items():
        alloc = (portfolio[asset]['val'] / total_val) * 100
        rating = "UNDERWEIGHT" if alloc < target else "OVERWEIGHT"
        dyn_entry = LEVELS[asset]['support'] * 1.05
        pos = "🟢 ACCUMULATION" if portfolio[asset]['price'] <= dyn_entry else "🟡 HOLD"
        if portfolio[asset]['price'] >= LEVELS[asset]['resistance'] * 0.98: pos = "🔴 RESISTANCE"
        strat_data.append({"Asset": asset, "Strategic": rating, "Position": pos, "Suggested Entry": f"${dyn_entry:,.2f}", "Action": "🔥 Prime Entry Zone" if pos == "🟢 ACCUMULATION" else "⏳ Wait for Pullback"})
    st.table(pd.DataFrame(strat_data))

    # --- ROW 6: SESSION CHECKLIST & AUTO-JOURNAL ---
    st.divider()
    st.subheader("✅ SESSION TRADE CHECKLIST")
    if 'trades_done' not in st.session_state:
        st.session_state.trades_done = {asset: False for asset in TARGETS.keys()}
    chk_cols = st.columns(3)
    for i, asset in enumerate(TARGETS.keys()):
        with chk_cols[i]:
            checked = st.checkbox(f"Log {asset} Trade", value=st.session_state.trades_done[asset], key=f"log_{asset}")
            if checked and not st.session_state.trades_done[asset]:
                log_trade(asset, portfolio[asset]['price'], "COMPLETED")
                st.session_state.trades_done[asset] = True
                st.toast(f"✅ {asset} Logged to CSV")

    # --- ROW 7: EXECUTION DIRECTIVES ---
    st.subheader("⚡ FINAL EXECUTION DIRECTIVES")
    d_cols = st.columns(3)
    for i, asset in enumerate(TARGETS.keys()):
        var_need = (total_val * (TARGETS[asset]/100)) - portfolio[asset]['val']
        with d_cols[i]:
            if st.session_state.trades_done[asset]:
                st.success(f"**{asset} SESSION COMPLETE**")
            elif var_need > 50:
                st.info(f"**{asset} BUY PLAN**\n• Buy ${var_need*0.33:,.2f} Market\n• Limit at ${LEVELS[asset]['support']*1.05:.2f}")
            else: st.success(f"**{asset} BALANCED**")

    # --- ROW 8: COMMAND LEGEND (SOP) ---
    st.divider()
    with st.expander("📖 VIEW COMMAND LEGEND & SOP"):
        l_col1, l_col2 = st.columns(2)
        with l_col1:
            st.markdown("### 🗺️ Position Legend")
            st.write("**🟢 ACCUMULATION:** Price at the Floor. High probability buying zone.")
            st.write("**🟡 HOLD:** Price in Mid-range. Neutral territory; wait for levels.")
            st.write("**🔴 RESISTANCE:** Price at the Ceiling. Risk of reversal; avoid buying.")
        with l_col2:
            st.markdown("### ⚡ Action Legend")
            st.write("**🔥 Prime Entry Zone:** System is Underweight + Price is in Accumulation. **Execute Strike.**")
            st.write("**⏳ Wait for Pullback:** Market is too expensive or position is full. **Exercise Patience.**")
            st.write("**✅ SESSION COMPLETE:** Trade logged to CSV. **Audit Trail locked.**")

else:
    st.error("🛑 API Connection Failed.")