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
import os

# ✅ **SYSTEM STABILITY FOR TERMUX / IPV4 OPTIMIZATION**
import urllib3.util.connection as urllib3_cn
urllib3_cn.HAS_IPV6 = False

# **Global Network Session for Performance Optimization (Fast API)**
session = requests.Session()

# =====================================================
# 📲 **TELEGRAM ALERT CONFIGURATION**
# =====================================================
TELEGRAM_BOT_TOKEN = "8584808786:AAGsgDbzAg618mEMW4YFM8RBJOvBiBxKHr8"  
TELEGRAM_CHAT_ID = "8909374225"      

def send_telegram_alert(msg, user):
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"🤖 **Quantum Terminal Alert**\n👤 User: {user}\n\n{msg}",
        "parse_mode": "Markdown"
    }
    
    try:
        threading.Thread(target=lambda: session.post(url, json=payload, timeout=5)).start()
    except Exception:
        pass

# =====================================================
# 🔐 **LOCAL AUTHENTICATION & USER DATABASE SYSTEM**
# =====================================================
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        init_db = {
            "yunay": {
                "password": "1122", "api_key": "", "api_secret": "", "btc_qty": 4, "eth_qty": 4,
                "risk_mode": False, "risk_value": 1000.0, "active": True, "is_running": True,
                "symbol_switches": {"BTCUSD": True, "ETHUSD": True},
                "strategy_switches": {
                    "2-STAR BUY": True, "2-STAR SELL": True, "5-STAR LONG": True, 
                    "5-STAR SHORT": True, "5-STAR BUY": True, "5-STAR SELL": True
                }
            }
        }
        save_users(init_db)
        return init_db
    with open(USERS_FILE, 'r') as f:
        try:
            db = json.load(f)
            for u, data in db.items():
                if "5-STAR BB BUY" in data.get("strategy_switches", {}):
                    data["strategy_switches"]["5-STAR BUY"] = data["strategy_switches"].pop("5-STAR BB BUY")
                if "5-STAR BB SELL" in data.get("strategy_switches", {}):
                    data["strategy_switches"]["5-STAR SELL"] = data["strategy_switches"].pop("5-STAR BB SELL")
            return db
        except json.JSONDecodeError:
            return {}

def save_users(db):
    with open(USERS_FILE, 'w') as f:
        json.dump(db, f, indent=4)

def auth_page():
    st.markdown("<h2 style='text-align: center; color: #38bdf8;'>🔐 QUANTUM TERMINAL SECURE ACCESS</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 **SIGN IN**", "📝 **SIGN UP (NEW CLIENT)**"])
    
    with tab1:
        with st.form("login_form"):
            u_login = st.text_input("Username").strip()
            p_login = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("LOGIN TO TERMINAL")
            
            if submit_login:
                db = load_users()
                if u_login in db and db[u_login]["password"] == p_login:
                    if not db[u_login].get("active", False) and u_login.lower() != "yunay":
                        st.error("⚠️ **Account Pending Approval!** Owner (Yunay) ko approve karne de.")
                    else:
                        st.session_state["logged_in"] = True
                        st.session_state["current_user"] = u_login
                        st.query_params["user"] = u_login 
                        st.success(f"Welcome back, {u_login}!")
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.error("❌ Invalid Username or Password")
                    
    with tab2:
        with st.form("signup_form"):
            u_reg = st.text_input("Choose Username").strip()
            p_reg = st.text_input("Choose Password", type="password")
            submit_reg = st.form_submit_button("REGISTER ACCOUNT")
            
            if submit_reg:
                if not u_reg or not p_reg:
                    st.error("Username and Password are required!")
                else:
                    db = load_users()
                    if u_reg in db:
                        st.error("❌ Username already exists. Choose another one.")
                    else:
                        db[u_reg] = {
                            "password": p_reg, "api_key": "", "api_secret": "", "btc_qty": 4, "eth_qty": 4,
                            "risk_mode": False, "risk_value": 1000.0, "active": False, "is_running": False,
                            "symbol_switches": {"BTCUSD": True, "ETHUSD": True},
                            "strategy_switches": {
                                "2-STAR BUY": True, "2-STAR SELL": True, "5-STAR LONG": True, 
                                "5-STAR SHORT": True, "5-STAR BUY": True, "5-STAR SELL": True
                            }
                        }
                        save_users(db)
                        send_telegram_alert(f"🆕 **New Registration Alert!**\nUser '{u_reg}' ne terminal par signup kiya hai. Waiting for approval.", "ADMIN")
                        st.success("✅ **Registration Successful!** Please wait for Admin (Yunay) to approve your account before logging in.")

# **Streamlit Configuration**
st.set_page_config(page_title="Quantum Multi-User Terminal", layout="wide", initial_sidebar_state="collapsed")

# ✅ CHECK FOR URL PARAMETER TO KEEP USER LOGGED IN ON PAGE RELOAD
if "user" in st.query_params:
    st.session_state["logged_in"] = True
    st.session_state["current_user"] = st.query_params["user"]

# =====================================================
# **GLOBAL ENGINE MEMORY MESH (Thread-Safe)**
# =====================================================
class GlobalEngineMemory:
    def __init__(self):
        self.lock = threading.Lock()
        self.users_db = {}
        self.active_trades = {}
        self.ordered_candles = {}
        self.is_processing = False
        
        self.last_triggered_setup_info = {
            "BTCUSD": {"entry": "-", "sl": "-", "t1": "-", "t2": "-", "status": "🔵 **SCANNING FOR SETUPS...**", "live_pnl": 0.0},
            "ETHUSD": {"entry": "-", "sl": "-", "t1": "-", "t2": "-", "status": "🔵 **SCANNING FOR SETUPS...**", "live_pnl": 0.0}
        }
        
        self.strategy_metrics = {
            "2-STAR BUY": {"triggers": 0}, "2-STAR SELL": {"triggers": 0},
            "5-STAR LONG": {"triggers": 0}, "5-STAR SHORT": {"triggers": 0},
            "5-STAR BUY": {"triggers": 0}, "5-STAR SELL": {"triggers": 0}
        }
        
        self.last_terminal_logs = [
            {"timestamp": "", "user": "ALL", "msg": "🚀 **Advance Controller Engine Activated with Smart Wick Detection Matrix.**", "color": "#38bdf8"}
        ]
        
        self.ticker_feeds = {
            "BTCUSD": {"ltp": 0.0, "rsi_1m": 0.0, "rsi_5m": 0.0, "rsi_15m": 0.0}, 
            "ETHUSD": {"ltp": 0.0, "rsi_1m": 0.0, "rsi_5m": 0.0, "rsi_15m": 0.0}
        }
        
        self.cached_dfs = {"BTCUSD": {"15m": None, "5m": None}, "ETHUSD": {"15m": None, "5m": None}}

if "mem_instance" not in st.session_state:
    if not hasattr(st, "_global_algo_memory"):
        st._global_algo_memory = GlobalEngineMemory()
    st.session_state["mem_instance"] = st._global_algo_memory

