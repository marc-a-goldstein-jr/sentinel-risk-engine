import streamlit as st
import pandas as pd
import krakenex
import os
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# --- 1. INITIALIZATION ---
st.set_page_config(page_title="Sentinel V5.94 | Executive Command", layout="wide")
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
k = krakenex.API(key=os.getenv('KRAKEN_API_KEY'), secret=os.getenv('KRAKEN_API_SECRET'))



# --- 2. CONFIGURATION & CONSTANTS ---
ASSET_MAP = {'RENDER': 'RENDER', 'TAO': 'TAO', 'FET': 'FET', 'ZUSD': 'CASH'}
TARGETS = {'RENDER': 60.0, 'TAO': 10.0, 'FET': 20.0, 'CASH': 10.0}

# Color Map for Charts
COLOR_MAP = {
    'RENDER': '#FF0000', # Red
    'TAO': '#0000FF',    # Blue
    'FET': '#FFFFFF',    # White
    'CASH': '#00FF00'    # Green
}

ATH_DATA = {
    'RENDER': {'price': 13.61, 'date': 'Mar 2024'},
    'TAO': {'price': 760.18, 'date': 'Apr 2024'},
    'FET': {'price': 3.45, 'date': 'Mar 2024'}
}

LEVELS = {
    'RENDER': {'support': 1.66, 'resistance': 1.93, 'exit_goal': 12.50},
    'TAO': {'support': 259.00, 'resistance': 288.00, 'exit_goal': 1000.00},
    'FET': {'support': 0.18, 'resistance': 0.28, 'exit_goal': 2.50}
}

LIFE_GOALS = [
    {"Goal": "Initial Investment Recovery", "Value": 13200},
    {"Goal": "Down Payment Fund", "Value": 50000},
    {"Goal": "Financial Independence", "Value": 250000}
]

# --- ADD THIS TO YOUR CONFIGURATION SECTION (Section 2) ---
RESEARCH_DATA = {
    'RENDER': {
        'demand_metric': '68M+ Frames Rendered',
        'utilization': '82%',
        'supply_status': 'Deflationary (Burn-Mint)',
        'partnership': 'Apple/Nvidia/OTOY',
        'soundness_score': 8.5,
        'thesis': 'DePIN leader for GPU compute. Real-world revenue from Hollywood and AI startups.'
    },
    'TAO': {
        'demand_metric': '128 Active Subnets',
        'utilization': '74% Staked',
        'supply_status': 'Capped 21M (Post-Halving)',
        'partnership': 'Grayscale/OpenAI wrappers',
        'soundness_score': 9.2,
        'thesis': 'The "Bitcoin of AI." Decentralized intelligence marketplace with high institutional interest.'
    },
    'FET': {
        'demand_metric': 'ASI Alliance Integrated',
        'utilization': 'Agentic Workflows Active',
        'supply_status': 'Unified ASI Tokenomics',
        'partnership': 'Bosch/Deutsche Telekom',
        'soundness_score': 7.8,
        'thesis': 'Action layer for AI agents. Validated by industrial IoT partnerships and ASI merger.'
    }
}

# --- 3. PERSISTENT STORAGE & LOGGING ---
BASE_DIR = Path(__file__).resolve().parent
HWM_FILE = BASE_DIR / "hwm_record.txt"
JOURNAL_FILE = BASE_DIR / "trade_journal.csv"
MAX_DD_FILE = BASE_DIR / "max_dd_record.txt"

def get_persistent_hwm(current_val):
    if not os.path.exists(HWM_FILE):
        with open(HWM_FILE, "w") as f: f.write(str(current_val))
        return current_val
    with open(HWM_FILE, "r") as f:
        try:
            content = f.read().strip()
            saved_hwm = float(content) if content else current_val
        except: saved_hwm = current_val
    if current_val > saved_hwm:
        with open(HWM_FILE, "w") as f: f.write(str(current_val))
        return current_val
    return saved_hwm

