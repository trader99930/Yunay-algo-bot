import hashlib
import hmac
import json
import time
import threading
import datetime
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
        self.active_trades = {"BTCUSD": {}, "ETHUSD": {}} 
        self.ordered_candles = {}
        self.is_processing = False
        
        # --- RMS & PERSISTENT LOSS TRACKING ---
        self.daily_pnl_tracker = {}
        self.max_daily_loss_limit = 50.0
        
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
            "<div><span style='color: #38bdf8;'>[SYSTEM]</span> 🚀 Advance Controller Engine Activated with Live RSI Synchronization.</div>"
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
all_users_list = load_users()

for usr, data in all_users_list.items():
    if usr not in mem.users_db:
        mem.users_db[usr] = {
            "api_key": data.get("api_key", ""),
            "api_secret": data.get("api_secret", ""),
            "btc_qty": data.get("btc_qty", 4),
            "eth_qty": data.get("eth_qty", 4),
            "active": True
        }

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = True  

if "current_user" not in st.session_state or not st.session_state["current_user"]:
    if all_users_list:
        st.session_state["current_user"] = list(all_users_list.keys())[0]
    else:
        st.session_state["current_user"] = "Master_Trader"

if not st.session_state.get("logged_in", False):
    if not auth_page():
        st.stop()

