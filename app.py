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
from auth import auth_page, load_users, save_users

# ✅ SYSTEM STABILITY FOR TERMUX/IPV4
import urllib3.util.connection as urllib3_cn
urllib3_cn.HAS_IPV6 = False

# Streamlit Configuration
st.set_page_config(page_title="Quantum Multi-User Terminal", layout="wide", initial_sidebar_state="collapsed")

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
            "<div><span style='color: #38bdf8;'>[SYSTEM]</span> 🚀 Advance Controller Engine Activated.</div>"
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

# --- 🔐 RELOAD PERSISTENCE ANCHOR ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = True  

if "current_user" not in st.session_state or not st.session_state["current_user"]:
    all_users_list = load_users()
    if all_users_list:
        st.session_state["current_user"] = list(all_users_list.keys())[0]
    else:
        st.session_state["current_user"] = "Master_Trader"

if not st.session_state.get("logged_in", False):
    if not auth_page():
        st.stop()

current_usr = st.session_state.get("current_user", "Master_Trader")
if current_usr not in mem.users_db:
    all_u = load_users()
    if current_usr in all_u and all_u[current_usr].get("api_key"):
        mem.users_db[current_usr] = {
            "api_key": all_u[current_usr]["api_key"],
            "api_secret": all_u[current_usr]["api_secret"],
            "btc_qty": all_u[current_usr].get("btc_qty", 4),
            "eth_qty": all_u[current_usr].get("eth_qty", 4),
            "active": True
        }
    else:
        mem.users_db[current_usr] = {"api_key": "", "api_secret": "", "btc_qty": 4, "eth_qty": 4, "active": True}