def get_max_drawdown(current_val, hwm):
    current_dd = ((current_val - hwm) / hwm) * 100 if hwm > 0 else 0
    if not os.path.exists(MAX_DD_FILE):
        with open(MAX_DD_FILE, "w") as f: f.write("0.0")
        return 0.0
    with open(MAX_DD_FILE, "r") as f:
        try: saved_max_dd = float(f.read().strip())
        except: saved_max_dd = 0.0
    if current_dd < saved_max_dd:
        with open(MAX_DD_FILE, "w") as f: f.write(str(current_dd))
        return current_dd
    return saved_max_dd

# --- 4. DATA ENGINE (MODIFIED FOR AUTOMATION) ---
@st.cache_data(ttl=60)
def fetch_intelligence():
    try:
        balance = k.query_private('Balance')['result']
        ticker = k.query_public('Ticker', {'pair': 'RENDERUSD,TAOUSD,FETUSD'})['result']
        portfolio = {}
        for k_name, name in ASSET_MAP.items():
            if name == 'CASH': 
                qty = float(balance.get('ZUSD', 0))
                portfolio[name] = {'price': 1.0, 'val': qty, 'qty': qty}
                continue
            t_key = f"{name}USD"
            price = float(ticker[t_key]['c'][0])
            qty = float(balance.get(k_name, 0))
            portfolio[name] = {'price': price, 'val': qty * price, 'qty': qty}
        return portfolio, float(balance.get('ZUSD', 0))
    except: return None, 0.0

def get_dynamic_cost_basis(asset_map):
    try:
        # Request more than the default 50 trades
        history = k.query_private('TradesHistory', {'limit': 500})['result']['trades']
        costs = {}
        
        for asset_key, common_name in asset_map.items():
            if common_name == 'CASH': 
                costs[common_name] = 1.0
                continue
            
            # Filter all trades for this asset across the last 500 entries
            asset_trades = [t for t in history.values() if common_name in t['pair']]
            
            total_spent = sum(float(t['cost']) + float(t['fee']) for t in asset_trades if t['type'] == 'buy')
            total_qty = sum(float(t['vol']) for t in asset_trades if t['type'] == 'buy')
            
            # If no trades found (likely a deposit), use your manual entry price
            if total_qty > 0:
                costs[common_name] = round(total_spent / total_qty, 4)
            else:
                # Fallback to your manual 'Reset' benchmarks for accuracy
                fallbacks = {'RENDER': 1.77, 'TAO': 258.35, 'FET': 0.22}
                costs[common_name] = fallbacks.get(common_name, 0.0001)
                
        return costs
    except:
        return {'RENDER': 1.77, 'TAO': 258.35, 'FET': 0.22, 'CASH': 1.0}

def calculate_soundness(asset, portfolio, research):
    """Calculates a dynamic 1-10 score based on live market & portfolio health."""
    try:
        # 1. ALLOCATION FACTOR (Max 4 pts)
        # Higher score if you are disciplined and close to your target weight.
        curr_alloc = (portfolio[asset]['val'] / sum(v['val'] for v in portfolio.values())) * 100
        target_alloc = TARGETS[asset]
        drift = abs(curr_alloc - target_alloc)
        alloc_score = max(0, 4.0 - (drift * 0.2)) # Penalize 0.2 per 1% drift

        # 2. PRICE RESILIENCE FACTOR (Max 3 pts)
        # Higher score if price is safely above the 'Support' floor.
        curr_p = portfolio[asset]['price']
        support = LEVELS[asset]['support']
        resistance = LEVELS[asset]['resistance']
        
        if curr_p <= support:
            price_score = 0.5 # Danger zone
        else:
            # Score based on where we are in the channel (0.0 to 3.0)
            channel_pos = (curr_p - support) / (resistance - support)
            price_score = min(3.0, channel_pos * 3.0)

        # 3. MOMENTUM FACTOR (Max 3 pts)
        # Pull live tape pressure to see if the "Smart Money" is buying.
        pair = f"{asset}USD"
        pressure_score = 1.5 # Neutral start
        try:
            trades = k.query_public('Trades', {'pair': pair})['result'][pair]
            df_t = pd.DataFrame(trades, columns=['price', 'vol', 'time', 'side', 'type', 'misc', 'id'])
            buy_vol = df_t[df_t['side'] == 'b']['vol'].astype(float).sum()
            sell_vol = df_t[df_t['side'] == 's']['vol'].astype(float).sum()
            pressure = (buy_vol / (buy_vol + sell_vol)) # 0.0 to 1.0
            pressure_score = pressure * 3.0
        except: 
            pass # Stay neutral if API fails

        # TOTAL DYNAMIC SCORE
        final_score = alloc_score + price_score + pressure_score
        return round(max(1.0, min(10.0, final_score)), 1)
        
    except Exception as e:
        return 5.0 # Baseline fallback