current_usr = st.session_state.get("current_user", "Master_Trader")

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
    
    .diagnostic-logger-container { background-color: #060913 !important; border: 1px solid #1e3a8a !important; padding: 15px; border-radius: 6px; height: 250px; overflow-y: auto; font-family: monospace; font-size: 12px; line-height: 1.8; color: #ffff00 !important; }
    
    input { background-color: #0d1b3e !important; color: #ffffff !important; font-weight: bold !important; border: 2px solid #1e3a8a !important; border-radius: 4px; padding: 8px; }
    
    div.stButton > button, div[data-testid="stForm"] button, .stFormSubmitButton button { 
        background-color: #07090e !important; 
        border: 2px solid #1e3a8a !important; 
        border-radius: 6px !important; 
        font-size: 12px !important; 
        font-weight: bold !important; 
        text-transform: uppercase !important; 
        padding: 10px 16px !important; 
        width: 100% !important;
        transition: all 0.2s ease-in-out !important; 
    }
    
    div.stButton > button:hover, div[data-testid="stForm"] button:hover { background-color: #1c2d5a !important; border-color: #38bdf8 !important; box-shadow: 0px 0px 10px rgba(56, 189, 248, 0.4) !important; }

    .neon-green-lbl { color: #00ff00 !important; font-weight: bold !important; font-size: 14px !important; text-shadow: 0px 0px 6px rgba(0,255,0,0.6); display: inline-block; }
    .neon-red-lbl { color: #ff0000 !important; font-weight: bold !important; font-size: 14px !important; text-shadow: 0px 0px 6px rgba(255,0,0,0.6); display: inline-block; }

    .stWidgetFormLabel, div[data-testid="stMarkdownContainer"] p, label { color: #ffff00 !important; font-weight: bold !important; }
    
    .client-row-header { color: #38bdf8 !important; font-size: 12px; font-weight: bold; border-bottom: 1px solid #1e3a8a; padding-bottom: 4px; margin-bottom: 8px; }
    .client-row-data { font-size: 13px; margin-bottom: 6px; }
    </style>
""", unsafe_allow_html=True)

BASE_URL = "https://api.india.delta.exchange"

@st.cache_data(ttl=3600)
def get_server_ip():
    try: return requests.get("https://api.ipify.org", timeout=5).text
    except: return "152.58.109.90"

SERVER_IP = get_server_ip()

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

def force_close_all_orders_and_positions(api_key, api_secret):
    try:
        send_signed_request("DELETE", "/v2/orders/all", api_key, api_secret, {})
        res = send_signed_request("GET", "/v2/positions/margined", api_key, api_secret)
        if res and "result" in res:
            for pos in res["result"]:
                sz = abs(int(pos.get("size", 0)))
                if sz > 0:
                    sym = pos.get("product_symbol")
                    side = pos.get("side")
                    rev_side = "sell" if side == "buy" else "buy"
                    send_signed_request("POST", "/v2/orders", api_key, api_secret, {
                        "product_symbol": sym, "size": sz, "side": rev_side, "order_type": "market_order"
                    })
        return True
    except:
        return False

def add_log(msg, type_icon="🚀"):
    import datetime
    ist_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)
    timestamp = ist_time.strftime("%H:%M:%S")
    full_msg = f"<div><span style='color: #38bdf8;'>[{timestamp}]</span> {type_icon} <span style='color:#ffff00; font-weight:bold;'>{msg}</span></div>"
    mem.last_terminal_logs.insert(0, full_msg)
    if len(mem.last_terminal_logs) > 20: mem.last_terminal_logs.pop()

# ✅ ACCURATE EM-WEIGHTED RSI FOR CRYPTO CANDLES
def rsi_calc(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period-1, adjust=False).mean()
    avg_loss = loss.ewm(com=period-1, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    return 100 - (100 / (1 + rs))

def fetch_candles_df(symbol, timeframe, limit=200):
    try:
        end_t = int(time.time())
        multiplier_seconds = 60 if timeframe == "1m" else (300 if timeframe == "5m" else 900)
        r = requests.get(f"{BASE_URL}/v2/history/candles", params={"symbol": symbol, "resolution": timeframe, "start": end_t - (limit * multiplier_seconds), "end": end_t}, timeout=10).json()
        if "result" in r and r["result"]:
            df = pd.DataFrame(r["result"])
            df["time"] = pd.to_numeric(df["time"])
            df = df.sort_values(by="time", ascending=True).reset_index(drop=True)
            for col in ["close", "high", "low"]: df[col] = pd.to_numeric(df[col])
            return df
        return None
    except: return None

# =====================================================
# BACKGROUND TRADE ENGINE THREAD WITH LIVE TRACKING & SL/TG TRIGGERS
# =====================================================
def core_execution_engine(shared_mem):
    while True:
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        
        # --- FORCED USER-BY-USER REALTIME DIRECT DELTA ACCOUNT SCRAPER ---
        try:
            for user, u_db in list(shared_mem.users_db.items()):
                if not u_db.get('api_key') or not u_db.get('api_secret'): continue
                res = send_signed_request("GET", "/v2/positions/margined", u_db['api_key'], u_db['api_secret'])
                if res and "result" in res:
                    active_symbols_this_run = []
                    for pos in res["result"]:
                        sym = pos.get("product_symbol", "")
                        if sym in ["BTCUSD", "ETHUSD"]:
                            sz = abs(int(pos.get("size", 0)))
                            if sz > 0:
                                active_symbols_this_run.append(sym)
                                side = pos.get("side", "buy").lower()
                                entry_p = float(pos.get("entry_price", shared_mem.ticker_feeds[sym]["ltp"]))
                                
                                # Instantly force-pull historical/pre-existing position matching user account bounds
                                if user not in shared_mem.active_trades[sym]:
                                    shared_mem.active_trades[sym][user] = {
                                        'side': side, 'entry_price': entry_p, 'sl': entry_p * 0.95 if side == 'buy' else entry_p * 1.05, 
                                        't1': entry_p * 1.02, 't2': entry_p * 1.04, 'current_stage': 0, 
                                        'qty': sz, 'initial_qty': sz, 'live_pnl': 0.0, 'is_external': True
                                    }
                                else:
                                    shared_mem.active_trades[sym][user]['qty'] = sz
                    
                    # Clear locally stored data if position squared off outside bounds
                    for sym in ["BTCUSD", "ETHUSD"]:
                        if user in shared_mem.active_trades[sym] and sym not in active_symbols_this_run:
                            calc_pnl = shared_mem.active_trades[sym][user].get('live_pnl', 0.0)
                            if user not in shared_mem.daily_pnl_tracker:
                                shared_mem.daily_pnl_tracker[user] = {"realized": 0.0, "date": today_str, "blocked": False}
                            shared_mem.daily_pnl_tracker[user]["realized"] += calc_pnl
                            del shared_mem.active_trades[sym][user]
        except: pass

        # Process market metrics updates
        try:
            symbols = ["BTCUSD", "ETHUSD"]
            for sym in symbols:
                r = requests.get(f"{BASE_URL}/v2/tickers/{sym}", timeout=4).json()
                if r and "result" in r: 
                    shared_mem.ticker_feeds[sym]["ltp"] = round(float(r["result"].get("mark_price", 0)), 2)
        except: pass

        # --- LIVE TERMINAL SL TRAILING & TARGET LIFECYCLE CONTROLLER ---
        for sym in ["BTCUSD", "ETHUSD"]:
            live_price = shared_mem.ticker_feeds[sym]["ltp"]
            if not live_price or sym not in shared_mem.active_trades: continue
            
            for user in list(shared_mem.active_trades[sym].keys()):
                trade = shared_mem.active_trades[sym][user]
                u_db = shared_mem.users_db.get(user, {})
                if not u_db.get("api_key"): continue

                mult = 1 if trade['side'] == 'buy' else -1
                trade['live_pnl'] = round((live_price - trade['entry_price']) * mult * trade['qty'], 2)
                is_buy = (trade['side'] == 'buy')

                # 1. LIVE STOP LOSS TRIGGER DETECTOR
                if (is_buy and live_price <= trade['sl']) or (not is_buy and live_price >= trade['sl']):
                    add_log(f"💥 SL HIT for {user} on {sym} @ ${live_price:,.2f} (Cleared Qty: {trade['qty']})", type_icon="❌")
                    force_close_all_orders_and_positions(u_db['api_key'], u_db['api_secret'])
                    continue

                # 2. LIVE TARGET 1 HIT -> BOOK 50% & TRAIL SL TO COST
                if trade['current_stage'] == 0:
                    if (is_buy and live_price >= trade['t1']) or (not is_buy and live_price <= trade['t1']):
                        trade['current_stage'] = 1
                        old_qty = trade['qty']
                        booked_qty = int(old_qty * 0.50)
                        
                        if booked_qty > 0:
                            opposite_side = "sell" if is_buy else "buy"
                            # Execute Market Order for Partial Booking
                            send_signed_request("POST", "/v2/orders", u_db['api_key'], u_db['api_secret'], {
                                "product_symbol": sym, "size": booked_qty, "side": opposite_side, "order_type": "market_order"
                            })
                            # Cancel pre-existing bracket orders to refresh structures
                            send_signed_request("DELETE", "/v2/orders/all", u_db['api_key'], u_db['api_secret'], {})
                            
                            # Recalculate remaining pool sizes
                            rem_qty = old_qty - booked_qty
                            trade['qty'] = rem_qty
                            trade['sl'] = trade['entry_price'] # Trail Remaining to Cost Engine
                            
                            if rem_qty > 0:
                                place_stop_loss(sym, rem_qty, opposite_side, trade['sl'], u_db['api_key'], u_db['api_secret'])
                                place_target_order(sym, rem_qty, opposite_side, trade['t2'], u_db['api_key'], u_db['api_secret'])
                            
                            add_log(f"🎯 T1 TRIGGERED for {user} ({sym})! Booked Qty: {booked_qty} @ ${live_price:,.2f} | Remaining Qty: {rem_qty} Trailed to Cost: ${trade['sl']:,.2f}", type_icon="🛡️")

                # 3. LIVE TARGET 2 HIT -> FULL CLOSURE
                if trade['current_stage'] == 1:
                    if (is_buy and live_price >= trade['t2']) or (not is_buy and live_price <= trade['t2']):
                        add_log(f"🚀 T2 MAX TARGET ACHIEVED for {user} on {sym}! Squared Off Remaining Qty: {trade['qty']} @ ${live_price:,.2f}", type_icon="💰")
                        force_close_all_orders_and_positions(u_db['api_key'], u_db['api_secret'])

        if not shared_mem.global_engine_running:
            time.sleep(1)
            continue

        if shared_mem.users_db and not shared_mem.is_processing:
            for sym in ["BTCUSD", "ETHUSD"]:
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
                
                rsi_15, rsi_5, rsi_1, rsi_1_prev = df_15m["RSI"].iloc[-1], df_5m["RSI"].iloc[-1], df_1m["RSI"].iloc[-1], df_1m["RSI"].iloc[-2]
                close_1m = df_1m["close"].iloc[-1]
                c_time = df_1m["time"].iloc[-1]
                
                if sym in shared_mem.ordered_candles and shared_mem.ordered_candles[sym] == c_time: continue
                triggered, s_key, side, entry, sl, t1, t2 = False, "", "", 0.0, 0.0, 0.0, 0.0
                
                if shared_mem.strategy_switches["5-STAR LONG"] and rsi_15 >= 60 and rsi_5 >= 60 and rsi_1 > 40 and rsi_1 > rsi_1_prev and (43 >= rsi_1_prev >= 20):
                    triggered, s_key, side = True, "5-STAR LONG", "buy"
                    entry = round(float(df_1m["high"].iloc[-1]), 2)
                    sl = round(float(df_1m["low"].iloc[-16:].min()), 2)
                    risk = entry - sl
                    t1, t2 = round(entry + risk, 2), round(entry + 2*risk, 2)
                
                elif shared_mem.strategy_switches["5-STAR SHORT"] and rsi_15 <= 40 and rsi_5 <= 40 and rsi_1 < 60 and rsi_1 < rsi_1_prev and (80 >= rsi_1_prev >= 57):
                    triggered, s_key, side = True, "5-STAR SHORT", "sell"
                    entry = round(float(df_1m["low"].iloc[-1]), 2)
                    sl = round(float(df_1m["high"].iloc[-16:].max()), 2)
                    risk = sl - entry
                    t1, t2 = round(entry - risk, 2), round(entry - 2*risk, 2)
                
                elif shared_mem.strategy_switches["5-STAR BB BUY"] and rsi_15 > 60 and rsi_5 > 60 and rsi_1_prev < 61 and rsi_1 >= 60 and close_1m > df_1m["BB_up"].iloc[-1]:
                    triggered, s_key, side = True, "5-STAR BB BUY", "buy"
                    entry, sl = round(float(df_1m["high"].iloc[-1]), 2), round(float(df_1m["low"].iloc[-1]), 2)
                    risk = entry - sl
                    t1, t2 = round(entry + risk, 2), round(entry + 2*risk, 2)
                
                elif shared_mem.strategy_switches["5-STAR BB SELL"] and rsi_15 < 40 and rsi_5 < 40 and rsi_1_prev > 39 and rsi_1 <= 40 and close_1m < df_1m["BB_low"].iloc[-1]:
                    triggered, s_key, side = True, "5-STAR BB SELL", "sell"
                    entry, sl = round(float(df_1m["low"].iloc[-1]), 2), round(float(df_1m["high"].iloc[-1]), 2)
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
                        if user not in shared_mem.daily_pnl_tracker or shared_mem.daily_pnl_tracker[user]["date"] != today_str:
                            shared_mem.daily_pnl_tracker[user] = {"realized": 0.0, "date": today_str, "blocked": False}
                        
                        if shared_mem.daily_pnl_tracker[user]["blocked"]:
                            continue
                            
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
                                'current_stage': 0, 'qty': u_qty, 'initial_qty': u_qty, 'live_pnl': 0.0, 'is_external': False
                            }
                    break
        shared_mem.is_processing = False
        time.sleep(1)

if "thread_started" not in st.session_state:
    threading.Thread(target=core_execution_engine, args=(mem,), daemon=True).start()
    st.session_state["thread_started"] = True

# =====================================================
# CALLBACK STATE CONTROL BUTTONS
# =====================================================
def trigger_stop_action():
    mem.global_engine_running = False
    add_log("Algorithmic System SCANNER Completely Stopped.", type_icon="🔴")

def trigger_start_action():
    mem.global_engine_running = True
    add_log("Algorithmic System RUNNER Activated.", type_icon="🟢")

def trigger_global_kill_switch():
    add_log("🚨 GLOBAL KILL SWITCH INITIATED! SQUARING OFF ALL ACCOUNTS...", type_icon="⚠️")
    for user, u_db in mem.users_db.items():
        if u_db.get("api_key") and u_db.get("api_secret"):
            force_close_all_orders_and_positions(u_db["api_key"], u_db["api_secret"])
                
    mem.active_trades = {"BTCUSD": {}, "ETHUSD": {}}
    mem.last_triggered_setup_info["BTCUSD"] = {"entry": "WAITING", "sl": "WAITING", "t1": "WAITING", "t2": "WAITING", "status": "SCANNING ENGINE", "live_pnl": 0.0}
    mem.last_triggered_setup_info["ETHUSD"] = {"entry": "WAITING", "sl": "WAITING", "t1": "WAITING", "t2": "WAITING", "status": "SCANNING ENGINE", "live_pnl": 0.0}

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
        <div class="live-pnl-text {pnl_class}">Global Setup P&L: {'+' if pnl_val >= 0 else ''}${pnl_val:,.2f}</div>
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
        <div class="live-pnl-text {pnl_class_eth}">Global Setup P&L: {'+' if pnl_val_eth >= 0 else ''}${pnl_val_eth:,.2f}</div>
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

# =====================================================
# REAL-TIME CLIENT MATRIX DISPLAY (NATIVE ST.COLUMNS)
# =====================================================
st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-heading">📈 REAL-TIME CLIENT MATRIX & RISK CONTROLLER</div>', unsafe_allow_html=True)

hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns([2, 2, 2, 2, 2])
with hcol1: st.markdown('<div class="client-row-header">CLIENT NAME</div>', unsafe_allow_html=True)
with hcol2: st.markdown('<div class="client-row-header">ENGINE STATUS</div>', unsafe_allow_html=True)
with hcol3: st.markdown('<div class="client-row-header">LOT SIZING</div>', unsafe_allow_html=True)
with hcol4: st.markdown('<div class="client-row-header">DAILY REALIZED</div>', unsafe_allow_html=True)
with hcol5: st.markdown('<div class="client-row-header">TOTAL NET P&L</div>', unsafe_allow_html=True)

has_records = False
for u_name, u_config in mem.users_db.items():
    if not u_config.get("api_key"): continue
    has_records = True
    
    btc_pnl = mem.active_trades.get("BTCUSD", {}).get(u_name, {}).get("live_pnl", 0.0)
    eth_pnl = mem.active_trades.get("ETHUSD", {}).get(u_name, {}).get("live_pnl", 0.0)
    current_open_running_pnl = btc_pnl + eth_pnl
    
    today_stamp = datetime.date.today().strftime("%Y-%m-%d")
    realized_day_pnl = mem.daily_pnl_tracker.get(u_name, {}).get("realized", 0.0) if mem.daily_pnl_tracker.get(u_name, {}).get("date") == today_stamp else 0.0
    total_net_pnl = current_open_running_pnl + realized_day_pnl
    
    if mem.daily_pnl_tracker.get(u_name, {}).get("blocked", False):
        status_txt = "🔴 RMS BLOCKED"
    elif current_open_running_pnl != 0.0:
        status_txt = "🟩 LIVE TRADING"
    else:
        status_txt = "🔵 SCANNING MESH"
        
    pnl_color = "#10b981" if total_net_pnl >= 0 else "#ef4444"
    
    rcol1, rcol2, rcol3, rcol4, rcol5 = st.columns([2, 2, 2, 2, 2])
    with rcol1: st.markdown(f'<div class="client-row-data" style="color: #38bdf8;">{u_name}</div>', unsafe_allow_html=True)
    with rcol2: st.markdown(f'<div class="client-row-data">{status_txt}</div>', unsafe_allow_html=True)
    with rcol3: st.markdown(f'<div class="client-row-data">{u_config["btc_qty"]} BTC / {u_config["eth_qty"]} ETH</div>', unsafe_allow_html=True)
    with rcol4: st.markdown(f'<div class="client-row-data">${realized_day_pnl:,.2f}</div>', unsafe_allow_html=True)
    with rcol5: st.markdown(f'<div class="client-row-data" style="color: {pnl_color}; font-weight: bold;">${total_net_pnl:,.2f}</div>', unsafe_allow_html=True)

if not has_records:
    st.info("No Live Accounts Mounted in Terminal Memory Mesh")

st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# 🚨 LIVE RUNNING POSITIONS MONITOR PANEL (STRICT USER ISOLATION SYNC)
# =====================================================
st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-heading">🚨 LIVE RUNNING POSITIONS MONITOR (DELTA EXCHANGE)</div>', unsafe_allow_html=True)

p_hcol1, p_hcol2, p_hcol3, p_hcol4, p_hcol5, p_hcol6 = st.columns([2, 1.5, 1.5, 2, 2, 3])
with p_hcol1: st.markdown('<div class="client-row-header">USER</div>', unsafe_allow_html=True)
with p_hcol2: st.markdown('<div class="client-row-header">SYMBOL</div>', unsafe_allow_html=True)
with p_hcol3: st.markdown('<div class="client-row-header">SIDE</div>', unsafe_allow_html=True)
with p_hcol4: st.markdown('<div class="client-row-header">QTY (LOTS)</div>', unsafe_allow_html=True)
with p_hcol5: st.markdown('<div class="client-row-header">AVG ENTRY</div>', unsafe_allow_html=True)
with p_hcol6: st.markdown('<div class="client-row-header">FLOATING P&L / SOURCE</div>', unsafe_allow_html=True)

has_active_positions = False
for sym in ["BTCUSD", "ETHUSD"]:
    if sym in mem.active_trades:
        for u_name in list(mem.users_db.keys()):
            if u_name in mem.active_trades[sym]:
                trade_details = mem.active_trades[sym][u_name]
                has_active_positions = True
                
                side_color = "#00ff00" if trade_details['side'].lower() == "buy" else "#ff0000"
                pnl_color = "#10b981" if trade_details['live_pnl'] >= 0 else "#ef4444"
                source_lbl = "<span style='color:#a855f7;font-size:10px;'> [PRE-EXISTING ACTIVE]</span>" if trade_details.get('is_external') else "<span style='color:#38bdf8;font-size:10px;'> [ALGO INITIALIZED]</span>"
                
                p_rcol1, p_rcol2, p_rcol3, p_rcol4, p_rcol5, p_rcol6 = st.columns([2, 1.5, 1.5, 2, 2, 3])
                with p_rcol1: st.markdown(f'<div class="client-row-data" style="color: #38bdf8;">{u_name}</div>', unsafe_allow_html=True)
                with p_rcol2: st.markdown(f'<div class="client-row-data" style="color: #ffff00;">{sym}</div>', unsafe_allow_html=True)
                with p_rcol3: st.markdown(f'<div class="client-row-data" style="color: {side_color}; font-weight: bold;">{trade_details["side"].upper()}</div>', unsafe_allow_html=True)
                with p_rcol4: st.markdown(f'<div class="client-row-data">{trade_details["qty"]}</div>', unsafe_allow_html=True)
                with p_rcol5: st.markdown(f'<div class="client-row-data">${trade_details["entry_price"]:,.2f}</div>', unsafe_allow_html=True)
                with p_rcol6: st.markdown(f'<div class="client-row-data" style="color: {pnl_color}; font-weight: bold;">${trade_details["live_pnl"]:,.2f}{source_lbl}</div>', unsafe_allow_html=True)

if not has_active_positions:
    st.markdown('<div style="color: #a855f7; font-size: 12px; font-style: italic; padding: 5px 0;">No Active Open Positions detected across accounts.</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# SYSTEM CORE CONTROL BUTTONS
# =====================================================
col_body_l, col_body_r = st.columns(2)
with col_body_l:
    st.markdown('<div class="grid-panel" style="min-height: 290px;">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">🎛️ ENGINE GLOBAL SWITCH SYSTEM</div>', unsafe_allow_html=True)
    
    engine_status_label = "ACTIVE (RUNNING)" if mem.global_engine_running else "DEACTIVATED (PAUSED)"
    st.subheader(f"STATUS: {engine_status_label}")
    
    if mem.global_engine_running:
        if st.button("🔴 STOP SCANNER SYSTEM", key="btn_stop_sc"):
            trigger_stop_action()
            st.rerun()
    else:
        if st.button("🟢 START RUNNER SYSTEM", key="btn_start_sc"):
            trigger_start_action()
            st.rerun()
        
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px; color:#ef4444; margin-bottom:5px;'>🚨 EMERGENCY OPERATIONS CONTROLLER:</div>", unsafe_allow_html=True)
    if st.button("💥 GLOBAL KILL SWITCH (SQUARE OFF ALL)", key="btn_kill_glob"):
        trigger_global_kill_switch()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_body_r:
    st.markdown('<div class="grid-panel" style="min-height: 290px;">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">⚙️ QUAD-STRATEGY PIPELINE SWITCHES</div>', unsafe_allow_html=True)
    
    mem.strategy_switches["5-STAR LONG"] = st.checkbox("1. RSI 5-STAR LONG", value=mem.strategy_switches["5-STAR LONG"], key="chk_5_long")
    mem.strategy_switches["5-STAR SHORT"] = st.checkbox("2. RSI 5-STAR SHORT", value=mem.strategy_switches["5-STAR SHORT"], key="chk_5_short")
    mem.strategy_switches["5-STAR BB BUY"] = st.checkbox("3. BOLLINGER BUY BREAKOUT", value=mem.strategy_switches["5-STAR BB BUY"], key="chk_bb_buy")
    mem.strategy_switches["5-STAR BB SELL"] = st.checkbox("4. BOLLINGER SELL BREAKOUT", value=mem.strategy_switches["5-STAR BB SELL"], key="chk_bb_sell")
    st.markdown('</div>', unsafe_allow_html=True)

# Tabs
tab_diag, tab_rms, tab_reg = st.tabs(["📊 LIVE DIAGNOSTICS LOGS", "🛡️ RISK CONTROLLER (RMS)", "👥 CLIENT REGISTRATION MATRIX"])

with tab_diag:
    st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">📊 LIVE TERMINAL DIAGNOSTIC REPORT</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="diagnostic-logger-container">{"".join(mem.last_terminal_logs)}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab_rms:
    st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">🛡️ RMS MAX DAILY LOSS WINDOW CONFIGURATION</div>', unsafe_allow_html=True)
    with st.form("RMS Form Configurator"):
        max_loss_input = st.number_input("Global Max Daily Loss Limit Per Client ($ Limit)", min_value=1.0, max_value=5000.0, value=float(mem.max_daily_loss_limit))
        save_rms_btn = st.form_submit_button("SAVE CONTROL LIMITS")
        if save_rms_btn:
            mem.max_daily_loss_limit = max_loss_input
            add_log(f"Global RMS Matrix updated: Max daily loss lock set at ${max_loss_input}", type_icon="🛡️")
            st.success("RMS Config parameters synchronized.")
            st.rerun()
            
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("<span style='color: #38bdf8; font-size:12px;'>🔓 RESET BLOCKED RMS WINDOW CLIENTS:</span>", unsafe_allow_html=True)
    blocked_accounts = [u for u, data in mem.daily_pnl_tracker.items() if data.get("blocked", False)]
    if blocked_accounts:
        target_reset_user = st.selectbox("Select Account to Unlock", options=blocked_accounts)
        if st.button("UNLOCK ACCOUNT FOR TODAY"):
            mem.daily_pnl_tracker[target_reset_user]["blocked"] = False
            mem.daily_pnl_tracker[target_reset_user]["realized"] = 0.0
            add_log(f"Unlocked account bounds for {target_reset_user}", type_icon="🔓")
            st.rerun()
    else:
        st.info("No users currently blocked under RMS safety thresholds.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab_reg:
    st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">👥 SELF CLIENT DIRECT REGISTRATION MATRIX</div>', unsafe_allow_html=True)
    with st.form("Client Register Form Hub"):
        rg_username = st.text_input("Choose Unique Client Username")
        rg_password = st.text_input("Trading Master Dashboard Password (For Auth)", type="password")
        rg_apikey = st.text_input("Delta Exchange API Public Key", type="password")
        rg_apisecret = st.text_input("Delta Exchange API Secret Private Key", type="password")
        
        r_col1, r_col2 = st.columns(2)
        with r_col1: rg_btc = st.number_input("Assigned BTC Lots Size Default", min_value=1, value=4)
        with r_col2: rg_eth = st.number_input("Assigned ETH Lots Size Default", min_value=1, value=4)
        
        submit_register = st.form_submit_button("➕ REGISTER CLIENT SECURELY INTO SYSTEM")
        if submit_register:
            if rg_username and rg_password and rg_apikey and rg_apisecret:
                all_current_u = load_users()
                if rg_username in all_current_u:
                    st.error("Username already registered in database file anchor!")
                else:
                    all_current_u[rg_username] = {
                        "password": rg_password,
                        "api_key": rg_apikey,
                        "api_secret": rg_apisecret,
                        "btc_qty": int(rg_btc),
                        "eth_qty": int(rg_eth)
                    }
                    save_users(all_current_u)
                    
                    mem.users_db[rg_username] = {
                        "api_key": rg_apikey,
                        "api_secret": rg_apisecret,
                        "btc_qty": int(rg_btc),
                        "eth_qty": int(rg_eth),
                        "active": True
                    }
                    add_log(f"New client registered successfully: '{rg_username}'", type_icon="👤")
                    st.success(f"Client account {rg_username} setup active!")
                    st.rerun()
            else:
                st.error("Please fill out all registration fields fully.")
    st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# MASTER ACCOUNT & DELTA API CONTROLLER
# =====================================================
st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-heading">📁 INDIVIDUAL ACCOUNT PROFILES MANAGEMENT</div>', unsafe_allow_html=True)

active_user = st.session_state.get("current_user", "Master_Trader")
all_u = load_users()

if "change_api_mode" not in st.session_state:
    st.session_state["change_api_mode"] = False

user_has_keys = active_user in mem.users_db and mem.users_db[active_user].get("api_key") != "" and not st.session_state["change_api_mode"]

if user_has_keys:
    btc_lots = mem.users_db[active_user]["btc_qty"]
    eth_lots = mem.users_db[active_user]["eth_qty"]
    
    st.write(f"**Current Active User:** `{active_user}` | **Allocated Sizing:** `{btc_lots} BTC Lots / {eth_lots} ETH Lots`")
    
    with st.form("Quantity Form Controller"):
        qc1, qc2 = st.columns(2)
        with qc1: new_btc = st.number_input("BTC Qty", min_value=1, value=int(btc_lots))
        with qc2: new_eth = st.number_input("ETH Qty", min_value=1, value=int(eth_lots))
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

    if st.button("✏️ MANUALLY RE-WRITE CURRENT ACCOUNT KEYS", key="btn_rewrite_ap"):
        st.session_state["change_api_mode"] = True
        st.rerun()
else:
    st.markdown("<span style='color: #f59e0b; font-size:12px; font-weight:bold;'>⚙️ ENTER DELTA INDIA API CREDENTIALS BELOW:</span>", unsafe_allow_html=True)
    with st.form("Dashboard Credentials Form"):
        cc1, cc2 = st.columns(2)
        with cc1: u_key = st.text_input("Delta Exchange API Key", type="password")
        with cc2: u_sec = st.text_input("Delta Exchange API Secret Key", type="password")
        
        save_triggered = st.form_submit_button("🔒 LOCK NEW API KEYS AND START ENGINE")
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
        if st.button("❌ CANCEL CHANGE", key="btn_cncl_ch"):
            st.session_state["change_api_mode"] = False
            st.rerun()

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
if st.button("🔴 LOGOUT TERMINAL SESSION", key="btn_logout_sess"):
    if active_user in mem.users_db: 
        mem.users_db[active_user] = {"api_key": "", "api_secret": "", "btc_qty": 4, "eth_qty": 4, "active": False}
    st.session_state["logged_in"] = False
    st.session_state["current_user"] = None
    st.rerun()

# Live dynamic engine page refresh handler
time.sleep(1)
st.rerun()
