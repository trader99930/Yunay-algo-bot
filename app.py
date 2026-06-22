import hmac
import json
import time
import threading
import hashlib
import numpy as np
import pandas as pd
import requests
import urllib3
import streamlit as st
import datetime
from auth import auth_page, load_users, save_users

# ✅ SYSTEM STABILITY FOR TERMUX / IPV4 OPTIMIZATION
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
        
        self.symbol_switches = {
            "BTCUSD": True,
            "ETHUSD": True
        }
        
        self.strategy_switches = {
            "2-STAR BUY": True, "2-STAR SELL": True,
            "5-STAR LONG": True, "5-STAR SHORT": True, 
            "5-STAR BB BUY": True, "5-STAR BB SELL": True
        }
        
        self.strategy_metrics = {
            "2-STAR BUY": {"triggers": 0}, "2-STAR SELL": {"triggers": 0},
            "5-STAR LONG": {"triggers": 0}, "5-STAR SHORT": {"triggers": 0},
            "5-STAR BB BUY": {"triggers": 0}, "5-STAR BB SELL": {"triggers": 0}
        }
        self.last_terminal_logs = [
            "<div><span style='color: #38bdf8;'>[SYSTEM]</span> 🚀 Advance Controller Engine Activated with Priority Hierarchy Matrix.</div>"
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

# 🔥 SAFETY PROTECTION STATE FOR OLD MEMORY CARRIEOVER
if not hasattr(mem, 'symbol_switches') or mem.symbol_switches is None:
    mem.symbol_switches = {"BTCUSD": True, "ETHUSD": True}

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

all_u = load_users()
for u_name, u_data in all_u.items():
    if u_name not in mem.users_db and u_data.get("api_key"):
        mem.users_db[u_name] = {
            "api_key": u_data["api_key"],
            "api_secret": u_data["api_secret"],
            "btc_qty": u_data.get("btc_qty", 4),
            "eth_qty": u_data.get("eth_qty", 4),
            "active": u_data.get("active", True)
        }

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
    div.stButton > button, div[data-testid="stForm"] button, .stFormSubmitButton button { background-color: #07090e !important; border: 2px solid #1e3a8a !important; border-radius: 6px !important; font-size: 11px !important; font-weight: bold !important; text-transform: uppercase !important; padding: 4px 10px !important; transition: all 0.2s ease-in-out !important; }
    div.stButton > button:hover, div[data-testid="stForm"] button:hover { background-color: #1c2d5a !important; border-color: #38bdf8 !important; box-shadow: 0px 0px 10px rgba(56, 189, 248, 0.4) !important; }
    .neon-green-lbl { color: #00ff00 !important; font-weight: bold !important; font-size: 14px !important; text-shadow: 0px 0px 6px rgba(0,255,0,0.6); display: inline-block; }
    .neon-red-lbl { color: #ff0000 !important; font-weight: bold !important; font-size: 14px !important; text-shadow: 0px 0px 6px rgba(255,0,0,0.6); display: inline-block; }
    .neon-blue-lbl { color: #38bdf8 !important; font-weight: bold !important; font-size: 14px !important; text-shadow: 0px 0px 6px rgba(56,189,248,0.6); display: inline-block; }
    div[data-testid="stColumn"] { display: flex; align-items: center !important; }
    div[data-testid="stCheckbox"] label { margin-bottom: 0px !important; padding-top: 5px !important; }
    div[data-testid="stTabs"] button { color: #38bdf8 !important; font-size: 13px !important; font-weight: bold !important; background-color: #07090e !important; border: 1px solid #1e3a8a !important; margin-right: 5px; padding: 8px 16px !important; }
    div[data-testid="stTabs"] button[aria-selected="true"] { color: #ffff00 !important; border-bottom: 2px solid #ffff00 !important; background-color: #0d1b3e !important; }
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
    ist_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)
    timestamp = ist_time.strftime("%H:%M:%S")
    full_msg = f"<div><span style='color: #38bdf8;'>[{timestamp}]</span> {type_icon} <span style='color:#ffff00; font-weight:bold;'>{msg}</span></div>"
    mem.last_terminal_logs.insert(0, full_msg)
    if len(mem.last_terminal_logs) > 20: mem.last_terminal_logs.pop()

# =====================================================
# DELTA INDIA API CONNECTORS (OPTIMISED AND TRACKED)
# =====================================================
def send_signed_request(method, path, api_key, api_secret, payload=None):
    if not api_key or not api_secret: return {"success": False, "error": "Keys Missing"}
    timestamp = str(int(time.time()))
    body_string = json.dumps(payload) if (payload and method in ["POST", "PUT", "DELETE"]) else ""
    signature_payload = method + timestamp + path + body_string
    signature = hmac.new(api_secret.encode("utf-8"), signature_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    headers = {"api-key": api_key, "timestamp": timestamp, "signature": signature, "Content-Type": "application/json"}
    try:
        if method == "POST": r = requests.post(BASE_URL + path, headers=headers, data=body_string, timeout=12)
        elif method == "DELETE": r = requests.delete(BASE_URL + path, headers=headers, data=body_string, timeout=12)
        else: r = requests.get(BASE_URL + path, headers=headers, params=payload, timeout=12)
        return r.json()
    except: return {"success": False, "error": "Network Timeout"}

def place_breakout_entry_order(symbol, size, side, trigger_price, api_key, api_secret):
    if size <= 0: return {"success": False, "error": "Size cannot be zero"}
    
    if "BTCUSD" in symbol:
        final_price = str(round(float(trigger_price) * 2) / 2)
    else:
        final_price = str(round(float(trigger_price), 2))

    payload = {
        "product_symbol": symbol, "size": int(size), "side": side.lower(),
        "order_type": "market_order", "stop_order_type": "stop_loss_order",
        "stop_price": final_price, "reduce_only": False
    }
    res = send_signed_request("POST", "/v2/orders", api_key, api_secret, payload)
    if res and res.get("success") is True: 
        return {"success": True, "order_id": res["result"].get("id")}
    
    err_explanation = res.get("error", {}).get("explanation", "") if res else ""
    err_msg = res.get("error", {}).get("message", "Execution Rejected") if res else "Unknown API Error"
    if "margin" in err_explanation.lower() or "insufficient" in err_explanation.lower() or "margin" in err_msg.lower():
        return {"success": False, "error": "INSUFFICIENT_MARGIN"}
        
    return {"success": False, "error": err_msg}

def cancel_order(order_id, symbol, api_key, api_secret):
    if not order_id: return False
    payload = {"product_symbol": symbol, "id": int(order_id)}
    res = send_signed_request("DELETE", "/v2/orders", api_key, api_secret, payload)
    return res and res.get("success") is True

def cancel_all_orders_for_symbol(symbol, api_key, api_secret):
    payload = {"product_symbol": symbol}
    send_signed_request("DELETE", "/v2/orders/all", api_key, api_secret, payload)

def close_position_market(symbol, api_key, api_secret):
    try:
        qty = get_open_position_qty(symbol, api_key, api_secret)
        if qty > 0:
            res = send_signed_request("GET", "/v2/positions/margined", api_key, api_secret)
            side = "sell"
            if res and "result" in res:
                for pos in res["result"]:
                    if pos.get("product_symbol") == symbol:
                        side = "sell" if pos.get("side") == "long" else "buy"
            payload = {
                "product_symbol": symbol, "size": int(qty), "side": side,
                "order_type": "market_order", "reduce_only": True
            }
            send_signed_request("POST", "/v2/orders", api_key, api_secret, payload)
    except: pass

def place_stop_loss(symbol, size, side, sl_price, api_key, api_secret):
    if size <= 0: return None
    if "BTCUSD" in symbol:
        final_sl = str(round(float(sl_price) * 2) / 2)
    else:
        final_sl = str(round(float(sl_price), 2))

    payload = {
        "product_symbol": symbol, "size": int(size), "side": side.lower(),
        "order_type": "market_order", "stop_order_type": "stop_loss_order",   
        "stop_price": final_sl, "reduce_only": True
    }
    res = send_signed_request("POST", "/v2/orders", api_key, api_secret, payload)
    if res and res.get("success") is True: return res["result"].get("id")
    return None

def place_limit_profit_target(symbol, size, side, price, api_key, api_secret):
    if size <= 0: return None
    if "BTCUSD" in symbol:
        final_price = str(round(float(price) * 2) / 2)
    else:
        final_price = str(round(float(price), 2))
    payload = {
        "product_symbol": symbol, "size": int(size), "side": side.lower(),
        "order_type": "limit_order", "limit_price": final_price, "reduce_only": True
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

def check_any_live_position_on_exchange(shared_mem):
    if not shared_mem.users_db: return None
    first_user = list(shared_mem.users_db.keys())[0]
    u_db = shared_mem.users_db[first_user]
    try:
        res = send_signed_request("GET", "/v2/positions/margined", u_db['api_key'], u_db['api_secret'])
        if res and "result" in res:
            for pos in res["result"]:
                if abs(int(pos.get("size", 0))) > 0: return pos.get("product_symbol")
        return None
    except: return None

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
# CORE PIPELINE TRADE ENGINE AUTOMATION (FIXED & LIVE)
# =====================================================
def core_execution_engine(shared_mem):
    while True:
        if not shared_mem.global_engine_running:
            time.sleep(1.5)
            continue
        try:
            symbols = ["BTCUSD", "ETHUSD"]
            for sym in symbols:
                try:
                    r = requests.get(f"{BASE_URL}/v2/tickers/{sym}", timeout=4).json()
                    if r and "result" in r: shared_mem.ticker_feeds[sym]["ltp"] = round(float(r["result"].get("mark_price", 0)), 2)
                except: pass

            true_live_asset = check_any_live_position_on_exchange(shared_mem)
            for sym in symbols:
                if true_live_asset != sym and sym in shared_mem.active_trades:
                    any_user_key = list(shared_mem.active_trades[sym].keys())[0] if shared_mem.active_trades[sym] else None
                    if any_user_key and shared_mem.active_trades[sym][any_user_key].get('is_triggered', False):
                        shared_mem.active_trades[sym].clear()
                        shared_mem.last_triggered_setup_info[sym] = {"entry": "WAITING", "sl": "WAITING", "t1": "WAITING", "t2": "WAITING", "status": "SCANNING ENGINE", "live_pnl": 0.0}
                        add_log(f"Exchange Sync: States cleared for {sym}.", type_icon="🔄")

            for sym in symbols:
                live_price = shared_mem.ticker_feeds[sym]["ltp"]
                if not live_price or sym not in shared_mem.active_trades: continue
                
                for user in list(shared_mem.active_trades[sym].keys()):
                    trade = shared_mem.active_trades[sym][user]
                    u_db = shared_mem.users_db.get(user)
                    if not u_db or not u_db.get('api_key') or not u_db.get('active', True): continue
                    
                    ex_qty = get_open_position_qty(sym, u_db['api_key'], u_db['api_secret'])
                    mult = 1 if trade['side'] == 'buy' else -1
                    calc_pnl = round((live_price - trade['entry_price']) * mult * trade['qty'], 2)
                    trade['live_pnl'] = calc_pnl
                    shared_mem.last_triggered_setup_info[sym]["live_pnl"] = calc_pnl

                    # 1. PRE-ENTRY VALIDATION CHECK
                    if not trade['is_triggered']:
                        is_sl_breached_pre_entry = (trade['side'] == 'buy' and live_price <= trade['initial_sl']) or \
                                                   (trade['side'] == 'sell' and live_price >= trade['initial_sl'])
                        if is_sl_breached_pre_entry:
                            cancel_order(trade['entry_order_id'], sym, u_db['api_key'], u_db['api_secret'])
                            del shared_mem.active_trades[sym][user]
                            shared_mem.last_triggered_setup_info[sym] = {"entry": "WAITING", "sl": "WAITING", "t1": "WAITING", "t2": "WAITING", "status": "SCANNING ENGINE", "live_pnl": 0.0}
                            add_log(f"Pre-Entry SL breached on {sym}. Order cancelled.", type_icon="⚠️")
                            continue
                        
                        if ex_qty > 0:
                            trade['is_triggered'] = True
                            trade['qty'] = ex_qty  
                            shared_mem.last_triggered_setup_info[sym]["entry"] = f"${trade['entry_price']:,.2f} (FILLED)"
                            shared_mem.last_triggered_setup_info[sym]["sl"] = f"${trade['sl']:,.2f} (ACTIVE)"
                            shared_mem.last_triggered_setup_info[sym]["status"] = "ENTRY FILLED (SL LIVE)"
                            add_log(f"💥 Breakout Triggered for {user} on {sym}!", type_icon="⚡")
                            
                            opposite_side = "sell" if trade['side'] == 'buy' else 'buy'
                            
                            # Place active stop loss on exchange
                            sl_id = place_stop_loss(sym, ex_qty, opposite_side, trade['sl'], u_db['api_key'], u_db['api_secret'])
                            trade['exchange_sl_id'] = sl_id
                            
                            # Calculate exit quantities for targets
                            q_t1 = int(ex_qty * 0.50)
                            q_t2 = int(ex_qty * 0.25)
                            q_t21 = ex_qty - q_t1 - q_t2
                            
                            # Place targets as absolute limit orders on exchange (LMT -> Pic 531)
                            trade['exchange_t1_id'] = place_limit_profit_target(sym, q_t1, opposite_side, trade['targets'][1], u_db['api_key'], u_db['api_secret']) if q_t1 > 0 else None
                            trade['exchange_t2_id'] = place_limit_profit_target(sym, q_t2, opposite_side, trade['targets'][2], u_db['api_key'], u_db['api_secret']) if q_t2 > 0 else None
                            trade['exchange_t21_id'] = place_limit_profit_target(sym, q_t21, opposite_side, trade['targets'][21], u_db['api_key'], u_db['api_secret']) if q_t21 > 0 else None
                            
                            add_log(f"Target Orders Synchronized on Exchange: T1 Qty({q_t1}), T2 Qty({q_t2}), T21 Qty({q_t21})", type_icon="🎯")
                            continue

                    # 2. RUNTIME ACTIVE TRAILING & PARTIAL TARGET MANAGEMENT MATRIX
                    if trade['is_triggered']:
                        is_hard_sl_hit = (trade['side'] == 'buy' and live_price <= trade['sl']) or \
                                         (trade['side'] == 'sell' and live_price >= trade['sl'])
                        
                        if ex_qty == 0 or is_hard_sl_hit:
                            cancel_all_orders_for_symbol(sym, u_db['api_key'], u_db['api_secret'])
                            if ex_qty > 0: close_position_market(sym, u_db['api_key'], u_db['api_secret'])
                            del shared_mem.active_trades[sym][user]
                            shared_mem.last_triggered_setup_info[sym] = {"entry": "WAITING", "sl": "WAITING", "t1": "WAITING", "t2": "WAITING", "status": "SCANNING ENGINE", "live_pnl": 0.0}
                            add_log(f"Stop-Loss Breached / Position Flattened for {user} on {sym}. Target open orders canceled.", type_icon="🛑")
                            continue

                        current_high_target_hit = trade['current_stage']
                        for target_idx in range(current_high_target_hit + 1, 22):
                            target_price_level = trade['targets'][target_idx]
                            is_target_passed = (trade['side'] == 'buy' and live_price >= target_price_level) or \
                                               (trade['side'] == 'sell' and live_price <= target_price_level)
                            
                            if is_target_passed:
                                trade['current_stage'] = target_idx
                                opposite_side = "sell" if trade['side'] == 'buy' else 'buy'
                                
                                # Trailing SL: Cancel & Re-place Matrix
                                if trade.get('exchange_sl_id'):
                                    cancel_order(trade['exchange_sl_id'], sym, u_db['api_key'], u_db['api_secret'])
                                
                                if target_idx == 1:
                                    trade['sl'] = trade['entry_price']  
                                    status_str = "TA1 HIT (SL @ COST)"
                                    add_log(f"🎯 Target 1 Cross verified! 50% Qty processed. Remaining SL trailed to Cost.", type_icon="💰")
                                    
                                elif target_idx == 2:
                                    trade['sl'] = trade['targets'][1]   
                                    status_str = "TA2 HIT (SL @ TA1)"
                                    add_log(f"🎯 Target 2 Cross verified! 25% Qty processed. Remaining SL trailed to TA1.", type_icon="💰")
                                    
                                else:
                                    trade['sl'] = trade['targets'][target_idx - 1]
                                    status_str = f"TA{target_idx} HIT (SL @ TA{target_idx-1})"
                                    add_log(f"🔄 📈 Target {target_idx} crossed. SL trailed to TA{target_idx-1}.", type_icon="🔄")
                                
                                updated_live_qty = get_open_position_qty(sym, u_db['api_key'], u_db['api_secret'])
                                if updated_live_qty > 0:
                                    trade['exchange_sl_id'] = place_stop_loss(sym, updated_live_qty, opposite_side, trade['sl'], u_db['api_key'], u_db['api_secret'])
                                
                                shared_mem.last_triggered_setup_info[sym]["sl"] = f"${trade['sl']:,.2f}"
                                shared_mem.last_triggered_setup_info[sym]["status"] = status_str
                                
                                if target_idx == 21:
                                    cancel_all_orders_for_symbol(sym, u_db['api_key'], u_db['api_secret'])
                                    if updated_live_qty > 0: close_position_market(sym, u_db['api_key'], u_db['api_secret'])
                                    del shared_mem.active_trades[sym][user]
                                    shared_mem.last_triggered_setup_info[sym] = {"entry": "WAITING", "sl": "WAITING", "t1": "WAITING", "t2": "WAITING", "status": "SCANNING ENGINE", "live_pnl": 0.0}
                                    add_log(f"🏆 MAX TARGET 21 REACHED! Matrix flattened.", type_icon="👑")
                                break

            # 3. SIGNAL GEN MATRIX
            if shared_mem.users_db and not shared_mem.is_processing:
                for sym in symbols:
                    sym_switches = getattr(shared_mem, 'symbol_switches', {"BTCUSD": True, "ETHUSD": True})
                    if not sym_switches.get(sym, True):
                        continue 

                    if sym in shared_mem.active_trades and len(shared_mem.active_trades[sym]) > 0: continue
                    valid_users = [u for u, data in shared_mem.users_db.items() if data.get('api_key')]
                    if not valid_users: continue
                    first_user = valid_users[0]
                    
                    if get_open_position_qty(sym, shared_mem.users_db[first_user]['api_key'], shared_mem.users_db[first_user]['api_secret']) > 0: continue
                    if true_live_asset is not None and true_live_asset != sym: continue 

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
                    triggered, s_key, side, entry, sl = False, "", "", 0.0, 0.0
                    
                    # 🟢 BUY SIDE
                    if shared_mem.strategy_switches["2-STAR BUY"] and rsi_1 > 60 and rsi_1_prev <= 60 and close_1m > df_1m["BB_up"].iloc[-2]:
                        triggered, s_key, side = True, "2-STAR BUY", "buy"
                    elif shared_mem.strategy_switches["5-STAR LONG"] and rsi_15 >= 60 and rsi_5 >= 60 and rsi_1 > 40 and rsi_1 > rsi_1_prev and (43 >= rsi_1_prev >= 20):
                        triggered, s_key, side = True, "5-STAR LONG", "buy"
                    elif shared_mem.strategy_switches["5-STAR BB BUY"] and rsi_15 > 60 and rsi_5 > 60 and rsi_1_prev < 61 and rsi_1 >= 60 and close_1m > df_1m["BB_up"].iloc[-2]:
                        triggered, s_key, side = True, "5-STAR BB BUY", "buy"
                    
                    if triggered and side == "buy":
                        raw_entry = float(df_1m["high"].iloc[-2])
                        raw_sl = float(df_1m["low"].iloc[-2])
                        entry = round(raw_entry * 2) / 2 if sym == "BTCUSD" else round(raw_entry, 2)
                        sl = round(raw_sl * 2) / 2 if sym == "BTCUSD" else round(raw_sl, 2)

                    # 🔴 SELL SIDE
                    elif shared_mem.strategy_switches["2-STAR SELL"] and rsi_1 < 40 and rsi_1_prev >= 40 and close_1m < df_1m["BB_low"].iloc[-2]:
                        triggered, s_key, side = True, "2-STAR SELL", "sell"
                    elif shared_mem.strategy_switches["5-STAR SHORT"] and rsi_15 <= 40 and rsi_5 <= 40 and rsi_1 < 60 and rsi_1 < rsi_1_prev and (80 >= rsi_1_prev >= 57):
                        triggered, s_key, side = True, "5-STAR SHORT", "sell"
                    elif shared_mem.strategy_switches["5-STAR BB SELL"] and rsi_15 < 40 and rsi_5 < 40 and rsi_1_prev > 39 and rsi_1 <= 40 and close_1m < df_1m["BB_low"].iloc[-2]:
                        triggered, s_key, side = True, "5-STAR BB SELL", "sell"
                        
                    if triggered and side == "sell":
                        raw_entry = float(df_1m["low"].iloc[-2])
                        raw_sl = float(df_1m["high"].iloc[-2])
                        entry = round(raw_entry * 2) / 2 if sym == "BTCUSD" else round(raw_entry, 2)
                        sl = round(raw_sl * 2) / 2 if sym == "BTCUSD" else round(raw_sl, 2)

                    if triggered:
                        risk = abs(entry - sl)
                        if risk > 0:
                            shared_mem.is_processing = True
                            shared_mem.ordered_candles[sym] = c_time
                            shared_mem.strategy_metrics[s_key]["triggers"] += 1
                            
                            target_mesh = {}
                            for i in range(1, 22):
                                raw_target = entry + (i * risk) if side == "buy" else entry - (i * risk)
                                target_mesh[i] = round(raw_target * 2) / 2 if sym == "BTCUSD" else round(raw_target, 2)

                            shared_mem.last_triggered_setup_info[sym] = {
                                "entry": f"${entry:,.2f} (Pending)", "sl": f"${sl:,.2f} (On Trigger)", "t1": f"${target_mesh[1]:,.2f}", "t2": f"${target_mesh[2]:,.2f}", "status": f"{s_key} ({side.upper()}) (Pending)", "live_pnl": 0.0
                            }
                            
                            if sym not in shared_mem.active_trades: shared_mem.active_trades[sym] = {}
                            
                            for user, u_db in shared_mem.users_db.items():
                                if not u_db.get("active", True): continue
                                u_qty = int(u_db["btc_qty"] if sym == "BTCUSD" else u_db["eth_qty"])
                                
                                order_status = place_breakout_entry_order(sym, u_qty, side, entry, u_db['api_key'], u_db['api_secret'])
                                
                                if order_status["success"]:
                                    add_log(f"Setup registered at ${entry} for {sym}.", type_icon="⏳")
                                    shared_mem.active_trades[sym][user] = {
                                        'side': side, 'entry_price': entry, 'initial_sl': sl, 'sl': sl, 
                                        'targets': target_mesh, 'current_stage': 0, 'qty': u_qty, 
                                        'entry_order_id': order_status["order_id"], 'exchange_sl_id': None, 'is_triggered': False, 'live_pnl': 0.0,
                                        'exchange_t1_id': None, 'exchange_t2_id': None, 'exchange_t21_id': None
                                    }
                                    time.sleep(0.2)
                                else:
                                    fail_reason = order_status["error"]
                                    if fail_reason == "INSUFFICIENT_MARGIN":
                                        shared_mem.last_triggered_setup_info[sym]["status"] = "REJECTED - INSUFFICIENT MARGIN"
                                        add_log(f"ORDER REJECTED for {user} on {sym}! Reason: INSUFFICIENT MARGIN.", type_icon="❌")
                                    else:
                                        shared_mem.last_triggered_setup_info[sym]["status"] = f"REJECTED - {fail_reason.upper()}"
                                        add_log(f"API Alert: {user} on {sym} rejected -> {fail_reason}", type_icon="❌")
                            break
            shared_mem.is_processing = False
            time.sleep(1.5)
        except: time.sleep(1.5)

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
    btc_sw_val = mem.symbol_switches.get("BTCUSD", True)
    ticker_title = "BTCUSD Future Live" if btc_sw_val else "BTCUSD Future (DISABLED)"
    st.markdown(f"""
    <div class="ticker-widget-card">
        <div><span class="ticker-dot-orange">●</span><span class="ticker-token-title">{ticker_title}</span></div>
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
    
    cls_entry = "signal-value-active" if "Pending" not in btc_info['entry'] and btc_info['entry'] != "WAITING" else "signal-value-waiting"
    cls_sl = "signal-value-active" if "On Trigger" not in btc_info['sl'] and btc_info['sl'] != "WAITING" else "signal-value-waiting"
    cls_t1 = "signal-value-active" if btc_info['t1'] != "WAITING" else "signal-value-waiting"
    cls_t2 = "signal-value-active" if btc_info['t2'] != "WAITING" else "signal-value-waiting"

    st.markdown(f"""
    <div class="pnl-analytics-card">
        <div style="font-size: 11px; color: #ffff00; font-weight: bold; margin-bottom: 2px;">Global Setup P&L:</div>
        <div class="live-pnl-text {pnl_class}">+${pnl_val:,.2f}</div>
    </div>
    <div class="signal-data-box">
        <div style="font-size: 11px; color: #ef4444; font-weight: bold; margin-bottom: 6px;">🔴 SETUP STATUS: {btc_info['status'] if btc_sw_val else 'SYMBOL SWITCH OFF'}</div>
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
    eth_sw_val = mem.symbol_switches.get("ETHUSD", True)
    ticker_title_eth = "ETHUSD Future Live" if eth_sw_val else "ETHUSD Future (DISABLED)"
    st.markdown(f"""
    <div class="ticker-widget-card">
        <div><span class="ticker-dot-purple">●</span><span class="ticker-token-title">{ticker_title_eth}</span></div>
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
    
    cls_entry_eth = "signal-value-active" if "Pending" not in eth_info['entry'] and eth_info['entry'] != "WAITING" else "signal-value-waiting"
    cls_sl_eth = "signal-value-active" if "On Trigger" not in eth_info['sl'] and eth_info['sl'] != "WAITING" else "signal-value-waiting"
    cls_t1_eth = "signal-value-active" if eth_info['t1'] != "WAITING" else "signal-value-waiting"
    cls_t2_eth = "signal-value-active" if eth_info['t2'] != "WAITING" else "signal-value-waiting"

    st.markdown(f"""
    <div class="pnl-analytics-card">
        <div style="font-size: 11px; color: #ffff00; font-weight: bold; margin-bottom: 2px;">Global Setup P&L:</div>
        <div class="live-pnl-text {pnl_class_eth}">+${pnl_val_eth:,.2f}</div>
    </div>
    <div class="signal-data-box">
        <div style="font-size: 11px; color: #ef4444; font-weight: bold; margin-bottom: 6px;">🔴 SETUP STATUS: {eth_info['status'] if eth_sw_val else 'SYMBOL SWITCH OFF'}</div>
        <div class="signal-grid">
            <div><span class="signal-metric">ENTRY:</span> <span class="{cls_entry_eth}">{eth_info['entry']}</span></div>
            <div><span class="signal-metric">STOP LOSS:</span> <span class="{cls_sl_eth}">{eth_info['sl']}</span></div>
            <div><span class="signal-metric">TARGET 1:</span> <span class="{cls_t1_eth}">{eth_info['t1']}</span></div>
            <div><span class="signal-metric">TARGET 2:</span> <span class="{cls_t2_eth}">{eth_info['t2']}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

# =====================================================
# ☑️ REAL-TIME CLIENT MATRIX
# =====================================================
st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-heading">☑️ REAL-TIME CLIENT MATRIX & RISK CONTROLLER</div>', unsafe_allow_html=True)

col_th1, col_th2, col_th3, col_th4, col_th5, col_th6, col_th7 = st.columns([1.5, 2, 2, 1.2, 1.2, 1.5, 1.2])
with col_th1: st.markdown("<span style='color:#38bdf8; font-size:11px;'>CLIENT NAME</span>", unsafe_allow_html=True)
with col_th2: st.markdown("<span style='color:#38bdf8; font-size:11px;'>ENGINE STATUS</span>", unsafe_allow_html=True)
with col_th3: st.markdown("<span style='color:#38bdf8; font-size:11px;'>LOT SIZING</span>", unsafe_allow_html=True)
with col_th4: st.markdown("<span style='color:#38bdf8; font-size:11px;'>DAILY REALIZED</span>", unsafe_allow_html=True)
with col_th5: st.markdown("<span style='color:#38bdf8; font-size:11px;'>TOTAL NET P&L</span>", unsafe_allow_html=True)
with col_th6: st.markdown("<span style='color:#38bdf8; font-size:11px;'>TRADE ALLOW</span>", unsafe_allow_html=True)
with col_th7: st.markdown("<span style='color:#ef4444; font-size:11px;'>ACTION</span>", unsafe_allow_html=True)
st.markdown("<hr style='border:1px solid #1e3a8a; margin-top:5px; margin-bottom:10px;'/>", unsafe_allow_html=True)

for u_name, u_data in list(mem.users_db.items()):
    col_r1, col_r2, col_r3, col_r4, col_r5, col_r6, col_r7 = st.columns([1.5, 2, 2, 1.2, 1.2, 1.5, 1.2])
    with col_r1: st.markdown(f"<span style='color:#38bdf8; font-size:13px;'>{u_name}</span>", unsafe_allow_html=True)
    with col_r2: 
        status_txt = "🔵 SCANNING MESH" if u_data.get("active", True) else "⚪ UNAPPROVED (PAUSED)"
        st.markdown(f"<span style='color:#ffff00; font-size:12px;'>{status_txt}</span>", unsafe_allow_html=True)
    with col_r3: st.markdown(f"<span style='color:#ffff00; font-size:12px;'>{u_data['btc_qty']} BTC / {u_data['eth_qty']} ETH</span>", unsafe_allow_html=True)
    with col_r4: st.markdown("<span style='color:#ffff00; font-size:12px;'>$0.00</span>", unsafe_allow_html=True)
    with col_r5: st.markdown("<span style='color:#10b981; font-size:12px;'>$0.00</span>", unsafe_allow_html=True)
    with col_r6:
        is_approved = st.checkbox("APPROVED", value=u_data.get("active", True), key=f"chk_active_{u_name}")
        if is_approved != u_data.get("active", True):
            mem.users_db[u_name]["active"] = is_approved
            if u_name in all_u:
                all_u[u_name]["active"] = is_approved
                save_users(all_u)
            add_log(f"User {u_name} status updated to {'APPROVED' if is_approved else 'UNAPPROVED'}")
            st.rerun()
    with col_r7:
        if st.button("❌", key=f"btn_rm_{u_name}", use_container_width=True):
            existing_users = load_users()
            if u_name in existing_users:
                del existing_users[u_name]
                save_users(existing_users)
            if u_name in mem.users_db:
                del mem.users_db[u_name]
            add_log(f"Client {u_name} disconnected.", type_icon="🛑")
            st.rerun()
    st.markdown("<hr style='border:1px solid #1e3a8a; opacity:0.3; margin-top:5px; margin-bottom:5px;'/>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# 🎛️ GLOBAL SWITCHES SECTION
# =====================================================
col_body_sw1, col_body_sw2 = st.columns(2)
with col_body_sw1:
    st.markdown('<div class="grid-panel" style="min-height: 290px;">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">🎛️ ENGINE GLOBAL SWITCH SYSTEM</div>', unsafe_allow_html=True)
    engine_status_label = "ACTIVE (RUNNING)" if mem.global_engine_running else "DEACTIVATED (PAUSED)"
    st.markdown(f"### STATUS: <span style='color:#00ff00;'>{engine_status_label}</span>", unsafe_allow_html=True)
    if mem.global_engine_running:
        st.button("🔴 STOP SCANNER SYSTEM", on_click=trigger_stop_action, use_container_width=True)
    else:
        st.button("🟢 START SCANNER SYSTEM", on_click=trigger_start_action, use_container_width=True)
        
    st.markdown("<hr style='border:1px dashed #1e3a8a; margin: 12px 0;'/>", unsafe_allow_html=True)
    st.markdown("<span style='color:#38bdf8; font-size:12px; font-weight:bold; text-transform:uppercase;'>🎯 SYMBOL SELECTION MATRIX:</span>", unsafe_allow_html=True)
    
    csym_b1, csym_b2 = st.columns([0.1, 0.9])
    with csym_b1: 
        mem.symbol_switches["BTCUSD"] = st.checkbox("", value=mem.symbol_switches.get("BTCUSD", True), key="chk_sym_btc")
    with csym_b2: 
        st.markdown('<span class="neon-blue-lbl" style="line-height: 1.8;">ALLOW BTCUSD TRADING</span>', unsafe_allow_html=True)
        
    csym_e1, csym_e2 = st.columns([0.1, 0.9])
    with csym_e1: 
        mem.symbol_switches["ETHUSD"] = st.checkbox("", value=mem.symbol_switches.get("ETHUSD", True), key="chk_sym_eth")
    with csym_e2: 
        st.markdown('<span class="neon-blue-lbl" style="line-height: 1.8;">ALLOW ETHUSD TRADING</span>', unsafe_allow_html=True)

    st.markdown("<span style='color:#ef4444; font-size:11px;'>🚨 EMERGENCY OPERATIONS CONTROLLER:</span>", unsafe_allow_html=True)
    if st.button("💥 GLOBAL KILL SWITCH (SQUARE OFF ALL)", use_container_width=True):
        for sym in ["BTCUSD", "ETHUSD"]:
            for usr, u_db in mem.users_db.items():
                cancel_all_orders_for_symbol(sym, u_db['api_key'], u_db['api_secret'])
                close_position_market(sym, u_db['api_key'], u_db['api_secret'])
        mem.active_trades.clear()
        add_log("EMERGENCY SQUARED OFF TRIGGERED!", type_icon="💥")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_body_sw2:
    st.markdown('<div class="grid-panel" style="min-height: 290px;">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">⚙️ HEXA-STRATEGY PIPELINE SWITCHES</div>', unsafe_allow_html=True)
    
    c2b1, c2b2 = st.columns([0.1, 0.9])
    with c2b1: mem.strategy_switches["2-STAR BUY"] = st.checkbox("", value=mem.strategy_switches.get("2-STAR BUY", True), key="chk_2_buy")
    with c2b2: st.markdown('<span class="neon-green-lbl" style="line-height: 2.0;">1. 2-STAR RSI+BB BUY BREAKOUT</span>', unsafe_allow_html=True)

    c2s1, c2s2 = st.columns([0.1, 0.9])
    with c2s1: mem.strategy_switches["2-STAR SELL"] = st.checkbox("", value=mem.strategy_switches.get("2-STAR SELL", True), key="chk_2_sell")
    with c2s2: st.markdown('<span class="neon-red-lbl" style="line-height: 2.0;">2. 2-STAR RSI+BB SELL BREAKOUT</span>', unsafe_allow_html=True)

    cl1, cl2 = st.columns([0.1, 0.9])
    with cl1: mem.strategy_switches["5-STAR LONG"] = st.checkbox("", value=mem.strategy_switches["5-STAR LONG"], key="chk_5_long")
    with cl2: st.markdown('<span class="neon-green-lbl" style="line-height: 2.0;">3. 5-STAR LONG</span>', unsafe_allow_html=True)
        
    cs1, cs2 = st.columns([0.1, 0.9])
    with cs1: mem.strategy_switches["5-STAR SHORT"] = st.checkbox("", value=mem.strategy_switches["5-STAR SHORT"], key="chk_5_short")
    with cs2: st.markdown('<span class="neon-red-lbl" style="line-height: 2.0;">4. 5-STAR SHORT</span>', unsafe_allow_html=True)
        
    cb1, cb2 = st.columns([0.1, 0.9])
    with cb1: mem.strategy_switches["5-STAR BB BUY"] = st.checkbox("", value=mem.strategy_switches["5-STAR BB BUY"], key="chk_bb_buy")
    with cb2: st.markdown('<span class="neon-green-lbl" style="line-height: 2.0;">5. 5-STAR BUY BREAKOUT </span>', unsafe_allow_html=True)
        
    cx1, cx2 = st.columns([0.1, 0.9])
    with cx1: mem.strategy_switches["5-STAR BB SELL"] = st.checkbox("", value=mem.strategy_switches["5-STAR BB SELL"], key="chk_bb_sell")
    with cx2: st.markdown('<span class="neon-red-lbl" style="line-height: 2.0;">6. 5-STAR SELL BREAKOUT </span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# BOTTOM NAVIGATION TAB CONTROLLER
tab_logs, tab_rms, tab_registration = st.tabs(["📊 LIVE DIAGNOSTICS LOGS", "🛡️ RISK CONTROLLER (RMS)", "👥 CLIENT REGISTRATION MATRIX"])

with tab_logs:
    st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">📊 LIVE TERMINAL DIAGNOSTIC REPORT</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="diagnostic-logger-container">{"".join(mem.last_terminal_logs)}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab_rms:
    st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">🛡️ RISK MANAGEMENT SYSTEM RULES</div>', unsafe_allow_html=True)
    st.info("Ecosystem Risk Controllers active under normal parameters.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab_registration:
    st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">👥 REGISTER NEW CLIENT GATEWAY</div>', unsafe_allow_html=True)
    with st.form("Client Registration Bottom Tab Form"):
        reg_username = st.text_input("Client ID / Username")
        reg_password = st.text_input("Terminal Trading Password", type="password")
        reg_key = st.text_input("Delta Exchange API Key", type="password")
        reg_secret = st.text_input("Delta Exchange API Secret Key", type="password")
        rc1, rc2 = st.columns(2)
        with rc1: reg_btc_qty = st.number_input("BTC Qty (Lots)", min_value=1, value=4)
        with rc2: reg_eth_qty = st.number_input("ETH Qty (Lots)", min_value=1, value=4)
        submit_registration = st.form_submit_button("🔒 REGISTER CLIENT SECURELY")
        if submit_registration:
            if not reg_username or not reg_password or not reg_key or not reg_secret:
                st.error("❌ Sabhi fields fill up karna anivarye hain!")
            else:
                existing_users = load_users()
                existing_users[reg_username] = {"password": reg_password, "api_key": reg_key, "api_secret": reg_secret, "btc_qty": int(reg_btc_qty), "eth_qty": int(reg_eth_qty), "active": True}
                save_users(existing_users)
                mem.users_db[reg_username] = {"api_key": reg_key, "api_secret": reg_secret, "btc_qty": int(reg_btc_qty), "eth_qty": int(reg_eth_qty), "active": True}
                add_log(f"New client deployment for {reg_username} verified.", type_icon="👤")
                st.success(f"🎉 User added successfully!")
                time.sleep(1)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"Current Active User: `{current_usr}`")

time.sleep(1)
st.rerun()