mem = st.session_state["mem_instance"]

# --- 🔐 **RELOAD PERSISTENCE ANCHOR** ---
if not st.session_state.get("logged_in", False):
    auth_page()
    st.stop()

current_usr = st.session_state.get("current_user", "")
is_owner = str(current_usr).strip().lower() == "yunay"

all_u = load_users()
with mem.lock:
    for u_name, u_data in all_u.items():
        mem.users_db[u_name] = u_data

# =====================================================
# **MASTER MULTI-COLOR NEON GLOW CUSTOM CSS**
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
    try: 
        return session.get("https://api.ipify.org", timeout=5).text
    except Exception: 
        return "152.58.109.90"

SERVER_IP = get_server_ip()

def add_log(msg, target_user="ALL", type_icon="🚀", color="#ffff00"):
    ist_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)
    timestamp = ist_time.strftime("%H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "user": target_user,
        "msg": f"{type_icon} {msg}",
        "color": color
    }
    with mem.lock:  
        mem.last_terminal_logs.insert(0, log_entry)
        if len(mem.last_terminal_logs) > 50: 
            mem.last_terminal_logs.pop()
            
    send_telegram_alert(f"{type_icon} {msg}", target_user)

# =====================================================
# **DELTA INDIA API CONNECTORS (WITH SIGNATURE FIX)**
# =====================================================
def send_signed_request(method, path, api_key, api_secret, payload=None):
    if not api_key or not api_secret: return {"success": False, "error": "Keys Missing"}
    timestamp = str(int(time.time()))
    
    body_string = json.dumps(payload, separators=(',', ':')) if (payload and method in ["POST", "PUT", "DELETE"]) else ""
    
    signature_payload = method + timestamp + path + body_string
    signature = hmac.new(api_secret.encode("utf-8"), signature_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    headers = {"api-key": api_key, "timestamp": timestamp, "signature": signature, "Content-Type": "application/json"}
    try:
        if method == "POST": r = session.post(BASE_URL + path, headers=headers, data=body_string, timeout=12)
        elif method == "DELETE": r = session.delete(BASE_URL + path, headers=headers, data=body_string, timeout=12)
        else: r = session.get(BASE_URL + path, headers=headers, params=payload, timeout=12)
        return r.json()
    except Exception: 
        return {"success": False, "error": "Network Timeout"}

def place_breakout_entry_order(symbol, size, side, trigger_price, api_key, api_secret):
    if size <= 0: return {"success": False, "error": "Size cannot be zero"}
    final_price = str(round(float(trigger_price) * 2) / 2) if "BTCUSD" in symbol else str(round(float(trigger_price), 2))
    payload = {
        "product_symbol": symbol, "size": int(size), "side": side.lower(),
        "order_type": "market_order", "stop_order_type": "stop_loss_order",
        "stop_price": final_price, "reduce_only": False
    }
    res = send_signed_request("POST", "/v2/orders", api_key, api_secret, payload)
    
    if res and res.get("success") is True: 
        return {"success": True, "order_id": res["result"].get("id")}
    
    return {"success": False, "error": f"RAW ERROR: {res}"}

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
    except Exception: 
        pass

def place_stop_loss(symbol, size, side, sl_price, api_key, api_secret):
    if size <= 0: return None
    final_sl = str(round(float(sl_price) * 2) / 2) if "BTCUSD" in symbol else str(round(float(sl_price), 2))
    payload = {
        "product_symbol": symbol, "size": int(size), "side": side.lower(),
        "order_type": "market_order", "stop_order_type": "stop_loss_order",   
        "stop_price": final_sl, "reduce_only": True
    }
    res = send_signed_request("POST", "/v2/orders", api_key, api_secret, payload)
    if res and res.get("success") is True: 
        return res["result"].get("id")
    return None

def place_limit_profit_target(symbol, size, side, price, api_key, api_secret):
    if size <= 0: return None
    final_price = str(round(float(price) * 2) / 2) if "BTCUSD" in symbol else str(round(float(price), 2))
    payload = {
        "product_symbol": symbol, "size": int(size), "side": side.lower(),
        "order_type": "limit_order", "limit_price": final_price, "reduce_only": True
    }
    res = send_signed_request("POST", "/v2/orders", api_key, api_secret, payload)
    if res and res.get("success") is True: 
        return res["result"].get("id")
    return None

def get_open_position_qty(symbol, api_key, api_secret):
    try:
        res = send_signed_request("GET", "/v2/positions/margined", api_key, api_secret)
        if res and "result" in res:
            for pos in res["result"]:
                if pos.get("product_symbol") == symbol: return abs(int(pos.get("size", 0)))
        return 0
    except Exception: 
        return 0

def rsi_calc(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    return 100 - (100 / (1 + (avg_gain / (avg_loss + 1e-10))))

def fetch_candles_df(symbol, timeframe, limit=30):
    try:
        end_t = int(time.time())
        multiplier_seconds = 60 if timeframe == "1m" else (300 if timeframe == "5m" else 900)
        r = session.get(f"{BASE_URL}/v2/history/candles", params={"symbol": symbol, "resolution": timeframe, "start": end_t - (limit * multiplier_seconds), "end": end_t}, timeout=5).json()
        if "result" in r and r["result"]:
            df = pd.DataFrame(r["result"]).iloc[::-1].reset_index(drop=True)
            for col in ["close", "high", "low"]: df[col] = pd.to_numeric(df[col])
            return df
        return None
    except Exception: 
        return None

# =====================================================
# **CORE PIPELINE TRADE ENGINE AUTOMATION (SMART WICK DETECTION)**
# =====================================================
def core_execution_engine(shared_mem):
    loop_counter = 0  
    while True:
        try:
            loop_counter += 1
            symbols = ["BTCUSD", "ETHUSD"]
            
            # 1. Update Live Prices
            for sym in symbols:
                try:
                    r = session.get(f"{BASE_URL}/v2/tickers/{sym}", timeout=4).json()
                    if r and "result" in r: 
                        with shared_mem.lock:
                            shared_mem.ticker_feeds[sym]["ltp"] = round(float(r["result"].get("mark_price", 0)), 2)
                except Exception: 
                    pass

            # 2. Check and Manage Live Trades (Per User)
            for sym in symbols:
                with shared_mem.lock:
                    live_price = shared_mem.ticker_feeds[sym]["ltp"]
                    has_trades = sym in shared_mem.active_trades
                
                if not live_price or not has_trades: continue
                
                total_pnl = 0.0

                with shared_mem.lock:
                    user_keys = list(shared_mem.active_trades[sym].keys())

                for user in user_keys:
                    with shared_mem.lock:
                        u_db = shared_mem.users_db.get(user)
                    
                    if not u_db or not u_db.get('api_key'): continue
                    
                    with shared_mem.lock:
                        trades_list = shared_mem.active_trades[sym][user]
                    
                    # Fetching Live Quantity from Exchange to catch fast Wick Hits
                    ex_qty = get_open_position_qty(sym, u_db['api_key'], u_db['api_secret'])

                    for trade in list(trades_list):
                        mult = 1 if trade['side'] == 'buy' else -1
                        calc_pnl = round((live_price - trade['entry_price']) * mult * trade['qty'], 2)
                        trade['live_pnl'] = calc_pnl
                        total_pnl += calc_pnl

                        # **PRE-ENTRY CHECK**
                        if not trade['is_triggered']:
                            is_sl_breached_pre_entry = (trade['side'] == 'buy' and live_price <= trade['initial_sl']) or \
                                                       (trade['side'] == 'sell' and live_price >= trade['initial_sl'])
                            
                            if is_sl_breached_pre_entry:
                                cancel_order(trade['entry_order_id'], sym, u_db['api_key'], u_db['api_secret'])
                                with shared_mem.lock:
                                    if trade in trades_list: trades_list.remove(trade)
                                add_log(f"Pre-Entry SL breached on {sym}. Order cancelled.", target_user=user, type_icon="⚠️")
                                continue
                            
                            # Entry Triggered Check
                            if ex_qty > 0:
                                trade['is_triggered'] = True
                                with shared_mem.lock:
                                    shared_mem.last_triggered_setup_info[sym]["entry"] = f"${trade['entry_price']:,.2f} (FILLED)"
                                    shared_mem.last_triggered_setup_info[sym]["sl"] = f"${trade['sl']:,.2f} (ACTIVE)"
                                    shared_mem.last_triggered_setup_info[sym]["status"] = f"🟢 **{trade['strategy']} LIVE (SL ACTIVE)**"
                                add_log(f"**Breakout Triggered on {sym} via {trade['strategy']}!**", target_user=user, type_icon="⚡")
                                
                                opposite_side = "sell" if trade['side'] == 'buy' else 'buy'
                                trade['exchange_sl_id'] = place_stop_loss(sym, trade['qty'], opposite_side, trade['sl'], u_db['api_key'], u_db['api_secret'])
                                add_log(f"**Initial Stop-Loss Plotted on {sym} @ ${trade['sl']}**", target_user=user, type_icon="🛑")
                                
                                q_t1 = int(trade['qty'] * 0.50)
                                q_t2 = int(trade['qty'] * 0.25)
                                q_t21 = trade['qty'] - q_t1 - q_t2
                                
                                trade['exchange_t1_id'] = place_limit_profit_target(sym, q_t1, opposite_side, trade['targets'][1], u_db['api_key'], u_db['api_secret']) if q_t1 > 0 else None
                                trade['exchange_t2_id'] = place_limit_profit_target(sym, q_t2, opposite_side, trade['targets'][2], u_db['api_key'], u_db['api_secret']) if q_t2 > 0 else None
                                
                                add_log(f"**Targets Plotted on {sym}** | T1: ${trade['targets'][1]} (50%) | T2: ${trade['targets'][2]} (25%)", target_user=user, type_icon="🎯")
                                
                                trade['exchange_t21_id'] = place_limit_profit_target(sym, q_t21, opposite_side, trade['targets'][21], u_db['api_key'], u_db['api_secret']) if q_t21 > 0 else None
                                continue

                        # **RUNTIME LIVE TRACKING & TRAILING MATRIX (SMART WICK FIX)**
                        if trade['is_triggered']:
                            is_hard_sl_hit = (trade['side'] == 'buy' and live_price <= trade['sl']) or \
                                             (trade['side'] == 'sell' and live_price >= trade['sl'])
                            
                            if ex_qty == 0 or is_hard_sl_hit:
                                cancel_all_orders_for_symbol(sym, u_db['api_key'], u_db['api_secret'])
                                if ex_qty > 0: close_position_market(sym, u_db['api_key'], u_db['api_secret'])
                                with shared_mem.lock:
                                    if trade in trades_list: trades_list.remove(trade)
                                add_log(f"**Stop-Loss Breached / Position Flattened on {sym}.**", target_user=user, type_icon="🛑", color="#ef4444")
                                continue

                            current_high_target_hit = trade['current_stage']
                            for target_idx in range(current_high_target_hit + 1, 22):
                                target_price_level = trade['targets'][target_idx]
                                
                                # Condition 1: Direct Price Match
                                is_target_passed = (trade['side'] == 'buy' and live_price >= target_price_level) or \
                                                   (trade['side'] == 'sell' and live_price <= target_price_level)
                                
                                # ✅ Condition 2: Quantity Drop Match (GHOST WICK DETECTION)
                                q_t1 = int(trade['qty'] * 0.50)
                                q_t2 = int(trade['qty'] * 0.25)
                                exp_qty_after_t1 = trade['qty'] - q_t1
                                exp_qty_after_t2 = trade['qty'] - q_t1 - q_t2
                                
                                is_qty_dropped = False
                                if target_idx == 1 and 0 < ex_qty <= exp_qty_after_t1 and trade['qty'] > 1:
                                    is_qty_dropped = True
                                elif target_idx == 2 and 0 < ex_qty <= exp_qty_after_t2 and trade['qty'] > 1:
                                    is_qty_dropped = True
                                
                                # IF EITHER CONDITION MEETS -> EXECUTE TRAIL
                                if is_target_passed or is_qty_dropped:
                                    trade['current_stage'] = target_idx
                                    opposite_side = "sell" if trade['side'] == 'buy' else 'buy'
                                    
                                    # 1. Cancel purana SL instantly
                                    if trade.get('exchange_sl_id'):
                                        cancel_order(trade['exchange_sl_id'], sym, u_db['api_key'], u_db['api_secret'])
                                    
                                    # 2. Assign New SL & Update Remaining QTY
                                    if target_idx == 1:
                                        trade['sl'] = trade['entry_price']  
                                        status_str = f"🎯 **{trade['strategy']} TA1 HIT (SL @ COST)**"
                                        updated_live_qty = ex_qty if is_qty_dropped else exp_qty_after_t1
                                        add_log(f"**Target 1 HIT (50% EXIT) on {sym}! SL Trailed to Cost @ ${trade['sl']}**", target_user=user, type_icon="💰", color="#10b981")
                                    elif target_idx == 2:
                                        trade['sl'] = trade['targets'][1]   
                                        status_str = f"🎯 **{trade['strategy']} TA2 HIT (SL @ TA1)**"
                                        updated_live_qty = ex_qty if is_qty_dropped else exp_qty_after_t2
                                        add_log(f"**Target 2 HIT (25% EXIT) on {sym}! SL Trailed to TA1 @ ${trade['sl']}**", target_user=user, type_icon="💰", color="#10b981")
                                    else:
                                        trade['sl'] = trade['targets'][target_idx - 1]
                                        status_str = f"🔄 **{trade['strategy']} TA{target_idx} HIT (SL TRAILED)**"
                                        updated_live_qty = ex_qty if is_qty_dropped else exp_qty_after_t2
                                        add_log(f"**Target {target_idx} HIT on {sym}! SL Trailed @ ${trade['sl']}**", target_user=user, type_icon="🔄")
                                    
                                    # 3. Place Naya SL instantly with live known qty
                                    if updated_live_qty > 0:
                                        trade['exchange_sl_id'] = place_stop_loss(sym, updated_live_qty, opposite_side, trade['sl'], u_db['api_key'], u_db['api_secret'])
                                    
                                    with shared_mem.lock:
                                        shared_mem.last_triggered_setup_info[sym]["sl"] = f"${trade['sl']:,.2f} (TRAILED)"
                                        shared_mem.last_triggered_setup_info[sym]["status"] = status_str
                                    
                                    if target_idx == 21:
                                        cancel_all_orders_for_symbol(sym, u_db['api_key'], u_db['api_secret'])
                                        if updated_live_qty > 0: close_position_market(sym, u_db['api_key'], u_db['api_secret'])
                                        with shared_mem.lock:
                                            if trade in trades_list: trades_list.remove(trade)
                                        add_log(f"**MAX TARGET 21 REACHED! Position flattened.**", target_user=user, type_icon="👑", color="#10b981")
                                    break
                
                with shared_mem.lock:
                    shared_mem.last_triggered_setup_info[sym]["live_pnl"] = total_pnl

            # =====================================================
            # 🚀 **SIGNAL GEN MATRIX**
            # =====================================================
            with shared_mem.lock:
                has_users = len(shared_mem.users_db) > 0
                processing_state = shared_mem.is_processing
            
            if has_users and not processing_state:
                for sym in symbols:
                    with shared_mem.lock:
                        valid_users = [u for u, data in shared_mem.users_db.items() if data.get('api_key') and data.get('active', True) and data.get('is_running', False)]
                    
                    if not valid_users: continue
                    
                    with shared_mem.lock:
                        cached_15m = shared_mem.cached_dfs[sym]["15m"]
                        cached_5m = shared_mem.cached_dfs[sym]["5m"]
                        
                    if loop_counter % 4 == 1 or cached_15m is None or cached_5m is None:
                        df_15m = fetch_candles_df(sym, "15m", limit=100)
                        df_5m = fetch_candles_df(sym, "5m", limit=100)
                        with shared_mem.lock:
                            shared_mem.cached_dfs[sym]["15m"] = df_15m
                            shared_mem.cached_dfs[sym]["5m"] = df_5m
                    else:
                        df_15m = cached_15m
                        df_5m = cached_5m

                    df_1m = fetch_candles_df(sym, "1m", limit=100)
                    if df_15m is None or df_5m is None or df_1m is None: continue
                    
                    df_15m["RSI"] = rsi_calc(df_15m["close"])
                    df_5m["RSI"] = rsi_calc(df_5m["close"])
                    df_1m["RSI"] = rsi_calc(df_1m["close"])
                    
                    ma = df_1m["close"].rolling(20).mean()
                    stdev = df_1m["close"].rolling(20).std()
                    df_1m["BB_up"], df_1m["BB_low"] = ma + (2 * stdev), ma - (2 * stdev)
                    
                    with shared_mem.lock:
                        shared_mem.ticker_feeds[sym]["rsi_1m"] = round(df_1m["RSI"].iloc[-1], 2)
                        shared_mem.ticker_feeds[sym]["rsi_5m"] = round(df_5m["RSI"].iloc[-1], 2)
                        shared_mem.ticker_feeds[sym]["rsi_15m"] = round(df_15m["RSI"].iloc[-1], 2)
                    
                    rsi_15 = df_15m["RSI"].iloc[-2]
                    rsi_5 = df_5m["RSI"].iloc[-2]
                    rsi_1 = df_1m["RSI"].iloc[-2]
                    rsi_1_prev = df_1m["RSI"].iloc[-3]
                    
                    close_1m = df_1m["close"].iloc[-2]
                    high_1m = df_1m["high"].iloc[-2]
                    low_1m = df_1m["low"].iloc[-2]
                    bb_up = df_1m["BB_up"].iloc[-2]
                    bb_low = df_1m["BB_low"].iloc[-2]
                    c_time = df_1m["time"].iloc[-2]
                    
                    lowest_15 = df_1m["low"].rolling(15).min().iloc[-2]
                    highest_15 = df_1m["high"].rolling(15).max().iloc[-2]
                    
                    with shared_mem.lock:
                        already_ordered = sym in shared_mem.ordered_candles and shared_mem.ordered_candles[sym] == c_time
                    if already_ordered: continue
                    
                    s_key = ""
                    side = ""
                    raw_entry = 0.0
                    raw_sl = 0.0
                    
                    if rsi_15 >= 60 and rsi_5 >= 60 and rsi_1 > 40 and rsi_1 > rsi_1_prev and (20 <= rsi_1_prev <= 43):
                        s_key, side = "5-STAR LONG", "buy"
                        raw_entry = float(high_1m)
                        raw_sl = float(lowest_15) 
                        
                    elif rsi_15 <= 40 and rsi_5 <= 40 and rsi_1 < 60 and rsi_1 < rsi_1_prev and (57 <= rsi_1_prev <= 80):
                        s_key, side = "5-STAR SHORT", "sell"
                        raw_entry = float(low_1m)
                        raw_sl = float(highest_15) 
                        
                    elif rsi_15 > 60 and rsi_5 > 60 and rsi_1_prev <= 60 and rsi_1 > 60 and close_1m > bb_up:
                        s_key, side = "5-STAR BUY", "buy"
                        raw_entry = float(high_1m)
                        raw_sl = float(low_1m)
                        
                    elif rsi_15 < 40 and rsi_5 < 40 and rsi_1_prev >= 40 and rsi_1 < 40 and close_1m < bb_low:
                        s_key, side = "5-STAR SELL", "sell"
                        raw_entry = float(low_1m)
                        raw_sl = float(high_1m)
                        
                    elif rsi_1_prev <= 60 and rsi_1 > 60 and close_1m > bb_up:
                        s_key, side = "2-STAR BUY", "buy"
                        raw_entry = float(high_1m)
                        raw_sl = float(low_1m)
                        
                    elif rsi_1_prev >= 40 and rsi_1 < 40 and close_1m < bb_low:
                        s_key, side = "2-STAR SELL", "sell"
                        raw_entry = float(low_1m)
                        raw_sl = float(high_1m)
                        
                    if s_key != "":
                        entry = round(raw_entry * 2) / 2 if sym == "BTCUSD" else round(raw_entry, 2)
                        sl = round(raw_sl * 2) / 2 if sym == "BTCUSD" else round(raw_sl, 2)
                        risk = abs(entry - sl)
                        
                        if risk > 0:
                            with shared_mem.lock:
                                shared_mem.is_processing = True
                                shared_mem.ordered_candles[sym] = c_time
                                shared_mem.strategy_metrics.setdefault(s_key, {"triggers": 0})["triggers"] += 1
                                current_users_snapshot = shared_mem.users_db.copy()
                            
                            target_mesh = {}
                            for i in range(1, 22):
                                raw_target = entry + (i * risk) if side == "buy" else entry - (i * risk)
                                target_mesh[i] = round(raw_target * 2) / 2 if sym == "BTCUSD" else round(raw_target, 2)

                            any_order_placed = False

                            for user, u_db in current_users_snapshot.items():
                                if not u_db.get("active", True): continue
                                if not u_db.get("is_running", False): continue
                                
                                user_sym_sw = u_db.get("symbol_switches", {"BTCUSD": True, "ETHUSD": True})
                                user_strat_sw = u_db.get("strategy_switches", {})
                                
                                if not user_sym_sw.get(sym, True): continue 
                                if not user_strat_sw.get(s_key, True): continue 

                                with shared_mem.lock:
                                    user_active_trades = shared_mem.active_trades.get(sym, {}).get(user, [])
                                    user_running_strats = [t.get('strategy') for t in user_active_trades]
                                    is_user_active = len(user_running_strats) > 0

                                user_can_trade = False
                                if is_user_active:
                                    if s_key == "5-STAR BUY" and "5-STAR LONG" in user_running_strats and "5-STAR BUY" not in user_running_strats:
                                        user_can_trade = True
                                    elif s_key == "5-STAR SELL" and "5-STAR SHORT" in user_running_strats and "5-STAR SELL" not in user_running_strats:
                                        user_can_trade = True
                                    else:
                                        user_can_trade = False
                                else:
                                    user_can_trade = True 

                                if not user_can_trade:
                                    continue 

                                if u_db.get("risk_mode", False):
                                    usd_risk = u_db.get("risk_value", 1000.0) / 84.0
                                    u_qty = max(1, int(usd_risk / risk))
                                else:
                                    u_qty = int(u_db["btc_qty"] if sym == "BTCUSD" else u_db["eth_qty"])

                                order_status = place_breakout_entry_order(sym, u_qty, side, entry, u_db['api_key'], u_db['api_secret'])
                                
                                if order_status["success"]:
                                    any_order_placed = True
                                    add_log(f"Setup [{s_key}] registered at ${entry} for {sym} | Lot: {u_qty}", target_user=user, type_icon="⏳")
                                    with shared_mem.lock:
                                        if sym not in shared_mem.active_trades: shared_mem.active_trades[sym] = {}
                                        if user not in shared_mem.active_trades[sym]: shared_mem.active_trades[sym][user] = []
                                        shared_mem.active_trades[sym][user].append({
                                            'strategy': s_key, 'side': side, 'entry_price': entry, 'initial_sl': sl, 'sl': sl, 
                                            'targets': target_mesh, 'current_stage': 0, 'qty': u_qty, 'entry_order_id': order_status["order_id"], 
                                            'exchange_sl_id': None, 'is_triggered': False, 'live_pnl': 0.0,
                                            'exchange_t1_id': None, 'exchange_t2_id': None, 'exchange_t21_id': None
                                        })
                                    time.sleep(0.2)
                                else:
                                    fail_reason = order_status["error"]
                                    add_log(f"**API Alert: {sym} rejected -> {fail_reason}**", target_user=user, type_icon="❌", color="#ef4444")

                            if any_order_placed:
                                with shared_mem.lock:
                                    shared_mem.last_triggered_setup_info[sym] = {
                                        "entry": f"${entry:,.2f} (PENDING)", "sl": f"${sl:,.2f} (PENDING)", "t1": f"${target_mesh[1]:,.2f}", "t2": f"${target_mesh[2]:,.2f}", "status": f"⏳ **{s_key} ({side.upper()}) DETECTED**", "live_pnl": 0.0
                                    }

        except Exception as e: 
            add_log(f"Engine Warning: {str(e)}", target_user="ALL", type_icon="⚠️", color="#f59e0b")
            time.sleep(3)
        finally:
            with shared_mem.lock:
                shared_mem.is_processing = False
            time.sleep(1)

if not hasattr(st, "_global_thread_started"):
    threading.Thread(target=core_execution_engine, args=(mem,), daemon=True).start()
    st._global_thread_started = True

# =====================================================
# **RENDER LAYOUT**
# =====================================================
st.markdown(f"""
<div class="quantum-header-box">
    <div class="header-main-title">⚡ **QUANTUM ALGO MULTI-USER MATRIX**</div>
    <div class="header-sub-ip">Welcome, {current_usr.upper()} | Whitelisting Server IP: <span class="ip-glow">{SERVER_IP}</span></div>
</div>
""", unsafe_allow_html=True)

@st.fragment(run_every=3) 
def render_live_widgets():
    col_btc_w, col_eth_w = st.columns(2)
    with col_btc_w:
        with mem.lock:
            btc_info = mem.last_triggered_setup_info["BTCUSD"].copy()
            live_ltp = mem.ticker_feeds["BTCUSD"]["ltp"]
            r_1m = mem.ticker_feeds["BTCUSD"]["rsi_1m"]
            r_5m = mem.ticker_feeds["BTCUSD"]["rsi_5m"]
            r_15m = mem.ticker_feeds["BTCUSD"]["rsi_15m"]
            
        ticker_title = "BTCUSD Future Live" 
        st.markdown(f"""
        <div class="ticker-widget-card">
            <div><span class="ticker-dot-orange">●</span><span class="ticker-token-title">{ticker_title}</span></div>
            <div class="ticker-price-green">${live_ltp:,.2f}</div>
            <div class="rsi-grid-row">
                <span class="rsi-tab-item-1m">{r_1m:.2f}</span>
                <span class="rsi-tab-item-5m">{r_5m:.2f}</span>
                <span class="rsi-tab-item-15m">{r_15m:.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        pnl_val = btc_info.get("live_pnl", 0.0)
        pnl_class = "pnl-green" if pnl_val > 0 else ("pnl-red" if pnl_val < 0 else "pnl-gray")
        cls_entry = "signal-value-active" if btc_info['entry'] != "-" else "signal-value-waiting"
        cls_sl = "signal-value-active" if btc_info['sl'] != "-" else "signal-value-waiting"
        cls_t1 = "signal-value-active" if btc_info['t1'] != "-" else "signal-value-waiting"
        cls_t2 = "signal-value-active" if btc_info['t2'] != "-" else "signal-value-waiting"

        st.markdown(f"""
        <div class="pnl-analytics-card">
            <div style="font-size: 11px; color: #ffff00; font-weight: bold; margin-bottom: 2px;">Global Setup P&L:</div>
            <div class="live-pnl-text {pnl_class}">+${pnl_val:,.2f}</div>
        </div>
        <div class="signal-data-box">
            <div style="font-size: 11px; color: #ef4444; font-weight: bold; margin-bottom: 6px;">🔴 **SETUP STATUS: {btc_info['status']}**</div>
            <div class="signal-grid">
                <div><span class="signal-metric">ENTRY:</span> <span class="{cls_entry}">{btc_info['entry']}</span></div>
                <div><span class="signal-metric">STOP LOSS:</span> <span class="{cls_sl}">{btc_info['sl']}</span></div>
                <div><span class="signal-metric">TARGET 1:</span> <span class="{cls_t1}">{btc_info['t1']}</span></div>
                <div><span class="signal-metric">TARGET 2:</span> <span class="{cls_t2}">{btc_info['t2']}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_eth_w:
        with mem.lock:
            eth_info = mem.last_triggered_setup_info["ETHUSD"].copy()
            live_ltp_eth = mem.ticker_feeds["ETHUSD"]["ltp"]
            re_1m = mem.ticker_feeds["ETHUSD"]["rsi_1m"]
            re_5m = mem.ticker_feeds["ETHUSD"]["rsi_5m"]
            re_15m = mem.ticker_feeds["ETHUSD"]["rsi_15m"]
            
        ticker_title_eth = "ETHUSD Future Live"
        st.markdown(f"""
        <div class="ticker-widget-card">
            <div><span class="ticker-dot-purple">●</span><span class="ticker-token-title">{ticker_title_eth}</span></div>
            <div class="ticker-price-green">${live_ltp_eth:,.2f}</div>
            <div class="rsi-grid-row">
                <span class="rsi-tab-item-1m">{re_1m:.2f}</span>
                <span class="rsi-tab-item-5m">{re_5m:.2f}</span>
                <span class="rsi-tab-item-15m">{re_15m:.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        pnl_val_eth = eth_info.get("live_pnl", 0.0)
        pnl_class_eth = "pnl-green" if pnl_val_eth > 0 else ("pnl-red" if pnl_val_eth < 0 else "pnl-gray")
        cls_entry_eth = "signal-value-active" if eth_info['entry'] != "-" else "signal-value-waiting"
        cls_sl_eth = "signal-value-active" if eth_info['sl'] != "-" else "signal-value-waiting"
        cls_t1_eth = "signal-value-active" if eth_info['t1'] != "-" else "signal-value-waiting"
        cls_t2_eth = "signal-value-active" if eth_info['t2'] != "-" else "signal-value-waiting"

        st.markdown(f"""
        <div class="pnl-analytics-card">
            <div style="font-size: 11px; color: #ffff00; font-weight: bold; margin-bottom: 2px;">Global Setup P&L:</div>
            <div class="live-pnl-text {pnl_class_eth}">+${pnl_val_eth:,.2f}</div>
        </div>
        <div class="signal-data-box">
            <div style="font-size: 11px; color: #ef4444; font-weight: bold; margin-bottom: 6px;">🔴 **SETUP STATUS: {eth_info['status']}**</div>
            <div class="signal-grid">
                <div><span class="signal-metric">ENTRY:</span> <span class="{cls_entry_eth}">{eth_info['entry']}</span></div>
                <div><span class="signal-metric">STOP LOSS:</span> <span class="{cls_sl_eth}">{eth_info['sl']}</span></div>
                <div><span class="signal-metric">TARGET 1:</span> <span class="{cls_t1_eth}">{eth_info['t1']}</span></div>
                <div><span class="signal-metric">TARGET 2:</span> <span class="{cls_t2_eth}">{eth_info['t2']}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

render_live_widgets()

st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

# =====================================================
# ☑️ **REAL-TIME CLIENT MATRIX**
# =====================================================
st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-heading">☑️ **REAL-TIME CLIENT MATRIX & RISK CONTROLLER**</div>', unsafe_allow_html=True)

col_th1, col_th2, col_th3, col_th4, col_th5, col_th6, col_th7 = st.columns([1.5, 2, 2, 1.2, 1.2, 1.5, 1.2])
with col_th1: st.markdown("<span style='color:#38bdf8; font-size:11px;'>**CLIENT NAME**</span>", unsafe_allow_html=True)
with col_th2: st.markdown("<span style='color:#38bdf8; font-size:11px;'>**ENGINE STATUS**</span>", unsafe_allow_html=True)
with col_th3: st.markdown("<span style='color:#38bdf8; font-size:11px;'>**LOT SIZING**</span>", unsafe_allow_html=True)
with col_th4: st.markdown("<span style='color:#38bdf8; font-size:11px;'>**DAILY REALIZED**</span>", unsafe_allow_html=True)
with col_th5: st.markdown("<span style='color:#38bdf8; font-size:11px;'>**TOTAL NET P&L**</span>", unsafe_allow_html=True)
with col_th6: st.markdown("<span style='color:#38bdf8; font-size:11px;'>**TRADE ALLOW**</span>", unsafe_allow_html=True)
with col_th7: st.markdown("<span style='color:#ef4444; font-size:11px;'>**ACTION**</span>", unsafe_allow_html=True)
st.markdown("<hr style='border:1px solid #1e3a8a; margin-top:5px; margin-bottom:10px;'/>", unsafe_allow_html=True)

with mem.lock:
    current_users_db = mem.users_db.copy()

for u_name, u_data in list(current_users_db.items()):
    if not is_owner and str(current_usr).strip().lower() != str(u_name).strip().lower():
        continue
        
    col_r1, col_r2, col_r3, col_r4, col_r5, col_r6, col_r7 = st.columns([1.5, 2, 2, 1.2, 1.2, 1.5, 1.2])
    with col_r1: st.markdown(f"<span style='color:#38bdf8; font-size:13px;'>**{u_name}**</span>", unsafe_allow_html=True)
    with col_r2: 
        status_txt = "🟢 **PERSONAL SCANNER RUNNING**" if u_data.get("is_running", False) else "🔴 **STOPPED (PAUSED)**"
        st.markdown(f"<span style='color:#ffff00; font-size:12px;'>{status_txt}</span>", unsafe_allow_html=True)
    with col_r3: 
        if u_data.get("risk_mode", False):
            st.markdown(f"<span style='color:#00ff00; font-size:12px;'>**AUTO RISK (₹{u_data.get('risk_value', 1000.0):.0f})**</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:#ffff00; font-size:12px;'>**{u_data.get('btc_qty', 4)} BTC / {u_data.get('eth_qty', 4)} ETH**</span>", unsafe_allow_html=True)
    with col_r4: st.markdown("<span style='color:#ffff00; font-size:12px;'>**$0.00**</span>", unsafe_allow_html=True)
    with col_r5: st.markdown("<span style='color:#10b981; font-size:12px;'>**$0.00**</span>", unsafe_allow_html=True)
    
    with col_r6:
        if is_owner:
            is_approved = st.checkbox("**APPROVED**", value=u_data.get("active", True), key=f"chk_active_{u_name}")
            if is_approved != u_data.get("active", True):
                with mem.lock:
                    mem.users_db[u_name]["active"] = is_approved
                existing_users = load_users()
                if u_name in existing_users:
                    existing_users[u_name]["active"] = is_approved
                    save_users(existing_users)
                add_log(f"**User {u_name} status updated to {'APPROVED' if is_approved else 'PAUSED'}**", target_user="ALL")
                st.rerun()
        else:
            status_color = "#00ff00" if u_data.get("active", True) else "#ef4444"
            status_text = "**APPROVED**" if u_data.get("active", True) else "**PAUSED**"
            st.markdown(f"<span style='color:{status_color}; font-size:12px; font-weight:bold;'>{status_text}</span>", unsafe_allow_html=True)
            
    with col_r7:
        if is_owner:
            if st.button("❌", key=f"btn_rm_{u_name}", use_container_width=True):
                existing_users = load_users()
                if u_name in existing_users:
                    del existing_users[u_name]
                    save_users(existing_users)
                with mem.lock:
                    if u_name in mem.users_db:
                        del mem.users_db[u_name]
                add_log(f"**Client {u_name} deleted from terminal mesh.**", target_user="ALL", type_icon="🛑", color="#ef4444")
                st.rerun()
        else:
            st.markdown("<span style='color:#555555; font-size:12px;'>🔒 Lck</span>", unsafe_allow_html=True)
            
    st.markdown("<hr style='border:1px solid #1e3a8a; opacity:0.3; margin-top:5px; margin-bottom:5px;'/>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# =====================================================
# 🎛️ **YOUR ENGINE CONTROLS (INDIVIDUAL)**
# =====================================================
with mem.lock:
    my_db = mem.users_db.get(current_usr, {})
    my_sym = my_db.get("symbol_switches", {"BTCUSD": True, "ETHUSD": True})
    my_strat = my_db.get("strategy_switches", {})
    my_running = my_db.get("is_running", False)

col_body_sw1, col_body_sw2 = st.columns(2)

with col_body_sw1:
    st.markdown('<div class="panel-heading">🎛️ **YOUR PERSONAL ENGINE CONTROLS**</div>', unsafe_allow_html=True)
    engine_status_label = "ACTIVE (RUNNING)" if my_running else "DEACTIVATED (PAUSED)"
    st.markdown(f"### STATUS: <span style='color:#00ff00;'>**{engine_status_label}**</span>", unsafe_allow_html=True)
    
    if my_running:
        if st.button("🔴 **STOP MY SCANNER**", use_container_width=True):
            with mem.lock:
                mem.users_db[current_usr]["is_running"] = False
            u = load_users()
            u[current_usr]["is_running"] = False
            save_users(u)
            add_log(f"**{current_usr}'s Algorithmic System Stopped.**", target_user=current_usr, type_icon="🔴", color="#ef4444")
            st.rerun()
    else:
        if st.button("🟢 **START MY SCANNER**", use_container_width=True):
            with mem.lock:
                mem.users_db[current_usr]["is_running"] = True
            u = load_users()
            u[current_usr]["is_running"] = True
            save_users(u)
            add_log(f"**{current_usr}'s Algorithmic System Activated.**", target_user=current_usr, type_icon="🟢", color="#10b981")
            st.rerun()
        
    st.markdown("<hr style='border:1px dashed #1e3a8a; margin: 12px 0;'/>", unsafe_allow_html=True)
    st.markdown("<span style='color:#38bdf8; font-size:12px; font-weight:bold; text-transform:uppercase;'>**MY SYMBOL ALLOW LIST:**</span>", unsafe_allow_html=True)
    
    def update_my_syms(btc_val, eth_val):
        with mem.lock:
            mem.users_db[current_usr]["symbol_switches"] = {"BTCUSD": btc_val, "ETHUSD": eth_val}
        u = load_users()
        u[current_usr]["symbol_switches"] = {"BTCUSD": btc_val, "ETHUSD": eth_val}
        save_users(u)

    csym_b1, csym_b2 = st.columns([0.1, 0.9])
    with csym_b1: 
        val_btc = st.checkbox("**BTC_M**", value=my_sym.get("BTCUSD", True), key="my_chk_sym_btc", label_visibility="collapsed")
    with csym_b2: st.markdown('<span class="neon-blue-lbl" style="line-height: 1.8;">BTCUSD</span>', unsafe_allow_html=True)
        
    csym_e1, csym_e2 = st.columns([0.1, 0.9])
    with csym_e1: 
        val_eth = st.checkbox("**ETH_M**", value=my_sym.get("ETHUSD", True), key="my_chk_sym_eth", label_visibility="collapsed")
    with csym_e2: st.markdown('<span class="neon-blue-lbl" style="line-height: 1.8;">ETHUSD</span>', unsafe_allow_html=True)
    
    if val_btc != my_sym.get("BTCUSD", True) or val_eth != my_sym.get("ETHUSD", True):
        update_my_syms(val_btc, val_eth)
        st.rerun()

    st.markdown("<span style='color:#ef4444; font-size:11px;'>🚨 **MY EMERGENCY OPERATIONS:**</span>", unsafe_allow_html=True)
    if st.button("💥 **MY KILL SWITCH (SQUARE OFF ALL MY TRADES)**", use_container_width=True):
        u_db_copy = mem.users_db.get(current_usr, {})
        for sym in ["BTCUSD", "ETHUSD"]:
            cancel_all_orders_for_symbol(sym, u_db_copy.get('api_key'), u_db_copy.get('api_secret'))
            close_position_market(sym, u_db_copy.get('api_key'), u_db_copy.get('api_secret'))
            with mem.lock:
                if sym in mem.active_trades and current_usr in mem.active_trades[sym]:
                    del mem.active_trades[sym][current_usr]
        add_log("**EMERGENCY SQUARED OFF TRIGGERED FOR MY ACCOUNT!**", target_user=current_usr, type_icon="💥", color="#ef4444")
        st.rerun()

with col_body_sw2:
    st.markdown('<div class="panel-heading">⚙️ **MY STRATEGY PIPELINE SWITCHES**</div>', unsafe_allow_html=True)
    
    def update_my_strats(s_dict):
        with mem.lock:
            mem.users_db[current_usr]["strategy_switches"] = s_dict
        u = load_users()
        u[current_usr]["strategy_switches"] = s_dict
        save_users(u)
    
    c2b1, c2b2 = st.columns([0.1, 0.9])
    with c2b1: p2b = st.checkbox("**2B**", value=my_strat.get("2-STAR BUY", True), key="m_chk_2_buy", label_visibility="collapsed")
    with c2b2: st.markdown('<span class="neon-green-lbl" style="line-height: 2.0;">**1. 2-STAR BUY BREAKOUT**</span>', unsafe_allow_html=True)

    c2s1, c2s2 = st.columns([0.1, 0.9])
    with c2s1: p2s = st.checkbox("**2S**", value=my_strat.get("2-STAR SELL", True), key="m_chk_2_sell", label_visibility="collapsed")
    with c2s2: st.markdown('<span class="neon-red-lbl" style="line-height: 2.0;">**2. 2-STAR SELL BREAKOUT**</span>', unsafe_allow_html=True)

    cl1, cl2 = st.columns([0.1, 0.9])
    with cl1: p5l = st.checkbox("**5L**", value=my_strat.get("5-STAR LONG", True), key="m_chk_5_long", label_visibility="collapsed")
    with cl2: st.markdown('<span class="neon-green-lbl" style="line-height: 2.0;">**3. 5-STAR LONG**</span>', unsafe_allow_html=True)
        
    cs1, cs2 = st.columns([0.1, 0.9])
    with cs1: p5s = st.checkbox("**5S**", value=my_strat.get("5-STAR SHORT", True), key="m_chk_5_short", label_visibility="collapsed")
    with cs2: st.markdown('<span class="neon-red-lbl" style="line-height: 2.0;">**4. 5-STAR SHORT**</span>', unsafe_allow_html=True)
        
    cb1, cb2 = st.columns([0.1, 0.9])
    with cb1: p5buy = st.checkbox("**5B**", value=my_strat.get("5-STAR BUY", True), key="m_chk_buy", label_visibility="collapsed")
    with cb2: st.markdown('<span class="neon-green-lbl" style="line-height: 2.0;">**5. 5-STAR BUY BREAKOUT**</span>', unsafe_allow_html=True)
        
    cx1, cx2 = st.columns([0.1, 0.9])
    with cx1: p5sell = st.checkbox("**5S**", value=my_strat.get("5-STAR SELL", True), key="m_chk_sell", label_visibility="collapsed")
    with cx2: st.markdown('<span class="neon-red-lbl" style="line-height: 2.0;">**6. 5-STAR SELL BREAKOUT**</span>', unsafe_allow_html=True)

    current_strats_gui = {
        "2-STAR BUY": p2b, "2-STAR SELL": p2s, "5-STAR LONG": p5l,
        "5-STAR SHORT": p5s, "5-STAR BUY": p5buy, "5-STAR SELL": p5sell
    }
    if current_strats_gui != my_strat:
        update_my_strats(current_strats_gui)
        st.rerun()

# BOTTOM NAVIGATION TAB CONTROLLER
tab_logs, tab_rms = st.tabs(["📊 **LIVE DIAGNOSTICS LOGS**", "🛡️ **RISK CONTROLLER (RMS)**"])

with tab_logs:
    st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">📊 **LIVE TERMINAL DIAGNOSTIC REPORT**</div>', unsafe_allow_html=True)
    
    @st.fragment(run_every=5) 
    def render_live_logs():
        with mem.lock:
            logs = mem.last_terminal_logs.copy()
            
        logs_html = ""
        for log in logs:
            if is_owner or log["user"] == "ALL" or log["user"] == current_usr:
                logs_html += f"<div><span style='color: #38bdf8;'>[{log['timestamp']}]</span> <span style='color:{log['color']}; font-weight:bold;'>{log['msg']}</span></div>"
                
        st.markdown(f'<div class="diagnostic-logger-container">{logs_html}</div>', unsafe_allow_html=True)
        
    render_live_logs()
    st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# 🛡️ **RISK CONTROLLER (PERSONAL CONFIGURATIONS)**
# =====================================================
with tab_rms:
    st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">🛡️ **RISK MANAGEMENT SYSTEM (RMS) CONTROLLER**</div>', unsafe_allow_html=True)
    
    with mem.lock:
        current_users_rms = mem.users_db.copy()
        
    if not current_users_rms:
        st.info("**No active clients found.**")
    else:
        for u_name, u_data in list(current_users_rms.items()):
            if not is_owner and str(current_usr).strip().lower() != str(u_name).strip().lower():
                continue
                
            st.markdown(f"<span style='color:#38bdf8; font-size:14px; font-weight:bold; border-bottom: 1px solid #1e3a8a; display:block; padding-bottom:4px;'>👤 **Client Configuration Profile: {u_name}**</span>", unsafe_allow_html=True)
            
            with st.container():
                st.markdown("<span style='color:#ffff00; font-size:11px; font-weight:bold;'>🔐 **UPDATE API KEYS (Optional):**</span>", unsafe_allow_html=True)
                ak_col, as_col = st.columns(2)
                with ak_col:
                    new_ak = st.text_input("**API Key**", value=u_data.get("api_key", ""), type="password", key=f"up_ak_{u_name}")
                with as_col:
                    new_as = st.text_input("**API Secret**", value=u_data.get("api_secret", ""), type="password", key=f"up_as_{u_name}")
                
                st.markdown("<span style='color:#ffff00; font-size:11px; font-weight:bold;'>📊 **QUANTUM LOT & RISK PROFILES:**</span>", unsafe_allow_html=True)
                rc1, rc2, rc3, rc4 = st.columns(4)
                with rc1:
                    risk_mode = st.checkbox("**AUTO RISK QTY**", value=u_data.get("risk_mode", False), key=f"rmode_{u_name}")
                with rc2:
                    risk_val = st.number_input("**Max Risk Amount (₹ INR)**", value=float(u_data.get("risk_value", 1000.0)), key=f"rval_{u_name}", step=100.0)
                with rc3:
                    btc_q = st.number_input("**BTC Manual Qty (Lots)**", min_value=1, value=int(u_data.get("btc_qty", 4)), key=f"rbtc_{u_name}")
                with rc4:
                    eth_q = st.number_input("**ETH Manual Qty (Lots)**", min_value=1, value=int(u_data.get("eth_qty", 4)), key=f"reth_{u_name}")
                
                if st.button(f"💾 **SAVE CONFIG FOR {u_name}**", key=f"save_rms_{u_name}", use_container_width=True):
                    with mem.lock:
                        mem.users_db[u_name]["api_key"] = new_ak
                        mem.users_db[u_name]["api_secret"] = new_as
                        mem.users_db[u_name]["risk_mode"] = risk_mode
                        mem.users_db[u_name]["risk_value"] = risk_val
                        mem.users_db[u_name]["btc_qty"] = btc_q
                        mem.users_db[u_name]["eth_qty"] = eth_q
                    
                    existing_users = load_users()
                    if u_name in existing_users:
                        existing_users[u_name]["api_key"] = new_ak
                        existing_users[u_name]["api_secret"] = new_as
                        existing_users[u_name]["risk_mode"] = risk_mode
                        existing_users[u_name]["risk_value"] = risk_val
                        existing_users[u_name]["btc_qty"] = btc_q
                        existing_users[u_name]["eth_qty"] = eth_q
                        save_users(existing_users)
                    
                    add_log(f"**Personalized Matrix saved successfully for {u_name}.**", target_user=u_name, type_icon="🛡️")
                    st.success(f"**Config Successfully Saved for {u_name}!**")
                    time.sleep(0.5)
                    st.rerun()
            st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Logout option block
st.markdown("---")
col_btm1, col_btm2 = st.columns([4, 1])
with col_btm1:
    st.markdown(f"Current Active User: `**{current_usr}**`") 
with col_btm2:
    if st.button("🚪 **LOGOUT**"):
        st.session_state["logged_in"] = False
        st.session_state["current_user"] = ""
        st.query_params.clear() 
        st.rerun()