# =====================================================
# MASTER MULTI-COLOR NEON GLOW CUSTOM CSS
# =====================================================
st.markdown("""
    <style>
    .stApp { background-color: #060913 !important; color: #ffff00 !important; font-family: monospace; font-weight: bold !important; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1.5rem !important; max-width: 96% !important; }
    
    .quantum-header-box { background-color: #0b132b; border: 2px solid #1e3a8a; padding: 15px 20px; border-radius: 6px; margin-bottom: 18px; }
    .header-main-title { color: #38bdf8; font-weight: bold; font-size: 17px; letter-spacing: 1px; }
    .header-sub-ip { color: #ffff00 !important; font-weight: bold !important; font-size: 11px; margin-top: 4px; }
    .ip-glow { color: #10b981; font-weight: bold; }

    .grid-panel { background-color: #0b132b !important; border: 2px solid #1e3a8a !important; border-radius: 6px !important; padding: 18px !important; margin-bottom: 15px !important; }
    .panel-heading { color: #38bdf8 !important; font-size: 13px !important; font-weight: bold !important; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 15px; border-bottom: 1px dashed #1e3a8a; padding-bottom: 6px; }

    .ticker-widget-card { background-color: #0d1b3e; border: 1px solid #1e3a8a; padding: 14px 18px; border-radius: 6px; margin-bottom: 5px; }
    .ticker-token-title { color: #ffff00 !important; font-size: 13px; font-weight: bold !important; }
    .ticker-dot-orange { color: #f59e0b; font-size: 14px; margin-right: 6px; }
    .ticker-dot-purple { color: #a855f7; font-size: 14px; margin-right: 6px; }
    .ticker-price-green { color: #38bdf8 !important; font-size: 28px !important; font-weight: bold; margin: 5px 0; }
    
    .rsi-grid-row { display: flex; gap: 15px; margin-top: 8px; font-size: 11px; margin-bottom: 5px; }
    
    .rsi-tab-item-1m { color: #ffff00 !important; font-weight: 900 !important; font-size: 12.5px !important; background: #1e3a8a; padding: 3px 10px; border-radius: 3px; border: 1px solid #3b82f6; }
    .rsi-tab-item-5m { color: #00ff00 !important; font-weight: 900 !important; font-size: 12.5px !important; background: #1e3a8a; padding: 3px 10px; border-radius: 3px; border: 1px solid #3b82f6; text-shadow: 0px 0px 5px rgba(0,255,0,0.5); }
    .rsi-tab-item-15m { color: #ff0000 !important; font-weight: 900 !important; font-size: 12.5px !important; background: #1e3a8a; padding: 3px 10px; border-radius: 3px; border: 1px solid #3b82f6; text-shadow: 0px 0px 5px rgba(255,0,0,0.5); }

    .pnl-analytics-card { background-color: #060913; border: 1px solid #1e3a8a; border-radius: 4px; padding: 15px; margin-bottom: 12px; }
    .live-pnl-text { font-size: 25px !important; font-weight: bold; font-family: monospace; margin-top: 3px; }
    .pnl-green { color: #10b981 !important; }
    .pnl-red { color: #ef4444 !important; }
    .pnl-gray { color: #ffff00 !important; }

    .signal-data-box { background-color: #060913; border: 1px dashed #1e3a8a; border-radius: 6px; padding: 12px; margin-top: 5px; }
    .signal-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; font-size: 12px; }
    .signal-metric { color: #38bdf8 !important; font-weight: bold !important; }
    .signal-value-active { color: #10b981; font-weight: bold; }
    .signal-value-waiting { color: #e2e8f0 !important; font-weight: 500 !important; font-size: 11.5px !important; }

    .terminal-table { width: 100%; border-collapse: collapse; font-size: 12px; color: #ffff00 !important; }
    .terminal-table th { color: #38bdf8 !important; text-align: left; padding: 10px 6px; border-bottom: 2px solid #1e3a8a; font-weight: bold !important; }
    .terminal-table td { padding: 12px 6px; border-bottom: 1px solid #1e3a8a; color: #ffff00 !important; font-weight: bold !important; }
    
    .diagnostic-logger-container { background-color: #060913 !important; border: 1px solid #1e3a8a !important; padding: 15px; border-radius: 6px; height: 250px; overflow-y: auto; font-family: monospace; font-size: 12px; line-height: 1.8; color: #ffff00 !important; }
    
    input { background-color: #0d1b3e !important; color: #ffffff !important; font-weight: bold !important; border: 2px solid #1e3a8a !important; border-radius: 4px; padding: 8px; }
    div[data-testid="stVerticalBlock"] > div { background-color: transparent !important; border: none !important; padding: 0 !important; }
    
    div.stButton > button, div[data-testid="stForm"] button, .stFormSubmitButton button { 
        background-color: #07090e !important; 
        border: 2px solid #1e3a8a !important; 
        border-radius: 6px !important; 
        font-size: 12px !important; 
        font-weight: bold !important; 
        text-transform: uppercase !important; 
        padding: 6px 16px !important; 
        transition: all 0.2s ease-in-out !important; 
    }
    
    div.stButton > button:hover, div[data-testid="stForm"] button:hover { background-color: #1c2d5a !important; border-color: #38bdf8 !important; box-shadow: 0px 0px 10px rgba(56, 189, 248, 0.4) !important; }

    .neon-green-lbl { color: #00ff00 !important; font-weight: bold !important; font-size: 14px !important; text-shadow: 0px 0px 6px rgba(0,255,0,0.6); display: inline-block; }
    .neon-red-lbl { color: #ff0000 !important; font-weight: bold !important; font-size: 14px !important; text-shadow: 0px 0px 6px rgba(255,0,0,0.6); display: inline-block; }
    
    div[data-testid="stColumn"] { display: flex; align-items: center !important; }
    div[data-testid="stCheckbox"] label { margin-bottom: 0px !important; padding-top: 5px !important; }

    .stWidgetFormLabel, div[data-testid="stMarkdownContainer"] p, label { color: #ffff00 !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

BASE_URL = "https://api.india.delta.exchange"

@st.cache_data(ttl=3600)
def get_server_ip():
    try: return requests.get("https://api.ipify.org", timeout=5).text
    except: return "152.58.109.90"

SERVER_IP = get_server_ip()

def add_log(msg, type_icon="🚀"):
    import datetime
    ist_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)
    timestamp = ist_time.strftime("%H:%M:%S")
    
    full_msg = f"<div><span style='color: #38bdf8;'>[{timestamp}]</span> {type_icon} <span style='color:#ffff00; font-weight:bold;'>{msg}</span></div>"
    mem.last_terminal_logs.insert(0, full_msg)
    if len(mem.last_terminal_logs) > 20: mem.last_terminal_logs.pop()

# =====================================================
# DELTA INDIA API CONNECTORS
# =====================================================
def send_signed_request(method, path, api_key, api_secret, payload=None):
    if not api_key or not api_secret: return {"success": False, "error": "Keys Missing"}
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
    if res and res.get("success") is True: return res["result"].get("id")
    return None

def place_target_order(symbol, size, side, target_price, api_key, api_secret):
    if size <= 0: return None
    payload = {
        "product_symbol": symbol, "size": int(size), "side": side.lower(),
        "order_type": "limit_order", "limit_price": str(round(float(target_price), 2)), "reduce_only": True
    }
    res = send_signed_request("POST", "/v2/orders", api_key, api_secret, payload)
    if res and res.get("success") is True: return res["result"].get("id")
    return None

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
    return 100 - (100 / (1 + (avg_gain / (avg_loss + 1e-10))))

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
                    if r and "result" in r: shared_mem.ticker_feeds[sym]["ltp"] = round(float(r["result"].get("mark_price", 0)), 2)
                except: pass

            for sym in symbols:
                live_price = shared_mem.ticker_feeds[sym]["ltp"]
                if not live_price or sym not in shared_mem.active_trades: continue
                
                for user in list(shared_mem.active_trades[sym].keys()):
                    trade = shared_mem.active_trades[sym][user]
                    u_db = shared_mem.users_db.get(user)
                    if not u_db or not u_db.get('api_key'): continue
                    
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
                    
                    if trade['current_stage'] == 0 and ex_qty <= int(trade['initial_qty'] * 0.55):
                        trade['sl'] = trade['entry_price']  
                        trade['current_stage'] = 1
                        shared_mem.last_triggered_setup_info[sym]["sl"] = f"${trade['entry_price']} (Cost)"
                        add_log(f"🎯 Target 1 Hit! 50% Qty Booked. SL Trailed to Cost for {user}", type_icon="💰")
                    
                    if trade['current_stage'] == 1 and ex_qty <= int(trade['initial_qty'] * 0.28):
                        trade['sl'] = trade['t1']  
                        trade['current_stage'] = 2
                        shared_mem.last_triggered_setup_info[sym]["sl"] = f"${trade['t1']} (T1 Protected)"
                        add_log(f"🎯 Target 2 Hit! 25% Qty Booked. SL Trailed to T1 for {user}", type_icon="🚀")

            if shared_mem.users_db and not shared_mem.is_processing:
                for sym in symbols:
                    if sym in shared_mem.active_trades and len(shared_mem.active_trades[sym]) > 0: continue
                    first_user = list(shared_mem.users_db.keys())[0]
                    if not shared_mem.users_db[first_user].get('api_key'): continue
                    
                    exchange_live_qty = get_open_position_qty(sym, shared_mem.users_db[first_user]['api_key'], shared_mem.users_db[first_user]['api_secret'])
                    if exchange_live_qty > 0: continue

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
                    
                    if shared_mem.strategy_switches["5-STAR LONG"] and rsi_15 >= 60 and rsi_5 >= 60 and rsi_1 > 40 and rsi_1 > rsi_1_prev and (43 >= rsi_1_prev >= 20):
                        triggered, s_key, side = True, "5-STAR LONG", "buy"
                        entry = round(float(df_1m["high"].iloc[-2]), 2)
                        sl = round(float(df_1m["low"].iloc[-16:-1].min()), 2)
                        risk = entry - sl
                        t1, t2 = round(entry + risk, 2), round(entry + 2*risk, 2)
                    
                    elif shared_mem.strategy_switches["5-STAR SHORT"] and rsi_15 <= 40 and rsi_5 <= 40 and rsi_1 < 60 and rsi_1 < rsi_1_prev and (80 >= rsi_1_prev >= 57):
                        triggered, s_key, side = True, "5-STAR SHORT", "sell"
                        entry = round(float(df_1m["low"].iloc[-2]), 2)
                        sl = round(float(df_1m["high"].iloc[-16:-1].max()), 2)
                        risk = sl - entry
                        t1, t2 = round(entry - risk, 2), round(entry - 2*risk, 2)
                    
                    elif shared_mem.strategy_switches["5-STAR BB BUY"] and rsi_15 > 60 and rsi_5 > 60 and rsi_1_prev < 61 and rsi_1 >= 60 and close_1m > df_1m["BB_up"].iloc[-2]:
                        triggered, s_key, side = True, "5-STAR BB BUY", "buy"
                        entry, sl = round(float(df_1m["high"].iloc[-2]), 2), round(float(df_1m["low"].iloc[-2]), 2)
                        risk = entry - sl
                        t1, t2 = round(entry + risk, 2), round(entry + 2*risk, 2)
                    
                    elif shared_mem.strategy_switches["5-STAR BB SELL"] and rsi_15 < 40 and rsi_5 < 40 and rsi_1_prev > 39 and rsi_1 <= 40 and close_1m < df_1m["BB_low"].iloc[-2]:
                        triggered, s_key, side = True, "5-STAR BB SELL", "sell"
                        entry, sl = round(float(df_1m["low"].iloc[-2]), 2), round(float(df_1m["high"].iloc[-2]), 2)
                        risk = sl - entry
                        t1, t2 = round(entry - risk, 2), round(entry - 2*risk, 2)

                    if triggered and risk > 0:
                        shared_mem.is_processing = True
                        shared_mem.ordered_candles[sym] = c_time
                        shared_mem.strategy_metrics[s_key]["triggers"] += 1
                        add_log(f"{s_key} Triggered on {sym}!", type_icon="⚡")
                        
                        shared_mem.last_triggered_setup_info[sym] = {
                            "entry": f"${entry:,.2f}", "sl": f"${sl:,.2f}", "t1": f"${t1:,.2f}", "t2": f"${t2:,.2f}", "status": f"{s_key} ({side.upper()})", "live_pnl": 0.0
                        }
                        
                        for user, u_db in shared_mem.users_db.items():
                            u_qty = int(u_db["btc_qty"] if sym == "BTCUSD" else u_db["eth_qty"])
                            if not u_db.get("api_key"): continue
                            
                            res = send_signed_request("POST", "/v2/orders", u_db['api_key'], u_db['api_secret'], {"product_symbol": sym, "size": u_qty, "side": side, "order_type": "market_order"} )
                            if res and res.get("success") is True:
                                opposite_side = "sell" if side == "buy" else "buy"
                                t1_qty = int(u_qty * 0.50)  
                                t2_qty = int(u_qty * 0.25)  
                                
                                if t1_qty > 0: place_target_order(sym, t1_qty, opposite_side, t1, u_db['api_key'], u_db['api_secret'])
                                if t2_qty > 0: place_target_order(sym, t2_qty, opposite_side, t2, u_db['api_key'], u_db['api_secret'])
                                
                                place_stop_loss(sym, t1_qty, opposite_side, sl, u_db['api_key'], u_db['api_secret'])
                                place_stop_loss(sym, t2_qty, opposite_side, sl, u_db['api_key'], u_db['api_secret'])
                                place_stop_loss(sym, (u_qty - t1_qty - t2_qty), opposite_side, sl, u_db['api_key'], u_db['api_secret'])
                                
                                if sym not in shared_mem.active_trades: shared_mem.active_trades[sym] = {}
                                shared_mem.active_trades[sym][user] = {
                                    'side': side, 'entry_price': entry, 'sl': sl, 't1': t1, 't2': t2,
                                    'current_stage': 0, 'qty': u_qty, 'initial_qty': u_qty, 'live_pnl': 0.0
                                }
                        break
            shared_mem.is_processing = False
            time.sleep(1)
        except: time.sleep(1)

if "thread_started" not in st.session_state:
    threading.Thread(target=core_execution_engine, args=(mem,), daemon=True).start()
    st.session_state["thread_started"] = True

# =====================================================
# CALLBACK STATE CONTROL BUTTONS
# =====================================================
def trigger_stop_action():
    mem.global_engine_running = False
    add_log("Algorithmic System SCANNER Completely Stopped.", type_icon="🔴")
    st.rerun()

def trigger_start_action():
    mem.global_engine_running = True
    add_log("Algorithmic System RUNNER Activated.", type_icon="🟢")
    st.rerun()

# =====================================================
# RENDER LAYOUT
# =====================================================
st.markdown(f"""
<div class="quantum-header-box">
    <div class="header-main-title">⚡ QUANTUM MULTI-USER MATRIX (PERSISTENT ACTIVE)</div>
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
            <span class="rsi-tab-item-1m">{mem.ticker_feeds["BTCUSD"]["rsi_1m"]:.2f}</span>
            <span class="rsi-tab-item-5m">{mem.ticker_feeds["BTCUSD"]["rsi_5m"]:.2f}</span>
            <span class="rsi-tab-item-15m">{mem.ticker_feeds["BTCUSD"]["rsi_15m"]:.2f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    pnl_val = btc_info.get("live_pnl", 0.0)
    pnl_class = "pnl-green" if pnl_val > 0 else ("pnl-red" if pnl_val < 0 else "pnl-gray")
    
    cls_entry = "signal-value-active" if btc_info['entry'] != "WAITING" else "signal-value-waiting"
    cls_sl = "signal-value-active" if btc_info['sl'] != "WAITING" else "signal-value-waiting"
    cls_t1 = "signal-value-active" if btc_info['t1'] != "WAITING" else "signal-value-waiting"
    cls_t2 = "signal-value-active" if btc_info['t2'] != "WAITING" else "signal-value-waiting"

    st.markdown(f"""
    <div class="pnl-analytics-card">
        <div class="live-pnl-text {pnl_class}">Net P&L: {'+' if pnl_val >= 0 else ''}${pnl_val:,.2f}</div>
    </div>
    <div class="signal-data-box">
        <div style="font-size: 11px; color: #38bdf8; font-weight: bold; margin-bottom: 6px;">🎯 SETUP STATUS: {btc_info['status']}</div>
        <div class="signal-grid">
            <div><span class="signal-metric">ENTRY:</span> <span class="{cls_entry}">{btc_info['entry']}</span></div>
            <div><span class="signal-metric">STOP LOSS:</span> <span class="{cls_sl}">{btc_info['sl']}</span></div>
            <div><span class="signal-metric">TARGET 1:</span> <span class="{cls_t1}">{btc_info['t1']}</span></div>
            <div><span class="signal-metric">TARGET 2:</span> <span class="{cls_t2}">{btc_info['t2']}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_eth_w:
    eth_info = mem.last_triggered_setup_info["ETHUSD"]
    st.markdown(f"""
    <div class="ticker-widget-card">
        <div><span class="ticker-dot-purple">●</span><span class="ticker-token-title">ETHUSD Future Live</span></div>
        <div class="ticker-price-green">${mem.ticker_feeds["ETHUSD"]["ltp"]:,.2f}</div>
        <div class="rsi-grid-row">
            <span class="rsi-tab-item-1m">{mem.ticker_feeds["ETHUSD"]["rsi_1m"]:.2f}</span>
            <span class="rsi-tab-item-5m">{mem.ticker_feeds["ETHUSD"]["rsi_5m"]:.2f}</span>
            <span class="rsi-tab-item-15m">{mem.ticker_feeds["ETHUSD"]["rsi_15m"]:.2f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    pnl_val_eth = eth_info.get("live_pnl", 0.0)
    pnl_class_eth = "pnl-green" if pnl_val_eth > 0 else ("pnl-red" if pnl_val_eth < 0 else "pnl-gray")
    
    cls_entry_eth = "signal-value-active" if eth_info['entry'] != "WAITING" else "signal-value-waiting"
    cls_sl_eth = "signal-value-active" if eth_info['sl'] != "WAITING" else "signal-value-waiting"
    cls_t1_eth = "signal-value-active" if eth_info['t1'] != "WAITING" else "signal-value-waiting"
    cls_t2_eth = "signal-value-active" if eth_info['t2'] != "WAITING" else "signal-value-waiting"

    st.markdown(f"""
    <div class="pnl-analytics-card">
        <div class="live-pnl-text {pnl_class_eth}">Net P&L: {'+' if pnl_val_eth >= 0 else ''}${pnl_val_eth:,.2f}</div>
    </div>
    <div class="signal-data-box">
        <div style="font-size: 11px; color: #38bdf8; font-weight: bold; margin-bottom: 6px;">🎯 SETUP STATUS: {eth_info['status']}</div>
        <div class="signal-grid">
            <div><span class="signal-metric">ENTRY:</span> <span class="{cls_entry_eth}">{eth_info['entry']}</span></div>
            <div><span class="signal-metric">STOP LOSS:</span> <span class="{cls_sl_eth}">{eth_info['sl']}</span></div>
            <div><span class="signal-metric">TARGET 1:</span> <span class="{cls_t1_eth}">{eth_info['t1']}</span></div>
            <div><span class="signal-metric">TARGET 2:</span> <span class="{cls_t2_eth}">{eth_info['t2']}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

col_body_l, col_body_r = st.columns(2)
with col_body_l:
    st.markdown('<div class="grid-panel" style="min-height: 250px;">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">🎛️ ENGINE GLOBAL SWITCH SYSTEM</div>', unsafe_allow_html=True)
    
    engine_status_label = "🟩 ACTIVE (RUNNING)" if mem.global_engine_running else "🟫 DEACTIVATED (PAUSED)"
    st.markdown(f"<div style='font-size:12px; margin-bottom:10px; color:#ffff00;'>CURRENT STATUS: <b style='color:#38bdf8;'>{engine_status_label}</b></div>", unsafe_allow_html=True)
    
    # ✅ FIX: Native callbacks to guarantee instant re-rendering on Streamlit Cloud
    if mem.global_engine_running:
        st.button("🔴 STOP SCANNER", on_click=trigger_stop_action, use_container_width=True)
    else:
        st.button("🟢 START RUNNER", on_click=trigger_start_action, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_body_r:
    st.markdown('<div class="grid-panel" style="min-height: 250px;">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">⚙️ QUAD-STRATEGY PIPELINE SWITCHES</div>', unsafe_allow_html=True)
    
    cl1, cl2 = st.columns([0.1, 0.9])
    with cl1: mem.strategy_switches["5-STAR LONG"] = st.checkbox("", value=mem.strategy_switches["5-STAR LONG"], key="chk_5_long")
    with cl2: st.markdown('<span class="neon-green-lbl" style="line-height: 2.2;">1. RSI 5-STAR LONG</span>', unsafe_allow_html=True)
        
    cs1, cs2 = st.columns([0.1, 0.9])
    with cs1: mem.strategy_switches["5-STAR SHORT"] = st.checkbox("", value=mem.strategy_switches["5-STAR SHORT"], key="chk_5_short")
    with cs2: st.markdown('<span class="neon-red-lbl" style="line-height: 2.2;">2. RSI 5-STAR SHORT</span>', unsafe_allow_html=True)
        
    cb1, cb2 = st.columns([0.1, 0.9])
    with cb1: mem.strategy_switches["5-STAR BB BUY"] = st.checkbox("", value=mem.strategy_switches["5-STAR BB BUY"], key="chk_bb_buy")
    with cb2: st.markdown('<span class="neon-green-lbl" style="line-height: 2.2;">3. BOLLINGER BUY BREAKOUT</span>', unsafe_allow_html=True)
        
    cx1, cx2 = st.columns([0.1, 0.9])
    with cx1: mem.strategy_switches["5-STAR BB SELL"] = st.checkbox("", value=mem.strategy_switches["5-STAR BB SELL"], key="chk_bb_sell")
    with cx2: st.markdown('<span class="neon-red-lbl" style="line-height: 2.2;">4. BOLLINGER SELL BREAKOUT</span>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-heading">📊 LIVE TERMINAL DIAGNOSTIC REPORT</div>', unsafe_allow_html=True)
st.markdown(f'<div class="diagnostic-logger-container">{"".join(mem.last_terminal_logs)}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# ONBOARD CREDENTIALS SYSTEM
# =====================================================
st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-heading">📁 MASTER ACCOUNT & DELTA API CONTROLLER</div>', unsafe_allow_html=True)

active_user = st.session_state.get("current_user", "Master_Trader")
all_u = load_users()

if "change_api_mode" not in st.session_state:
    st.session_state["change_api_mode"] = False

user_has_keys = active_user in mem.users_db and mem.users_db[active_user].get("api_key") != "" and not st.session_state["change_api_mode"]

if user_has_keys:
    btc_lots = mem.users_db[active_user]["btc_qty"]
    eth_lots = mem.users_db[active_user]["eth_qty"]
    
    st.markdown(f"""
    <table class="terminal-table" style="margin-bottom: 20px;">
        <thead><tr><th>User Profile</th><th>Status</th><th>Allocated Qty (BTC / ETH)</th></tr></thead>
        <tbody><tr>
            <td style="color: #38bdf8; font-weight: bold;">{active_user}</td>
            <td style="color: #39ff14; font-weight: bold; text-shadow: 0px 0px 8px #39ff14;">🟢 KEYS LOCKED & LIVE</td>
            <td style="color: #ffff00; font-weight: bold;">{btc_lots} Lots / {eth_lots} Lots</td>
        </tr></tbody>
    </table>
    """, unsafe_allow_html=True)
    
    with st.form("Quantity Form Controller"):
        qc1, qc2, qc3 = st.columns([2, 2, 1])
        with qc1: new_btc = st.number_input("BTC Qty", min_value=1, value=int(btc_lots))
        with qc2: new_eth = st.number_input("ETH Qty", min_value=1, value=int(eth_lots))
        with qc3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            apply_qty = st.form_submit_button("UPDATE QTY")
        if apply_qty:
            mem.users_db[active_user]["btc_qty"] = new_btc
            mem.users_db[active_user]["eth_qty"] = new_eth
            if active_user in all_u:
                all_u[active_user]["btc_qty"] = new_btc
                all_u[active_user]["eth_qty"] = new_eth
                save_users(all_u)
            add_log(f"Quantity sync complete.")
            st.rerun()

    if st.button("✏️ CHANGE / UPDATE API KEYS", use_container_width=True):
        st.session_state["change_api_mode"] = True
        st.rerun()
else:
    st.markdown("<span style='color: #f59e0b; font-size:12px; font-weight:bold;'>⚙️ ENTER DELTA INDIA API CREDENTIALS BELOW:</span>", unsafe_allow_html=True)
    with st.form("Dashboard Credentials Form"):
        cc1, cc2 = st.columns(2)
        with cc1: u_key = st.text_input("Delta Exchange API Key", type="password")
        with cc2: u_sec = st.text_input("Delta Exchange API Secret Key", type="password")
        
        save_triggered = st.form_submit_button("🔒 LOCK NEW API KEYS AND START ENGINE", use_container_width=True)
        if save_triggered and u_key and u_sec:
            mem.users_db[active_user] = {"api_key": u_key, "api_secret": u_sec, "btc_qty": 4, "eth_qty": 4, "active": True}
            if active_user in all_u:
                all_u[active_user]["api_key"] = u_key
                all_u[active_user]["api_secret"] = u_sec
                save_users(all_u)
            st.session_state["change_api_mode"] = False
            add_log(f"API Credentials updated permanent.", type_icon="🔒")
            st.success("API Keys change successful!")
            st.rerun()
            
    if st.session_state.get("change_api_mode"):
        if st.button("❌ CANCEL CHANGE", use_container_width=True):
            st.session_state["change_api_mode"] = False
            st.rerun()

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
if st.button("🔴 LOGOUT TERMINAL SESSION", use_container_width=True):
    if active_user in mem.users_db: 
        mem.users_db[active_user] = {"api_key": "", "api_secret": "", "btc_qty": 4, "eth_qty": 4, "active": False}
    st.session_state["logged_in"] = False
    st.session_state["current_user"] = None
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# Live dynamic engine page refresh handler
time.sleep(1)
st.rerun()