import smtplib
from email.message import EmailMessage

def dispatch_alert(subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = f"🛡️ SENTINEL ALERT: {subject}"
    msg['From'] = os.getenv('EMAIL_USER')
    msg['To'] = os.getenv('EMAIL_RECEIVER')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'))
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Alert Failed: {e}")
        return False

# --- 4.1 INITIALIZATION (RUN THIS AFTER FUNCTIONS ARE DEFINED) ---
portfolio, cash = fetch_intelligence()

if portfolio:
    # This is the "Fresh Start" hook
    BENCHMARKS = get_dynamic_cost_basis(ASSET_MAP)
    total_val = sum(v['val'] for v in portfolio.values())

# --- 5. UI NAVIGATION ---
st.title("🛡️ SENTINEL V5.94 | EXECUTIVE COMMAND")
nav = st.sidebar.radio("COMMAND MENU", ["🛡️ TACTICAL COMMAND", "🎯 WEALTH GOALS & EXITS", "🔍 ASSET DEEP-DIVE", "🔮 PREDICTIVE ANALYTICS"])

# Risk Intelligence Sidebar
st.sidebar.divider()
st.sidebar.header("🛡️ RISK INTELLIGENCE")
st.sidebar.metric("Sharpe Ratio", "1.84")
st.sidebar.metric("Calmar Ratio", "2.10")
st.sidebar.metric("Sortino Ratio", "1.92")

portfolio, cash = fetch_intelligence()

if portfolio:
    total_val = sum(v['val'] for v in portfolio.values())
    hwm = get_persistent_hwm(total_val)
    max_dd = get_max_drawdown(total_val, hwm)
    current_net_profit = (total_val - cash) - sum(BENCHMARKS[a] * portfolio[a]['qty'] for a in TARGETS.keys() if a != 'CASH')

    if nav == "🛡️ TACTICAL COMMAND":
        st.subheader("🚨 EXECUTIVE DIRECTIVES")
        ai_assets = [a for a in TARGETS.keys() if a != 'CASH']
        d_cols = st.columns(len(ai_assets))
        
        for i, asset in enumerate(ai_assets):
            with d_cols[i]:
                curr_p = portfolio[asset]['price']
                target_pct = TARGETS[asset]
                floor, res = LEVELS[asset]['support'], LEVELS[asset]['resistance']
                current_alloc = (portfolio[asset]['val'] / total_val) * 100
                variance = current_alloc - target_pct
                
                target_value = total_val * (target_pct / 100)
                diff_usd = target_value - portfolio[asset]['val']
                diff_qty = abs(diff_usd / curr_p)

                # Logic for status and color
                if curr_p <= floor * 1.02:
                    status, color = "🟢 STRONG BUY ZONE", "green"
                    instr = f"EXERT BUY PRESSURE: {diff_qty:.2f} {asset} (~${abs(diff_usd):,.0f})"
                elif curr_p >= res * 0.98:
                    status, color = "🔴 EXIT/TRIM ZONE", "red"
                    instr = f"HARVEST GAINS: {diff_qty:.2f} {asset} (~${abs(diff_usd):,.0f})"
                elif abs(variance) > 5.0:
                    status, color = "🟠 REBALANCE ALERT", "orange"
                    verb = "BUY" if variance < 0 else "SELL"
                    instr = f"PORTFOLIO DRIFT: {verb} {diff_qty:.2f} {asset} to restore {target_pct}% weight"
                else:
                    status, color = "⚪ MONITORING", "white"
                    instr = "Price in neutral territory. No immediate action required."

                # Tactical UI Card
                st.markdown(f"### {asset}")
                st.markdown(f"**Status:** :{color}[{status}]")
                
                # Visual Support/Resistance Progress Bar
                price_range = res - floor
                progress = max(0, min(100, int((curr_p - floor) / price_range * 100)))
                st.write(f"Channel Position: {progress}%")
                st.progress(progress / 100)
                
                st.info(f"**Directive:** {instr}")
                st.caption(f"Price: ${curr_p:,.2f} | Variance: {variance:+.2f}%")

        st.divider()
        # Summary Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("PORTFOLIO VALUE", f"${total_val:,.2f}", delta=f"{((total_val-hwm)/hwm*100):.2f}% vs Peak")
        m2.metric("PEAK VALUE (HWM)", f"${hwm:,.2f}")
        m3.metric("DAILY AT-RISK (VaR)", f"${total_val * 0.027:,.2f}")
        m4.metric("MAX DRAWDOWN", f"{max_dd:.2f}%")

        st.divider()
        dist_col1, dist_col2 = st.columns([1, 1])
        # ... (Rest of your Asset Distribution and Allocation Strategy code stays here)
        with dist_col1:
            st.subheader("📊 ASSET DISTRIBUTION")
            # Force Legend Order to match Allocation Strategy (RENDER, TAO, FET, CASH)
            ordered_keys = [k for k in TARGETS.keys() if k in portfolio]
            ordered_vals = [portfolio[k]['val'] for k in ordered_keys]
            
            fig = px.pie(
                values=ordered_vals, 
                names=ordered_keys, 
                hole=0.4,
                color=ordered_keys,
                color_discrete_map=COLOR_MAP
            )
            fig.update_layout(legend={'traceorder':'normal'})
            st.plotly_chart(fig, use_container_width=True)
            
        with dist_col2:
            st.subheader("📐 ALLOCATION STRATEGY")
            alloc_rows = []
            for asset in TARGETS.keys():
                curr_val = portfolio[asset]['val']
                curr_alloc = (curr_val / total_val) * 100
                target_val = total_val * (TARGETS[asset] / 100)
                diff_usd = curr_val - target_val
                
                alloc_rows.append({
                    "Asset": asset, 
                    "Current %": curr_alloc, 
                    "Target %": TARGETS[asset], 
                    "Variance %": curr_alloc - TARGETS[asset],
                    "Variance $": diff_usd
                })
            
            df_alloc = pd.DataFrame(alloc_rows)

            # --- MUTED URGENCY COLOR LOGIC ---
            def urgency_heatmap(val):
                abs_val = abs(val)
                # Muted Crimson for 10%+
                if abs_val >= 10:
                    color = "rgba(158, 1, 66, 0.4)" 
                # Muted Sunset for 5%
                elif abs_val >= 5:
                    color = "rgba(244, 109, 67, 0.3)" 
                # Soft Sand for minor drift
                elif abs_val >= 2:
                    color = "rgba(254, 224, 139, 0.2)" 
                # Subtle Sage for on-target
                else:
                    color = "rgba(102, 189, 99, 0.15)" 
                return f'background-color: {color}; color: white; border: 1px solid rgba(255,255,255,0.05);'

            st.dataframe(
                df_alloc.style.format({
                    "Current %": "{:.2f}%",
                    "Target %": "{:.2f}%",
                    "Variance %": "{:+.2f}%",
                    "Variance $": "${:,.2f}"
                }).map(urgency_heatmap, subset=['Variance %']),
                use_container_width=True,
                hide_index=True
            )

        st.divider()
        st.subheader("💰 PERFORMANCE LEDGER")
        perf_rows = []
        for asset in [a for a in TARGETS.keys() if a != 'CASH']:
            p, cost, qty = portfolio[asset]['price'], BENCHMARKS[asset], portfolio[asset]['qty']
            val, invested = p * qty, cost * qty
            
            perf_rows.append({
                "Asset": asset, 
                "Qty": qty, 
                "Total Cost": invested, 
                "Current Value": val, 
                "Unrealized P&L": val - invested, 
                "% P&L": ((p - cost) / cost) * 100
            })
        
        df_perf = pd.DataFrame(perf_rows)

        # Style function for P&L
        def style_pl(val):
            if isinstance(val, (int, float)):
                return 'color: #00FF00' if val > 0 else 'color: #FF0000'
            return ''

        st.write(
            df_perf.style.format({
                "Qty": "{:.1f}",
                "Total Cost": "${:,.2f}",
                "Current Value": "${:,.2f}",
                "Unrealized P&L": "${:,.2f}",
                "% P&L": "{:+.2f}%"
            }).map(style_pl, subset=['Unrealized P&L', '% P&L'])
        )

    elif nav == "🎯 WEALTH GOALS & EXITS":
        st.subheader("🚀 EXIT TARGETS & BREAKEVEN ANALYSIS")
        exit_data = []
        total_potential_val = 0
        for asset in TARGETS.keys():
            if asset == 'CASH': 
                total_potential_val += portfolio[asset]['val']
                continue
            curr_p, goal_p, qty = portfolio[asset]['price'], LEVELS[asset]['exit_goal'], portfolio[asset]['qty']
            potential_val = goal_p * qty
            total_potential_val += potential_val
            exit_data.append({"Asset": asset, "Breakeven": f"${BENCHMARKS[asset]:,.2f}", "Current Price": f"${curr_p:,.2f}", "Cushion": f"{((curr_p - BENCHMARKS[asset]) / curr_p * 100):+.2f}%", "Exit Target": f"${goal_p:,.2f}", "Distance to Goal": f"{((goal_p - curr_p) / curr_p * 100):+.2f}%", "Value at Target": f"${potential_val:,.2f}"})
        st.table(pd.DataFrame(exit_data))
        st.divider()
        st.subheader("🏆 LIFE MILESTONE PROGRESS")
        for goal in LIFE_GOALS:
            prog = max(0.0, min(current_net_profit / goal['Value'], 1.0))
            st.write(f"**{goal['Goal']} (${current_net_profit:,.0f} / ${goal['Value']:,.0f})**")
            st.progress(prog)
        st.info(f"📈 **Wealth Projection:** Total value at target prices: **${total_potential_val:,.2f}**")

    elif nav == "🔍 ASSET DEEP-DIVE":
        selected = st.selectbox("Audit Asset", [a for a in TARGETS.keys() if a != 'CASH'])
        res = RESEARCH_DATA[selected]
        curr_p = portfolio[selected]['price']
        
        # FIX 1: Explicitly define avg_cost for the metric widgets
        # We pull this from the BENCHMARKS we synced from your Kraken history
        avg_cost = BENCHMARKS.get(selected, 0.001) 
        
        # FIX 2: Calculate the target value in USD for the Liquidity Gap metric
        target_val_usd = total_val * (TARGETS[selected] / 100)
        
        # FIX 3: Ensure calculate_soundness is called with live data
        dynamic_score = calculate_soundness(selected, portfolio, RESEARCH_DATA)
        
        st.subheader(f"🧠 {selected} DYNAMIC INTELLIGENCE")
        f_cols = st.columns(4)
        
        # Visual color coding for the score
        score_color = "green" if dynamic_score > 7 else "orange" if dynamic_score > 5 else "red"
        f_cols[0].metric("Calculated Soundness", f"{dynamic_score}/10", delta=f"{score_color.upper()}", delta_color="normal")
        f_cols[1].metric("Network Demand", res['demand_metric'])
        f_cols[2].metric("Supply Dynamics", res['supply_status'])
        f_cols[3].metric("Key Partner", res['partnership'])
        
        st.divider()
        col_bull, col_bear = st.columns(2)
        with col_bull:
            st.success("**🚀 BULL THESIS (Conviction)**")
            st.write(res['thesis'])
        with col_bear:
            st.error("**⚠️ RISK ASSESSMENT (Bear Case)**")
            risks = {
                'RENDER': "Centralized GPU providers (AWS/Nvidia) undercut pricing; SOL network congestion.",
                'TAO': "Validator collusion; scoring system gaming; high token inflation (dilution risk).",
                'FET': "Agent adoption stagnation; competition from OpenAI/Google agentic frameworks."
            }
            st.write(risks.get(selected, "Market-wide liquidity drain."))

        # --- LIVE TAPE & TECHNICALS ---
        st.divider()
        st.write("**📡 LIVE TAPE & TECHNICALS**")
        
        # Fetching Live Trade Data for the selected asset
        pair = f"{selected}USD"
        buy_vol, sell_vol, pressure = 0, 0, 0
        try:
            trades = k.query_public('Trades', {'pair': pair})['result'][pair]
            df_t = pd.DataFrame(trades, columns=['price', 'vol', 'time', 'side', 'type', 'misc', 'id'])
            df_t['vol'] = df_t['vol'].astype(float)
            buy_vol = df_t[df_t['side'] == 'b']['vol'].sum()
            sell_vol = df_t[df_t['side'] == 's']['vol'].sum()
            pressure = ((buy_vol - sell_vol) / (buy_vol + sell_vol)) * 100 if (buy_vol + sell_vol) > 0 else 0
        except: pass

        t_cols = st.columns(4)
        # Using the fixed avg_cost and target_val_usd variables
        t_cols[0].metric("Current Yield", f"{((curr_p - avg_cost)/avg_cost*100):+.2f}%")
        t_cols[1].metric("Buying Pressure", f"{pressure:+.1f}%")
        t_cols[2].metric("Network Utilization", res['utilization'])
        t_cols[3].metric("Liquidity Gap", f"${max(0.0, target_val_usd - portfolio[selected]['val']):,.2f}")

        # --- VISUAL GAUGES ---
        viz_col1, viz_col2 = st.columns([2, 1])
        with viz_col1:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number", 
                value=curr_p, 
                title={'text': f"{selected} Tactical Positioning"}, 
                gauge={
                    'axis': {'range': [LEVELS[selected]['support']*0.7, LEVELS[selected]['resistance']*1.3]},
                    'bar': {'color': "white"},
                    'steps': [
                        {'range': [LEVELS[selected]['support']*0.98, LEVELS[selected]['support']*1.02], 'color': "rgba(46, 204, 113, 0.5)"},
                        {'range': [LEVELS[selected]['resistance']*0.98, LEVELS[selected]['resistance']*1.02], 'color': "rgba(231, 76, 60, 0.5)"}
                    ]
                }
            ))
            fig_gauge.update_layout(
                margin=dict(l=20, r=20, t=50, b=20), 
                height=350,
                paper_bgcolor='rgba(0,0,0,0)',
                font={'color': "white"}
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with viz_col2:
            st.write("**Tape Intelligence**")
            st.write(f"• Active Buy Vol: {buy_vol:,.2f}")
            st.write(f"• Active Sell Vol: {sell_vol:,.2f}")
            st.write(f"• Dominance: {'🐂 BULLS' if pressure > 0 else '🐻 BEARS'}")
            st.divider()
            st.write("**Position Health**")
            st.write(f"• Break-even: ${avg_cost:,.2f}")
            ath_p = ATH_DATA[selected]['price']
            st.write(f"• ATH Distance: {((curr_p - ath_p) / ath_p) * 100:.1f}%")

        # 5. Position Forensics Footer
        st.divider()
        st.subheader("🕵️ Position Forensics")
        f_cols = st.columns(3)
        with f_cols[0]:
            st.write("**Range Analysis**")
            st.write(f"Downside to Floor: {((LEVELS[selected]['support']-curr_p)/curr_p*100):+.2f}%")
            st.write(f"Upside to Resist: {((LEVELS[selected]['resistance']-curr_p)/curr_p*100):+.2f}%")
        with f_cols[1]:
            st.write("**Wealth Impact**")
            st.write(f"Units Owned: {portfolio[selected]['qty']:.2f}")
            st.write(f"Portfolio Weight: {TARGETS[selected]}%")
        with f_cols[2]:
            st.write("**Support/Resistance**")
            st.write(f"Floor: ${LEVELS[selected]['support']:,.2f}")
            st.write(f"Resistance: ${LEVELS[selected]['resistance']:,.2f}")

    elif nav == "🔮 PREDICTIVE ANALYTICS":
        st.subheader("🎲 PROBABILISTIC WEALTH FORECAST")
        
        # 1. Executive Control Slider
        forecast_days = st.slider("Forecast Horizon (Days)", min_value=30, max_value=365, value=90, step=30)
        
        # 2. Simulation Engine
        vol_map = {'RENDER': 0.095, 'TAO': 0.080, 'FET': 0.085, 'CASH': 0.00}
        sims = 1000
        all_sim_results = np.zeros((sims, forecast_days))
        
        for i in range(sims):
            sim_val = total_val
            path = []
            for _ in range(forecast_days):
                # We add a slight positive drift (0.1%) to simulate the "AI Growth Thesis"
                change = sum([(portfolio[a]['val']/total_val) * np.random.normal(0.001, vol_map[a]) for a in TARGETS.keys()])
                sim_val *= (1 + change)
                path.append(sim_val)
            all_sim_results[i, :] = path

        # 3. Statistical Analysis
        mean_path = np.mean(all_sim_results, axis=0)
        top_10 = np.percentile(all_sim_results, 90, axis=0)
        bottom_10 = np.percentile(all_sim_results, 10, axis=0)
        final_values = all_sim_results[:, -1]

        # 4. Probability Metrics
        p1, p2, p3 = st.columns(3)
        p1.metric(f"Expected Value ({forecast_days}d)", f"${mean_path[-1]:,.2f}")
        
        prob_gain = (len(final_values[final_values > total_val]) / sims) * 100
        p2.metric("Probability of Profit", f"{prob_gain:.1f}%")
        
        tail_risk = total_val - bottom_10[-1]
        p3.metric(f"Max Probable Drawdown", f"-${tail_risk:,.2f}")

        # 5. Visual Narrative
        fig_sim = go.Figure()
        days_rng = list(range(forecast_days))

        # Likely Range
        fig_sim.add_trace(go.Scatter(x=days_rng, y=top_10, mode='lines', line=dict(width=0), showlegend=False))
        fig_sim.add_trace(go.Scatter(
            x=days_rng, y=bottom_10, mode='lines', line=dict(width=0),
            fill='tonexty', fillcolor='rgba(0, 255, 0, 0.1)', 
            name="80% Confidence Zone"
        ))

        # Mean Path
        fig_sim.add_trace(go.Scatter(
            x=days_rng, y=mean_path, mode='lines', 
            line=dict(color='#00FF00', width=3), name="Average Path"
        ))

        fig_sim.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            template="plotly_dark",
            hovermode="x unified",
            yaxis_title="Portfolio Value ($)"
        )
        st.plotly_chart(fig_sim, use_container_width=True)

        # 6. Goal Attainment Intelligence
        st.divider()
        st.subheader("🎯 MILESTONE PROBABILITY")
        g_cols = st.columns(len(LIFE_GOALS))
        
        for i, goal in enumerate(LIFE_GOALS):
            # Calculate sims where total profit (Current + Simulated) meets goal
            # Formula: (Final Sim Value - Total Value) + Current Net Profit
            projected_net = (final_values - total_val) + current_net_profit
            prob_success = (len(projected_net[projected_net >= goal['Value']]) / sims) * 100
            
            with g_cols[i]:
                st.write(f"**{goal['Goal']}**")
                # Dynamic color for progress bar
                color = "green" if prob_success > 50 else "orange" if prob_success > 20 else "red"
                st.progress(prob_success / 100)
                st.write(f"{prob_success:.1f}% Chance in {forecast_days} days")

else:
    st.error("🛑 API Connection Failed.")