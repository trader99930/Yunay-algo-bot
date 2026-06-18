import hashlib
import hmac
import json
import time
import threading
import numpy as np
import pandas as pd
import requests
import urllib3
import streamlit as st

# ✅ SYSTEM STABILITY FOR TERMUX/IPV4
import urllib3.util.connection as urllib3_cn
urllib3_cn.HAS_IPV6 = False

# Streamlit Configuration
st.set_page_config(page_title="Quantum Multi-User Terminal", layout="wide", initial_sidebar_state="collapsed")

# =====================================================
# PREMIUM CYBER TERMINAL CSS
# =====================================================
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14 !important; color: #e2e8f0 !important; font-family: monospace; }
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; max-width: 95% !important; }
    
    .quantum-header-box {
        background-color: #131722; border: 1px solid #1e222d; padding: 15px 20px; border-radius: 4px; margin-bottom: 18px;
    }
    .header-main-title { color: #f59e0b; font-weight: bold; font-size: 16px; letter-spacing: 1px; }
    .header-sub-ip { color: #64748b; font-size: 11px; margin-top: 4px; }
    .ip-glow { color: #38bdf8; font-weight: bold; }

    .grid-panel {
        background-color: #131722 !important; border: 1px solid #1e222d !important;
        border-radius: 4px !important; padding: 18px !important; margin-bottom: 15px !important;
    }
    .panel-heading {
        color: #38bdf8 !important; font-size: 13px !important; font-weight: bold !important;
        letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 15px; border-bottom: 1px dotted #1e222d; padding-bottom: 6px;
    }

    .ticker-widget-card {
        background-color: #131722; border: 1px solid #1e222d; padding: 14px 18px; border-radius: 4px; margin-bottom: 5px;
    }
    .ticker-token-title { color: #94a3b8; font-size: 12px; font-weight: bold; }
    .ticker-dot-orange { color: #f59e0b; font-size: 14px; margin-right: 6px; }
    .ticker-dot-purple { color: #a855f7; font-size: 14px; margin-right: 6px; }
    .ticker-price-green { color: #10b981 !important; font-size: 26px !important; font-weight: bold; margin: 5px 0; }
    
    .rsi-grid-row { display: flex; gap: 15px; margin-top: 8px; font-size: 11px; margin-bottom: 5px; }
    .rsi-tab-item { color: #38bdf8; font-weight: bold; background: #1c2030; padding: 3px 8px; border-radius: 3px; border: 1px solid #2d313f; }

    .pnl-analytics-card {
        background-color: #0d111a; border: 1px solid #1e222d; border-radius: 4px; padding: 18px; margin-bottom: 15px;
    }
    .live-pnl-text { font-size: 24px !important; font-weight: bold; font-family: monospace; margin-top: 5px; }
    .pnl-green { color: #10b981 !important; }
    .pnl-red { color: #ef4444 !important; }
    .pnl-gray { color: #64748b !important; }

    .signal-data-box {
        background-color: #07090e; border: 1px dashed #2d313f; border-radius: 4px; padding: 12px; margin-top: 10px;
    }
    .signal-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; font-size: 12px; }
    .signal-metric { color: #64748b; }
    .signal-value-active { color: #38bdf8; font-weight: bold; }
    .signal-value-waiting { color: #475569; font-weight: bold; }

    .terminal-table { width: 100%; border-collapse: collapse; font-size: 12px; color: #94a3b8; }
    .terminal-table th { color: #475569; text-align: left; padding: 10px 6px; border-bottom: 1px solid #1e222d; font-weight: normal; }
    .terminal-table td { padding: 12px 6px; border-bottom: 1px solid #141822; }
    
    .diagnostic-logger-container {
        background-color: #07090e !important; border: 1px solid #1a1f2c !important; padding: 15px; border-radius: 4px; 
        height: 260px; overflow-y: auto; font-family: monospace; font-size: 12px; line-height: 1.8; color: #94a3b8;
    }
    
    input { background-color: #1c2030 !important; color: white !important; border: 1px solid #2d313f !important; border-radius: 4px; padding: 8px; }
    div[data-testid="stVerticalBlock"] > div { background-color: transparent !important; border: none !important; padding: 0 !important; }
    
    div.stButton > button, div[data-testid="stForm"] button {
        background-color: #171b26 !important; color: #38bdf8 !important; border: 1px solid #2d313f !important;
        border-radius: 4px !important; font-size: 12px !important; font-weight: bold !important; 
        text-transform: uppercase !important; padding: 6px 16px !important; transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button:hover, div[data-testid="stForm"] button:hover {
        background-color: #1c2333 !important; border-color: #38bdf8 !important;
        box-shadow: 0px 0px 8px rgba(56, 189, 248, 0.4) !important;
    }
    
    div[data-testid="stCheckbox"] label p { color: #38bdf8 !important; font-weight: bold !important; font-size: 13px !important; }
    </style>
""", unsafe_allow_html=True)

# =====================================================
# GLOBAL ENGINE MEMORY MESH
# =====================================================
class GlobalEngineMemory:
    def __init__(self):
        self.users_db = {}
        self.global_engine_running = True
        self.active_trades = {}
        self.ordered_candles = {}
        self.is_processing = False
        
        self.last_triggered_setup_info = {
            "BTCUSD": {"entry": "WAITING", "sl": "WAITING", "t1": "WAITING", "t2": "WAITING", "status": "SCANNING ENGINE", "live_pnl": 0.0},
            "ETHUSD": {"entry": "WAITING", "sl": "WAITING", "t1": "WAITING", "t2": "WAITING", "status": "SCANNING ENGINE", "live_pnl": 0.0}
        }
        
        self.strategy_switches = {
            "5-STAR LONG": True, "5-STAR SHORT": True, "5-STAR BB BUY": True, "5-STAR BB SELL": True
        }
        
        self.strategy_metrics = {
            "5-STAR LONG": {"triggers": 0}, "5-STAR SHORT": {"triggers": 0},
            "5-STAR BB BUY": {"triggers": 0}, "5-STAR BB SELL": {"triggers": 0}
        }
        self.last_terminal_logs = [
            "<div><span style='color: #475569;'>[11:10:04]</span> 🚀 Advance Controller Engine Activated.</div>"
        ]
        self.ticker_feeds = {
            "BTCUSD": {"ltp": 0.0, "rsi_1m": 0.0, "rsi_5m": 0.0, "rsi_15m": 0.0}, 
            "ETHUSD": {"ltp": 0.0, "rsi_1m": 0.0, "rsi_5m": 0.0, "rsi_15m": 0.0}
        }

if "mem_instance" not in st.session_state:
    if not hasattr(st, "_global_algo_memory"):
        st._global_algo_memory = GlobalEngineMemory()
    st.session_state["mem_instance"] = st._global_algo_memory

mem = st.session_state["mem_instance"]

BASE_URL = "https://api.india.delta.exchange"

@st.cache_data(ttl=3600)
def get_server_ip():
    try: return requests.get("https://api.ipify.org", timeout=5).text
    except: return "152.58.109.90"

SERVER_IP = get_server_ip()

def add_log(msg, type_icon="🚀"):
    timestamp = time.strftime("%H:%M:%S")
    full_msg = f"<div><span style='color: #475569;'>[{timestamp}]</span> {type_icon} {msg}</div>"
    mem.last_terminal_logs.insert(0, full_msg)
    if len(mem.last_terminal_logs) > 20: mem.last_terminal_logs.pop()

# =====================================================
# DELTA INDIA API CONNECTORS
# =====================================================
def send_signed_request(method, path, api_key, api_secret, payload=None):
    timestamp = str(int(time.time()))
    body_string = json.dumps(payload) if (payload and method in ["POST", "PUT", "DELETE"]) else ""
    signature_payload = method + timestamp + path + "" + body_string
    signature = hmac.new(api_secret.encode("utf-8"), signature_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    headers = {"api-key": api_key, "timestamp": timestamp, "signature": signature, "Content-Type": "application/json"}
    try:
        if method == "POST": r = requests.post(BASE_URL + path, headers=headers, data=body_string, timeout=12)
        else: r = requests.get(BASE_URL + path, headers=headers, params=payload, timeout=12)
        return r.json()
    except: return {"success": False, "error": "Network Timeout"}

def place_stop_loss(symbol, size, side, sl_price, api_key, api_secret):
    if size <= 0: return None
    payload = {
        "product_symbol": symbol, "size": int(size), "side": side.lower(),
        "order_type": "market_order", "stop_order_type": "stop_loss_order",   
        "stop_price": str(round(float(sl_price), 2)), "reduce_only": True
    }
    res = send_signed_request("POST", "/v2/orders", api_key, api_secret, payload)
    return res["result"].get("id") if res and res.get("success") else None

def get_open_position_qty(symbol, api_key, api_secret):
    try:
        res = send_signed_request("GET", "/v2/positions/margined", api_key, api_secret)
        if res and "result" in res:
            for pos in res["result"]:
                if pos.get("product_symbol") == symbol: return abs(int(pos.get("size", 0)))
        return 0
    except: return 0

def rsi_calc(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    return 100 - (100 / (1 + rs))

def fetch_candles_df(symbol, timeframe, limit=200):
    try:
        end_t = int(time.time())
        multiplier_seconds = 60 if timeframe == "1m" else (300 if timeframe == "5m" else 900)
        r = requests.get(f"{BASE_URL}/v2/history/candles", params={"symbol": symbol, "resolution": timeframe, "start": end_t - (limit * multiplier_seconds), "end": end_t}, timeout=10).json()
        if "result" in r and r["result"]:
            df = pd.DataFrame(r["result"]).iloc[::-1].reset_index(drop=True)
            for col in ["close", "high", "low"]: df[col] = pd.to_numeric(df[col])
            return df
        return None
    except: return None

# =====================================================
# BACKGROUND TRADE ENGINE THREAD
# =====================================================
def core_execution_engine(shared_mem):
    while True:
        if not shared_mem.global_engine_running:
            time.sleep(1)
            continue
        try:
            symbols = ["BTCUSD", "ETHUSD"]
            for sym in symbols:
                try:
                    r = requests.get(f"{BASE_URL}/v2/tickers/{sym}", timeout=4).json()
                    if r and "result" in r:
                        shared_mem.ticker_feeds[sym]["ltp"] = round(float(r["result"].get("mark_price", 0)), 2)
                except: pass

            for sym in symbols:
                live_price = shared_mem.ticker_feeds[sym]["ltp"]
                if not live_price or sym not in shared_mem.active_trades:
                    continue
                
                for user in list(shared_mem.active_trades[sym].keys()):
                    trade = shared_mem.active_trades[sym][user]
                    u_db = shared_mem.users_db.get(user)
                    if not u_db: continue
                    
                    ex_qty = get_open_position_qty(sym, u_db['api_key'], u_db['api_secret'])
                    
                    mult = 1 if trade['side'] == 'buy' else -1
                    calc_pnl = round((live_price - trade['entry_price']) * mult * trade['qty'], 2)
                    trade['live_pnl'] = calc_pnl
                    
                    shared_mem.last_triggered_setup_info[sym]["live_pnl"] = calc_pnl
                    
                    if ex_qty == 0 or (trade['side'] == 'buy' and live_price <= trade['sl']) or (trade['side'] == 'sell' and live_price >= trade['sl']):
                        del shared_mem.active_trades[sym][user]
                        shared_mem.last_triggered_setup_info[sym] = {"entry": "WAITING", "sl": "WAITING", "t1": "WAITING", "t2": "WAITING", "status": "SCANNING ENGINE", "live_pnl": 0.0}
                        add_log(f"Position closed safely for {user} on {sym}", type_icon="🛑")
                        continue
                    
                    if trade['current_stage'] == 0 and ex_qty <= int(trade['initial_qty'] * 0.50):
                        trade['sl'] = trade['entry_price']
                        trade['current_stage'] = 1
                        shared_mem.last_triggered_setup_info[sym]["sl"] = f"${trade['entry_price']} (Cost)"
                        add_log(f"Target 1 Hit! SL shifted to Cost for {user}", type_icon="🎯")

            if shared_mem.users_db and not shared_mem.is_processing:
                for sym in symbols:
                    
                    # 🛡️ CRITICAL DUAL PROTECTION BLOCK (No Multiple Entries Allowed)
                    # 1. Local Tracking Check: Agar thread memory mein trade active hai, toh aage nahi badhega.
                    if sym in shared_mem.active_trades and len(shared_mem.active_trades[sym]) > 0:
                        continue
                        
                    # 2. Live Exchange API Check: Agar Exchange par kisi bhi user ki live open position padi hai (> 0), toh entry skip ho jayegi.
                    first_user = list(shared_mem.users_db.keys())[0]
                    exchange_live_qty = get_open_position_qty(sym, shared_mem.users_db[first_user]['api_key'], shared_mem.users_db[first_user]['api_secret'])
                    if exchange_live_qty > 0: 
                        continue

                    df_15m = fetch_candles_df(sym, "15m", limit=200)
                    df_5m = fetch_candles_df(sym, "5m", limit=200)
                    df_1m = fetch_candles_df(sym, "1m", limit=200)
                    if df_15m is None or df_5m is None or df_1m is None: continue
                    
                    df_15m["RSI"] = rsi_calc(df_15m["close"])
                    df_5m["RSI"] = rsi_calc(df_5m["close"])
                    df_1m["RSI"] = rsi_calc(df_1m["close"])
                    
                    ma = df_1m["close"].rolling(20).mean()
                    stdev = df_1m["close"].rolling(20).std()
                    df_1m["BB_up"], df_1m["BB_low"] = ma + (2 * stdev), ma - (2 * stdev)
                    
                    shared_mem.ticker_feeds[sym]["rsi_1m"] = round(df_1m["RSI"].iloc[-1], 2)
                    shared_mem.ticker_feeds[sym]["rsi_5m"] = round(df_5m["RSI"].iloc[-1], 2)
                    shared_mem.ticker_feeds[sym]["rsi_15m"] = round(df_15m["RSI"].iloc[-1], 2)
                    
                    rsi_15, rsi_5, rsi_1, rsi_1_prev = df_15m["RSI"].iloc[-2], df_5m["RSI"].iloc[-2], df_1m["RSI"].iloc[-2], df_1m["RSI"].iloc[-3]
                    close_1m = df_1m["close"].iloc[-2]
                    c_time = df_1m["time"].iloc[-2]
                    
                    if sym in shared_mem.ordered_candles and shared_mem.ordered_candles[sym] == c_time: continue
                    
                    triggered, s_key, side, entry, sl, t1, t2 = False, "", "", 0.0, 0.0, 0.0, 0.0
                    
                    # 1. 5-STAR LONG LOGIC
                    if shared_mem.strategy_switches["5-STAR LONG"] and rsi_15 >= 60 and rsi_5 >= 60 and rsi_1 > 40 and rsi_1 > rsi_1_prev and (43 >= rsi_1_prev >= 20):
                        triggered, s_key, side = True, "5-STAR LONG", "buy"
                        entry = round(float(df_1m["high"].iloc[-2]), 2)
                        sl = round(float(df_1m["low"].iloc[-16:-1].min()), 2)
                        risk = entry - sl
                        t1, t2 = round(entry + risk, 2), round(entry + 2*risk, 2)
                    
                    # 2. 5-STAR SHORT LOGIC
                    elif shared_mem.strategy_switches["5-STAR SHORT"] and rsi_15 <= 40 and rsi_5 <= 40 and rsi_1 < 60 and rsi_1 < rsi_1_prev and (80 >= rsi_1_prev >= 57):
                        triggered, s_key, side = True, "5-STAR SHORT", "sell"
                        entry = round(float(df_1m["low"].iloc[-2]), 2)
                        sl = round(float(df_1m["high"].iloc[-16:-1].max()), 2)
                        risk = sl - entry
                        t1, t2 = round(entry - risk, 2), round(entry - 2*risk, 2)
                    
                    # 3. 5-STAR BB BUY LOGIC (RSI Crossover 60 from below + Price > BB Upper Band)
                    elif shared_mem.strategy_switches["5-STAR BB BUY"] and rsi_15 > 60 and rsi_5 > 60 and rsi_1_prev < 61 and rsi_1 >= 60 and close_1m > df_1m["BB_up"].iloc[-2]:
                        triggered, s_key, side = True, "5-STAR BB BUY", "buy"
                        entry, sl = round(float(df_1m["high"].iloc[-2]), 2), round(float(df_1m["low"].iloc[-2]), 2)
                        risk = entry - sl
                        t1, t2 = round(entry + risk, 2), round(entry + 2*risk, 2)
                    
                    # 4. 5-STAR BB SELL LOGIC (RSI Crossover 40 from above + Price < BB Lower Band)
                    elif shared_mem.strategy_switches["5-STAR BB SELL"] and rsi_15 < 40 and rsi_5 < 40 and rsi_1_prev > 39 and rsi_1 <= 40 and close_1m < df_1m["BB_low"].iloc[-2]:
                        triggered, s_key, side = True, "5-STAR BB SELL", "sell"
                        entry, sl = round(float(df_1m["low"].iloc[-2]), 2), round(float(df_1m["high"].iloc[-2]), 2)
                        risk = sl - entry
                        t1, t2 = round(entry - risk, 2), round(entry - 2*risk, 2)

                    if triggered and risk > 0:
                        shared_mem.is_processing = True
                        shared_mem.ordered_candles[sym] = c_time
                        
                        shared_mem.strategy_metrics[s_key]["triggers"] += 1
                        add_log(f"{s_key} Condition Triggered on {sym}!", type_icon="⚡")
                        
                        shared_mem.last_triggered_setup_info[sym] = {
                            "entry": f"${entry:,.2f}", "sl": f"${sl:,.2f}", "t1": f"${t1:,.2f}", "t2": f"${t2:,.2f}", "status": f"{s_key} ({side.upper()})", "live_pnl": 0.0
                        }
                        
                        for user, u_db in shared_mem.users_db.items():
                            u_qty = u_db["btc_qty"] if sym == "BTCUSD" else u_db["eth_qty"]
                            if u_db["api_key"] in ["mock", ""]: continue
                            
                            res = send_signed_request("POST", "/v2/orders", u_db['api_key'], u_db['api_secret'], {"product_symbol": sym, "size": int(u_qty), "side": side, "order_type": "market_order"} )
                            if res and res.get("success") is True:
                                place_stop_loss(sym, u_qty, "sell" if side == "buy" else "buy", sl, u_db['api_key'], u_db['api_secret'])
                                
                                if sym not in shared_mem.active_trades: shared_mem.active_trades[sym] = {}
                                shared_mem.active_trades[sym][user] = {
                                    'side': side, 'entry_price': entry, 'sl': sl, 't1': t1, 't2': t2,
                                    'current_stage': 0, 'qty': u_qty, 'initial_qty': u_qty, 'live_pnl': 0.0
                                }
                                add_log(f"[REAL ORDER] {user} | {sym} | Size: {u_qty}", type_icon="🚀")
                            else:
                                err = res.get("error", "API Error")
                                add_log(f"Order Failed for {user}: {err}", type_icon="❌")
                        break
            shared_mem.is_processing = False
            time.sleep(1)
        except: time.sleep(1)

if "thread_started" not in st.session_state:
    threading.Thread(target=core_execution_engine, args=(mem,), daemon=True).start()
    st.session_state["thread_started"] = True

# =====================================================
# RENDER LAYOUT
# =====================================================
st.markdown(f"""
<div class="quantum-header-box">
    <div class="header-main-title">⚡ QUANTUM MULTI-USER MATRIX</div>
    <div class="header-sub-ip">Whitelisting Server IP: <span class="ip-glow">{SERVER_IP}</span></div>
</div>
""", unsafe_allow_html=True)

col_btc_w, col_eth_w = st.columns(2)

with col_btc_w:
    btc_info = mem.last_triggered_setup_info["BTCUSD"]
    st.markdown(f"""
    <div class="ticker-widget-card">
        <div><span class="ticker-dot-orange">●</span><span class="ticker-token-title">BTCUSD Future Live</span></div>
        <div class="ticker-price-green">${mem.ticker_feeds["BTCUSD"]["ltp"]:,.2f}</div>
        <div class="rsi-grid-row">
            <span class="rsi-tab-item">1M RSI: {mem.ticker_feeds["BTCUSD"]["rsi_1m"]:.2f}</span>
            <span class="rsi-tab-item" style="color: #10b981;">5M RSI: {mem.ticker_feeds["BTCUSD"]["rsi_5m"]:.2f}</span>
            <span class="rsi-tab-item" style="color: #eab308;">15M RSI: {mem.ticker_feeds["BTCUSD"]["rsi_15m"]:.2f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    pnl_val = btc_info.get("live_pnl", 0.0)
    pnl_class = "pnl-green" if pnl_val > 0 else ("pnl-red" if pnl_val < 0 else "pnl-gray")
    cls_e = "signal-value-active" if btc_info["entry"] != "WAITING" else "signal-value-waiting"
    
    st.markdown(f"""
    <div class="pnl-analytics-card">
        <div style="font-size: 11px; color: #64748b; font-weight: bold;">📊 LIVE TRANSACTION RUNTIME MATRIX</div>
        <div class="live-pnl-text {pnl_class}">Net P&L: {'+' if pnl_val >= 0 else ''}${pnl_val:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="signal-data-box">
        <div style="font-size: 11px; color: #38bdf8; font-weight: bold; margin-bottom: 6px;">🎯 SETUP STATUS: {btc_info['status']}</div>
        <div class="signal-grid">
            <div><span class="signal-metric">ENTRY PRICE:</span> <span class="{cls_e}">{btc_info['entry']}</span></div>
            <div><span class="signal-metric">STOP LOSS:</span> <span class="{cls_e}">{btc_info['sl']}</span></div>
            <div><span class="signal-metric">TARGET 1:</span> <span class="{cls_e}">{btc_info['t1']}</span></div>
            <div><span class="signal-metric">TARGET 2:</span> <span class="{cls_e}">{btc_info['t2']}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_eth_w:
    eth_info = mem.last_triggered_setup_info["ETHUSD"]
    st.markdown(f"""
    <div class="ticker-widget-card">
        <div><span class="ticker-dot-purple">●</span><span class="ticker-token-title">ETHUSD Future Live</span></div>
        <div class="ticker-price-green" style="color: #a855f7 !important;">${mem.ticker_feeds["ETHUSD"]["ltp"]:,.2f}</div>
        <div class="rsi-grid-row">
            <span class="rsi-tab-item">1M RSI: {mem.ticker_feeds["ETHUSD"]["rsi_1m"]:.2f}</span>
            <span class="rsi-tab-item" style="color: #10b981;">5M RSI: {mem.ticker_feeds["ETHUSD"]["rsi_5m"]:.2f}</span>
            <span class="rsi-tab-item" style="color: #eab308;">15M RSI: {mem.ticker_feeds["ETHUSD"]["rsi_15m"]:.2f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    pnl_val_eth = eth_info.get("live_pnl", 0.0)
    pnl_class_eth = "pnl-green" if pnl_val_eth > 0 else ("pnl-red" if pnl_val_eth < 0 else "pnl-gray")
    cls_ee = "signal-value-active" if eth_info["entry"] != "WAITING" else "signal-value-waiting"
    
    st.markdown(f"""
    <div class="pnl-analytics-card">
        <div style="font-size: 11px; color: #64748b; font-weight: bold;">📊 LIVE TRANSACTION RUNTIME MATRIX</div>
        <div class="live-pnl-text {pnl_class_eth}">Net P&L: {'+' if pnl_val_eth >= 0 else ''}${pnl_val_eth:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="signal-data-box">
        <div style="font-size: 11px; color: #38bdf8; font-weight: bold; margin-bottom: 6px;">🎯 SETUP STATUS: {eth_info['status']}</div>
        <div class="signal-grid">
            <div><span class="signal-metric">ENTRY PRICE:</span> <span class="{cls_ee}">{eth_info['entry']}</span></div>
            <div><span class="signal-metric">STOP LOSS:</span> <span class="{cls_ee}">{eth_info['sl']}</span></div>
            <div><span class="signal-metric">TARGET 1:</span> <span class="{cls_ee}">{eth_info['t1']}</span></div>
            <div><span class="signal-metric">TARGET 2:</span> <span class="{cls_ee}">{eth_info['t2']}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Mid Layer Switches
col_body_l, col_body_r = st.columns(2)
with col_body_l:
    st.markdown('<div class="grid-panel" style="min-height: 250px;">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">🎛️ ENGINE GLOBAL SWITCH SYSTEM</div>', unsafe_allow_html=True)
    c_status = "🟢 RUNNING" if mem.global_engine_running else "🔴 STOPPED"
    st.markdown(f"<div style='font-size:14px; margin-bottom:15px;'>Current Engine State: <b>{c_status}</b></div>", unsafe_allow_html=True)
    
    sc1, sc2 = st.columns(2)
    with sc1:
        if st.button("🟢 START RUNNER", use_container_width=True):
            mem.global_engine_running = True
            st.rerun()
    with sc2:
        if st.button("🔴 STOP SCANNER", use_container_width=True):
            mem.global_engine_running = False
            st.rerun()
            
    st.markdown('<div class="embedded-status-msg">🛡️ PROFILE MATRIX ACTION ACTIVE</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_body_r:
    st.markdown('<div class="grid-panel" style="min-height: 250px;">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">⚙️ QUAD-STRATEGY PIPELINE SWITCHES</div>', unsafe_allow_html=True)
    mem.strategy_switches["5-STAR LONG"] = st.checkbox("1. RSI 5-STAR LONG", value=mem.strategy_switches["5-STAR LONG"])
    mem.strategy_switches["5-STAR SHORT"] = st.checkbox("2. RSI 5-STAR SHORT", value=mem.strategy_switches["5-STAR SHORT"])
    mem.strategy_switches["5-STAR BB BUY"] = st.checkbox("3. BOLLINGER BUY BREAKOUT", value=mem.strategy_switches["5-STAR BB BUY"])
    mem.strategy_switches["5-STAR BB SELL"] = st.checkbox("4. BOLLINGER SELL BREAKOUT", value=mem.strategy_switches["5-STAR BB SELL"])
    st.markdown('</div>', unsafe_allow_html=True)

# Diagnostic Logger Report
st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-heading">📊 LIVE TERMINAL DIAGNOSTIC REPORT</div>', unsafe_allow_html=True)
st.markdown(f'<div class="diagnostic-logger-container">{"".join(mem.last_terminal_logs)}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Active Positions Tracker Visual Panel
st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-heading">💸 LIVE ACTIVE TRADE MATRIX MONITOR Ledger</div>', unsafe_allow_html=True)
if mem.active_trades and any(mem.active_trades.values()):
    ledger_items = []
    for asset, users in mem.active_trades.items():
        for usr, detail in users.items():
            ledger_items.append({
                "User Account": usr, "Asset": asset, "Direction": detail['side'].upper(),
                "Entry Trigger": f"${detail['entry_price']:.2f}", "Stop Loss": f"${detail['sl']:.2f}",
                "Target 1 Grid": f"${detail['t1']:.2f}", "Target 2 Grid": f"${detail['t2']:.2f}",
                "Allocated Size": detail['qty'], "Net P&L": f"${detail['live_pnl']:.2f}"
            })
    st.dataframe(pd.DataFrame(ledger_items), use_container_width=True)
else:
    st.markdown("<div style='color:#10b981; font-size:12px;'>All positions clean. Waiting for active 5-star validation signals to trigger ledger...</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Accounts Configuration Grid & Quantity Setup
st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-heading">📁 MASTER ACCOUNT CONFIGURATION MATRIX (QUANTITY MANAGEMENT)</div>', unsafe_allow_html=True)

if mem.users_db:
    active_user = list(mem.users_db.keys())[0]
    btc_lots = mem.users_db[active_user]["btc_qty"]
    eth_lots = mem.users_db[active_user]["eth_qty"]
    
    st.markdown(f"""
    <table class="terminal-table" style="margin-bottom: 20px;">
        <thead>
            <tr><th>ID</th><th>User Name</th><th>Active Coins</th><th>Active Matrix Strategies</th><th>Allocated Qty (BTC / ETH)</th></tr>
        </thead>
        <tbody>
            <tr>
                <td style="color: #38bdf8;">CUST-002</td>
                <td style="color: #fff; font-weight: bold;">{active_user}</td>
                <td style="color: #eab308;">[BTCUSD] [ETHUSD]</td>
                <td style="color: #10b981;">[DYNAMIC MATRIX INTERFACE CONTROL]</td>
                <td style="color: #38bdf8; font-weight: bold;">{btc_lots} Lots / {eth_lots} Lots</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)
    
    with st.form("Live Multiplier Form Controller"):
        qc1, qc2, qc3 = st.columns([2, 2, 1])
        with qc1: new_btc = st.number_input("Adjust BTC Multiplier Size (Lots)", min_value=1, value=int(btc_lots))
        with qc2: new_eth = st.number_input("Adjust ETH Multiplier Size (Lots)", min_value=1, value=int(eth_lots))
        with qc3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            apply_qty = st.form_submit_button("UPDATE QTY")
            
        if apply_qty:
            mem.users_db[active_user]["btc_qty"] = new_btc
            mem.users_db[active_user]["eth_qty"] = new_eth
            add_log(f"Quantity updated: BTC -> {new_btc}, ETH -> {new_eth}", type_icon="⚙️")
            st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    if st.button("LOGOUT SESSION CONTROL"):
        mem.users_db.clear()
        st.rerun()
else:
    st.markdown("<span style='color: #f43f5e; font-size:12px; font-weight:bold;'>⚠️ NO ACTIVE PROFILE FOUND. PLEASE ONBOARD REAL TRADING KEYS:</span>", unsafe_allow_html=True)
    with st.form("Onboard Credentials Setup Check", clear_on_submit=True):
        cc1, cc2, cc3 = st.columns(3)
        with cc1: u_name = st.text_input("User Account Name", value="Sushil")
        with cc2: u_key = st.text_input("Delta Exchange API Key", type="password")
        with cc3: u_sec = st.text_input("Delta Exchange API Secret Key", type="password")
        
        save_triggered = st.form_submit_button("🔒 SAVE & INITIATE SECURE SCANNER CORE", use_container_width=True)
        if save_triggered and u_name and u_key and u_sec:
            mem.users_db[u_name] = {"api_key": u_key, "api_secret": u_sec, "btc_qty": 4, "eth_qty": 4, "active": True}
            add_log(f"Secure Profile saved for {u_name}. Scanning loop ready.", type_icon="🔒")
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Auto Refresh Sync Loop
time.sleep(1)
st.rerun()
