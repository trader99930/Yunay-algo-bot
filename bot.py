import time
import json
import threading
import pandas as pd
import requests
import urllib3
import streamlit as st
import datetime
from auth import load_users, save_users

# ✅ SYSTEM STABILITY FOR TERMUX / IPV4 OPTIMIZATION
import urllib3.util.connection as urllib3_cn
urllib3_cn.HAS_IPV6 = False

# Global Network Session for Performance Optimization
session = requests.Session()

# Streamlit Configuration
st.set_page_config(page_title="Quantum Multi-User Terminal", layout="wide", initial_sidebar_state="collapsed")

# =====================================================
# NIFTY 50 (TOP 50 STOCKS) FOR FYERS SECURITIES
# =====================================================
TOP_50_STOCKS = [
    "NSE:RELIANCE-EQ", "NSE:TCS-EQ", "NSE:HDFCBANK-EQ", "NSE:ICICIBANK-EQ", "NSE:INFY-EQ",
    "NSE:ITC-EQ", "NSE:SBIN-EQ", "NSE:BHARTIARTL-EQ", "NSE:BAJFINANCE-EQ", "NSE:L&T-EQ",
    "NSE:HUL-EQ", "NSE:AXISBANK-EQ", "NSE:KOTAKBANK-EQ", "NSE:ASIANPAINT-EQ", "NSE:MARUTI-EQ",
    "NSE:SUNPHARMA-EQ", "NSE:TITAN-EQ", "NSE:TATASTEEL-EQ", "NSE:ULTRACEMCO-EQ", "NSE:BAJAJFINSV-EQ",
    "NSE:M&M-EQ", "NSE:WIPRO-EQ", "NSE:HCLTECH-EQ", "NSE:TATAMOTORS-EQ", "NSE:NESTLEIND-EQ",
    "NSE:NTPC-EQ", "NSE:POWERGRID-EQ", "NSE:TECHM-EQ", "NSE:INDUSINDBK-EQ", "NSE:ONGC-EQ",
    "NSE:JSWSTEEL-EQ", "NSE:HINDALCO-EQ", "NSE:GRASIM-EQ", "NSE:ADANIPORTS-EQ", "NSE:TATACONSUM-EQ",
    "NSE:DRREDDY-EQ", "NSE:CIPLA-EQ", "NSE:DIVISLAB-EQ", "NSE:EICHERMOT-EQ", "NSE:APOLLOHOSP-EQ",
    "NSE:BAJAJ-AUTO-EQ", "NSE:BRITANNIA-EQ", "NSE:SBILIFE-EQ", "NSE:HDFCLIFE-EQ", "NSE:LTIM-EQ",
    "NSE:HEROMOTOCO-EQ", "NSE:COALINDIA-EQ", "NSE:UPL-EQ", "NSE:BPCL-EQ", "NSE:ADANIENT-EQ"
]

# =====================================================
# GLOBAL ENGINE MEMORY MESH (Thread-Safe)
# =====================================================
class GlobalEngineMemory:
    def __init__(self):
        self.lock = threading.Lock()
        self.users_db = {}
        self.global_engine_running = True
        self.active_trades = {}
        self.ordered_candles = {}
        self.is_processing = False
        
        self.last_triggered_setup_info = {
            sym: {"entry": "-", "sl": "-", "t1": "-", "t2": "-", "status": "🔵 SCANNING FOR SETUPS...", "live_pnl": 0.0}
            for sym in TOP_50_STOCKS
        }
        
        self.symbol_switches = {sym: True for sym in TOP_50_STOCKS}
        
        self.strategy_switches = {
            "2-STAR BUY": True, "2-STAR SELL": True,
            "5-STAR LONG": True, "5-STAR SHORT": True, 
            "5-STAR BB BUY": True, "5-STAR BB SELL": True
        }
        
        self.last_terminal_logs = [
            "<div><span style='color: #38bdf8;'>[SYSTEM]</span> 🚀 Fyers Advance Controller Engine Activated.</div>"
        ]
        self.ticker_feeds = {
            sym: {"ltp": 0.0, "rsi_1m": 0.0, "rsi_5m": 0.0, "rsi_15m": 0.0}
            for sym in TOP_50_STOCKS
        }

if "mem_instance" not in st.session_state:
    if not hasattr(st, "_global_algo_memory"):
        st._global_algo_memory = GlobalEngineMemory()
    st.session_state["mem_instance"] = st._global_algo_memory

mem = st.session_state["mem_instance"]

with mem.lock:
    for symbol_key in TOP_50_STOCKS:
        if symbol_key in mem.last_triggered_setup_info and mem.last_triggered_setup_info[symbol_key]["entry"] == "WAITING":
            mem.last_triggered_setup_info[symbol_key] = {"entry": "-", "sl": "-", "t1": "-", "t2": "-", "status": "🔵 SCANNING FOR SETUPS...", "live_pnl": 0.0}
        if symbol_key not in mem.symbol_switches:
            mem.symbol_switches[symbol_key] = True

current_usr = "Yunay"
is_owner = True

# ✅ TOKEN AUTO-SYNC
all_u = load_users()
with mem.lock:
    for u_name, u_data in all_u.items():
        if u_data.get("api_key"): 
            old_strats = u_data.get("strategy_switches", {})
            safe_strats = {
                "2-STAR BUY": old_strats.get("2-STAR BUY", True),
                "2-STAR SELL": old_strats.get("2-STAR SELL", True),
                "5-STAR LONG": old_strats.get("5-STAR LONG", True),
                "5-STAR SHORT": old_strats.get("5-STAR SHORT", True),
                "5-STAR BB BUY": old_strats.get("5-STAR BB BUY", old_strats.get("5-STAR BUY", True)),
                "5-STAR BB SELL": old_strats.get("5-STAR BB SELL", old_strats.get("5-STAR SELL", True))
            }
            mem.users_db[u_name] = {
                "api_key": u_data["api_key"],          
                "api_secret": u_data["api_secret"],    
                "btc_qty": u_data.get("btc_qty", 10),  
                "eth_qty": u_data.get("eth_qty", 10),  
                "risk_mode": u_data.get("risk_mode", False),
                "risk_value": u_data.get("risk_value", 1000.0),
                "active": u_data.get("active", True),
                "symbol_switches": u_data.get("symbol_switches", mem.users_db.get(u_name, {}).get("symbol_switches", {s: True for s in TOP_50_STOCKS})),
                "strategy_switches": safe_strats
            }

st.markdown("""
    <style>
    .stApp { background-color: #060913 !important; color: #ffff00 !important; font-family: monospace; font-weight: bold !important; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1.5rem !important; max-width: 98% !important; }
    .quantum-header-box { background-color: #0b132b; border: 2px solid #1e3a8a; padding: 15px 20px; border-radius: 6px; margin-bottom: 18px; }
    .header-main-title { color: #38bdf8; font-weight: bold; font-size: 17px; letter-spacing: 1px; }
    .header-sub-ip { color: #ffff00 !important; font-weight: bold !important; font-size: 11px; margin-top: 4px; }
    .ip-glow { color: #10b981; font-weight: bold; }
    .grid-panel { background-color: #0b132b !important; border: 2px solid #1e3a8a !important; border-radius: 6px !important; padding: 18px !important; margin-bottom: 15px !important; }
    .panel-heading { color: #38bdf8 !important; font-size: 13px !important; font-weight: bold !important; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 15px; border-bottom: 1px dashed #1e3a8a; padding-bottom: 6px; }
    .ticker-widget-card { background-color: #0d1b3e; border: 1px solid #1e3a8a; padding: 10px 14px; border-radius: 6px; margin-bottom: 5px; height: 100%; }
    .ticker-token-title { color: #ffff00 !important; font-size: 11px; font-weight: bold !important; }
    .ticker-dot-orange { color: #f59e0b; font-size: 12px; margin-right: 4px; }
    .ticker-price-green { color: #38bdf8 !important; font-size: 20px !important; font-weight: bold; margin: 3px 0; }
    .rsi-grid-row { display: flex; gap: 8px; margin-top: 5px; font-size: 10px; margin-bottom: 3px; }
    .rsi-tab-item-1m { color: #ffff00 !important; font-weight: 900 !important; padding: 2px 5px; border-radius: 3px; border: 1px solid #3b82f6; }
    .rsi-tab-item-5m { color: #00ff00 !important; font-weight: 900 !important; padding: 2px 5px; border-radius: 3px; border: 1px solid #3b82f6; }
    .rsi-tab-item-15m { color: #ff0000 !important; font-weight: 900 !important; padding: 2px 5px; border-radius: 3px; border: 1px solid #3b82f6; }
    .pnl-analytics-card { background-color: #060913; border: 1px solid #1e3a8a; border-radius: 4px; padding: 10px; margin-bottom: 8px; }
    .live-pnl-text { font-size: 18px !important; font-weight: bold; font-family: monospace; }
    .pnl-green { color: #10b981 !important; }
    .pnl-red { color: #ef4444 !important; }
    .pnl-gray { color: #ffff00 !important; }
    .signal-data-box { background-color: #060913; border: 1px dashed #1e3a8a; border-radius: 6px; padding: 10px; font-size: 11px;}
    .signal-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 5px; font-size: 10px; }
    .signal-metric { color: #38bdf8 !important; font-weight: bold !important; }
    .signal-value-active { color: #10b981; font-weight: bold; }
    .signal-value-waiting { color: #e2e8f0 !important; font-weight: 500 !important; }
    .diagnostic-logger-container { background-color: #060913 !important; border: 1px solid #1e3a8a !important; padding: 15px; border-radius: 6px; height: 250px; overflow-y: auto; font-family: monospace; font-size: 12px; line-height: 1.8; color: #ffff00 !important; }
    input { background-color: #0d1b3e !important; color: #ffffff !important; font-weight: bold !important; border: 2px solid #1e3a8a !important; border-radius: 4px; padding: 8px; }
    div.stButton > button, div[data-testid="stForm"] button, .stFormSubmitButton button { background-color: #07090e !important; border: 2px solid #1e3a8a !important; border-radius: 6px !important; font-size: 11px !important; font-weight: bold !important; text-transform: uppercase !important; padding: 4px 10px !important; transition: all 0.2s ease-in-out !important; }
    div.stButton > button:hover, div[data-testid="stForm"] button:hover { background-color: #1c2d5a !important; border-color: #38bdf8 !important; box-shadow: 0px 0px 10px rgba(56, 189, 248, 0.4) !important; }
    .neon-green-lbl { color: #00ff00 !important; font-weight: bold !important; font-size: 13px !important; text-shadow: 0px 0px 6px rgba(0,255,0,0.6); display: inline-block; }
    .neon-red-lbl { color: #ff0000 !important; font-weight: bold !important; font-size: 13px !important; text-shadow: 0px 0px 6px rgba(255,0,0,0.6); display: inline-block; }
    .neon-blue-lbl { color: #38bdf8 !important; font-weight: bold !important; font-size: 13px !important; text-shadow: 0px 0px 6px rgba(56,189,248,0.6); display: inline-block; }
    div[data-testid="stColumn"] { display: block !important; }
    div[data-testid="stCheckbox"] label { margin-bottom: 0px !important; padding-top: 5px !important; }
    div[data-testid="stTabs"] button { color: #38bdf8 !important; font-size: 13px !important; font-weight: bold !important; background-color: #07090e !important; border: 1px solid #1e3a8a !important; margin-right: 5px; padding: 8px 16px !important; }
    div[data-testid="stTabs"] button[aria-selected="true"] { color: #ffff00 !important; border-bottom: 2px solid #ffff00 !important; background-color: #0d1b3e !important; }
    .stWidgetFormLabel, div[data-testid="stMarkdownContainer"] p, label { color: #ffff00 !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_server_ip():
    try: return session.get("https://api.ipify.org", timeout=5).text
    except Exception: return "152.58.109.90"

SERVER_IP = get_server_ip()

def add_log(msg, type_icon="🚀"):
    ist_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)
    timestamp = ist_time.strftime("%H:%M:%S")
    full_msg = f"<div><span style='color: #38bdf8;'>[{timestamp}]</span> {type_icon} <span style='color:#ffff00; font-weight:bold;'>{msg}</span></div>"
    with mem.lock:  
        mem.last_terminal_logs.insert(0, full_msg)
        if len(mem.last_terminal_logs) > 30: 
            mem.last_terminal_logs.pop()

# =====================================================
# FYERS API CONNECTORS
# =====================================================
FYERS_API_URL = "https://api-t1.fyers.in/api/v3"
FYERS_DATA_URL = "https://api-t1.fyers.in/data"

def send_fyers_request(method, url_type, path, client_id, access_token, payload=None):
    if not client_id or not access_token: return {"s": "error", "message": "Keys Missing"}
    headers = {"Authorization": f"{client_id}:{access_token}", "Content-Type": "application/json"}
    base = FYERS_API_URL if url_type == "api" else FYERS_DATA_URL
    try:
        if method == "POST": r = session.post(base + path, headers=headers, json=payload, timeout=12)
        elif method == "DELETE": r = session.delete(base + path, headers=headers, json=payload, timeout=12)
        else: r = session.get(base + path, headers=headers, params=payload, timeout=12)
        return r.json()
    except Exception as e: return {"s": "error", "message": str(e)}

def round_to_tick(price): return round(float(price) * 20) / 20

def get_all_open_positions(client_id, access_token):
    try:
        res = send_fyers_request("GET", "api", "/positions", client_id, access_token)
        pos_dict = {}
        if res and res.get("s") == "ok":
            for pos in res.get("netPositions", []):
                pos_dict[pos.get("symbol")] = abs(int(pos.get("netQty", 0)))
        return pos_dict
    except Exception: return {}

def place_breakout_entry_order(symbol, size, side, trigger_price, client_id, access_token):
    if size <= 0: return {"success": False, "error": "Size cannot be zero"}
    final_price = round_to_tick(trigger_price)
    fyers_side = 1 if side.lower() == "buy" else -1
    payload = {"symbol": symbol, "qty": int(size), "type": 2, "side": fyers_side, "productType": "INTRADAY", "limitPrice": 0, "stopPrice": 0, "validity": "DAY", "offlineOrder": False}
    res = send_fyers_request("POST", "api", "/orders/sync", client_id, access_token, payload)
    if res and res.get("s") == "ok": return {"success": True, "order_id": res.get("id")}
    err_msg = res.get("message", "Execution Rejected") if res else "Unknown API Error"
    return {"success": False, "error": err_msg}

def cancel_order(order_id, symbol, client_id, access_token):
    if not order_id: return False
    res = send_fyers_request("DELETE", "api", "/orders/sync", client_id, access_token, {"id": str(order_id)})
    return res and res.get("s") == "ok"

def cancel_all_orders_for_symbol(symbol, client_id, access_token):
    res = send_fyers_request("GET", "api", "/orders", client_id, access_token)
    if res and res.get("s") == "ok":
        for order in res.get("orderBook", []):
            if order.get("symbol") == symbol and order.get("status") in [6, 4]: 
                cancel_order(order.get("id"), symbol, client_id, access_token)

def close_position_market(symbol, client_id, access_token):
    try:
        res = send_fyers_request("GET", "api", "/positions", client_id, access_token)
        if res and res.get("s") == "ok":
            for pos in res.get("netPositions", []):
                if pos.get("symbol") == symbol and pos.get("netQty") != 0:
                    qty = abs(pos.get("netQty"))
                    side = -1 if pos.get("netQty") > 0 else 1
                    payload = {"symbol": symbol, "qty": qty, "type": 2, "side": side, "productType": "INTRADAY", "limitPrice": 0, "stopPrice": 0, "validity": "DAY"}
                    send_fyers_request("POST", "api", "/orders/sync", client_id, access_token, payload)
    except Exception: pass

def place_stop_loss(symbol, size, side, sl_price, client_id, access_token):
    if size <= 0: return None
    final_sl = round_to_tick(sl_price)
    fyers_side = 1 if side.lower() == "buy" else -1
    payload = {"symbol": symbol, "qty": int(size), "type": 3, "side": fyers_side, "productType": "INTRADAY", "limitPrice": 0, "stopPrice": final_sl, "validity": "DAY"}
    res = send_fyers_request("POST", "api", "/orders/sync", client_id, access_token, payload)
    if res and res.get("s") == "ok": return res.get("id")
    return None

def place_limit_profit_target(symbol, size, side, price, client_id, access_token):
    if size <= 0: return None
    final_price = round_to_tick(price)
    fyers_side = 1 if side.lower() == "buy" else -1
    payload = {"symbol": symbol, "qty": int(size), "type": 1, "side": fyers_side, "productType": "INTRADAY", "limitPrice": final_price, "stopPrice": 0, "validity": "DAY"}
    res = send_fyers_request("POST", "api", "/orders/sync", client_id, access_token, payload)
    if res and res.get("s") == "ok": return res.get("id")
    return None

def rsi_calc(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    return 100 - (100 / (1 + (avg_gain / (avg_loss + 1e-10))))

def fetch_candles_df(symbol, timeframe, limit=100):
    try:
        res_map = {"1m": "1", "5m": "5", "15m": "15"}
        f_res = res_map.get(timeframe, "1")
        end_dt = datetime.datetime.now()
        start_dt = end_dt - datetime.timedelta(days=5) 
        
        payload = {
            "symbol": symbol, "resolution": f_res, "date_format": "1",
            "range_from": start_dt.strftime("%Y-%m-%d"), "range_to": end_dt.strftime("%Y-%m-%d"), "cont_flag": "1"
        }
        active_token, active_client = "", ""
        for u in mem.users_db.values():
            if u.get('api_key') and u.get('api_secret'):
                active_client, active_token = u['api_key'], u['api_secret']
                break
        if not active_token: return None
        
        r = send_fyers_request("GET", "data", "/history", active_client, active_token, payload)
        if r and r.get("s") == "ok" and "candles" in r:
            cols = ["time", "open", "high", "low", "close", "volume"]
            df = pd.DataFrame(r["candles"], columns=cols)
            for col in ["close", "high", "low"]: df[col] = pd.to_numeric(df[col])
            return df.tail(limit).reset_index(drop=True)
        return None
    except Exception: return None

# =====================================================
# CORE PIPELINE TRADE ENGINE AUTOMATION (FYERS)
# =====================================================
def core_execution_engine(shared_mem):
    while True:
        if not shared_mem.global_engine_running:
            time.sleep(1.5)
            continue
        try:
            active_client, active_token = "", ""
            with shared_mem.lock:
                for u in shared_mem.users_db.values():
                    if u.get('api_key') and u.get('api_secret'):
                        active_client, active_token = u['api_key'], u['api_secret']
                        break
            
            quotes_list = []
            user_positions_cache = {}
            if active_client and active_token:
                with shared_mem.lock:
                    for u_name, u_db in shared_mem.users_db.items():
                        if u_db.get('api_key') and u_db.get('active', True):
                            user_positions_cache[u_name] = get_all_open_positions(u_db['api_key'], u_db['api_secret'])
                            time.sleep(0.3) 
                
                chunked_symbols = [TOP_50_STOCKS[i:i + 20] for i in range(0, len(TOP_50_STOCKS), 20)]
                for chunk in chunked_symbols:
                    try:
                        sym_str = ",".join(chunk)
                        time.sleep(0.3) 
                        headers = {"Authorization": f"{active_client}:{active_token}", "Content-Type": "application/json"}
                        raw_r = session.get(FYERS_DATA_URL + f"/quotes?symbols={sym_str}", headers=headers, timeout=10)
                        
                        if raw_r.status_code == 200:
                            r = raw_r.json()
                            if r and r.get("s") == "ok" and "d" in r:
                                for data in r["d"]:
                                    s_name = data["n"]
                                    lp = round(float(data["v"].get("lp", 0)), 2)
                                    chp = float(data["v"].get("chp", 0)) # Percentage change
                                    quotes_list.append({"sym": s_name, "lp": lp, "chp": chp})
                                    with shared_mem.lock:
                                        if s_name in shared_mem.ticker_feeds:
                                            shared_mem.ticker_feeds[s_name]["ltp"] = lp
                    except Exception: pass

            # ✅ SMART FILTER: ONLY SELECT TOP 5 GAINERS AND TOP 5 LOSERS (TOTAL 10 STOCKS)
            dynamic_top_10 = TOP_50_STOCKS[:10] # Default fallback
            if len(quotes_list) > 0:
                quotes_list.sort(key=lambda x: x["chp"], reverse=True)
                top_5_gainers = [x["sym"] for x in quotes_list[:5]]
                top_5_losers = [x["sym"] for x in quotes_list[-5:]] if len(quotes_list) >= 10 else []
                dynamic_top_10 = top_5_gainers + top_5_losers

            # 🛠️ TRADE MANAGEMENT LOOP (Checks all active positions)
            for sym in TOP_50_STOCKS:
                with shared_mem.lock:
                    live_price = shared_mem.ticker_feeds[sym]["ltp"]
                    has_trades = sym in shared_mem.active_trades
                if not live_price or not has_trades: continue
                
                any_user_active_on_exchange = False
                any_trade_ever_triggered = False
                total_pnl = 0.0

                with shared_mem.lock: user_keys = list(shared_mem.active_trades[sym].keys())

                for user in user_keys:
                    with shared_mem.lock: u_db = shared_mem.users_db.get(user)
                    if not u_db or not u_db.get('api_key') or not u_db.get('active', True): continue
                    
                    with shared_mem.lock: trades_list = shared_mem.active_trades[sym][user]
                    ex_qty = user_positions_cache.get(user, {}).get(sym, 0)
                    if ex_qty > 0: any_user_active_on_exchange = True

                    for trade in list(trades_list):
                        if trade.get('is_triggered', False): any_trade_ever_triggered = True

                        mult = 1 if trade['side'] == 'buy' else -1
                        calc_pnl = round((live_price - trade['entry_price']) * mult * trade['qty'], 2)
                        trade['live_pnl'] = calc_pnl
                        total_pnl += calc_pnl

                        if not trade['is_triggered']:
                            is_sl_breached_pre_entry = (trade['side'] == 'buy' and live_price <= trade['initial_sl']) or \
                                                       (trade['side'] == 'sell' and live_price >= trade['initial_sl'])
                            if is_sl_breached_pre_entry:
                                cancel_order(trade['entry_order_id'], sym, u_db['api_key'], u_db['api_secret'])
                                with shared_mem.lock:
                                    if trade in trades_list: trades_list.remove(trade)
                                continue
                            
                            if ex_qty > 0:
                                trade['is_triggered'] = True
                                any_trade_ever_triggered = True
                                with shared_mem.lock:
                                    shared_mem.last_triggered_setup_info[sym]["entry"] = f"₹{trade['entry_price']:,.2f} (FILLED)"
                                    shared_mem.last_triggered_setup_info[sym]["sl"] = f"₹{trade['sl']:,.2f} (ACTIVE)"
                                    shared_mem.last_triggered_setup_info[sym]["status"] = f"🟢 {trade['strategy']} LIVE (SL ACTIVE)"
                                add_log(f"💥 Breakout Triggered for {user} on {sym} via {trade['strategy']}!", type_icon="⚡")
                                
                                opposite_side = "sell" if trade['side'] == 'buy' else 'buy'
                                trade['exchange_sl_id'] = place_stop_loss(sym, trade['qty'], opposite_side, trade['sl'], u_db['api_key'], u_db['api_secret'])
                                q_t1 = int(trade['qty'] * 0.50); q_t2 = int(trade['qty'] * 0.25); q_t21 = trade['qty'] - q_t1 - q_t2
                                trade['exchange_t1_id'] = place_limit_profit_target(sym, q_t1, opposite_side, trade['targets'][1], u_db['api_key'], u_db['api_secret']) if q_t1 > 0 else None
                                trade['exchange_t2_id'] = place_limit_profit_target(sym, q_t2, opposite_side, trade['targets'][2], u_db['api_key'], u_db['api_secret']) if q_t2 > 0 else None
                                trade['exchange_t21_id'] = place_limit_profit_target(sym, q_t21, opposite_side, trade['targets'][21], u_db['api_key'], u_db['api_secret']) if q_t21 > 0 else None
                                continue

                        if trade['is_triggered']:
                            is_hard_sl_hit = (trade['side'] == 'buy' and live_price <= trade['sl']) or \
                                             (trade['side'] == 'sell' and live_price >= trade['sl'])
                            
                            if ex_qty == 0 or is_hard_sl_hit:
                                cancel_all_orders_for_symbol(sym, u_db['api_key'], u_db['api_secret'])
                                if ex_qty > 0: close_position_market(sym, u_db['api_key'], u_db['api_secret'])
                                with shared_mem.lock:
                                    if trade in trades_list: trades_list.remove(trade)
                                add_log(f"Stop-Loss Breached / Flattened on {sym} ({trade['strategy']}).", type_icon="🛑")
                                continue

                            current_high_target_hit = trade['current_stage']
                            for target_idx in range(current_high_target_hit + 1, 22):
                                target_price_level = trade['targets'][target_idx]
                                is_target_passed = (trade['side'] == 'buy' and live_price >= target_price_level) or \
                                                   (trade['side'] == 'sell' and live_price <= target_price_level)
                                
                                if is_target_passed:
                                    trade['current_stage'] = target_idx
                                    opposite_side = "sell" if trade['side'] == 'buy' else 'buy'
                                    if trade.get('exchange_sl_id'): cancel_order(trade['exchange_sl_id'], sym, u_db['api_key'], u_db['api_secret'])
                                    
                                    if target_idx == 1:
                                        trade['sl'] = trade['entry_price']; status_str = f"🎯 {trade['strategy']} TA1 HIT (SL @ COST)"
                                    elif target_idx == 2:
                                        trade['sl'] = trade['targets'][1]; status_str = f"🎯 {trade['strategy']} TA2 HIT (SL @ TA1)"
                                    else:
                                        trade['sl'] = trade['targets'][target_idx - 1]; status_str = f"🔄 {trade['strategy']} TA{target_idx} HIT (SL TRAILED)"
                                    
                                    time.sleep(0.5) 
                                    updated_live_qty = user_positions_cache.get(user, {}).get(sym, 0)
                                    if updated_live_qty > 0:
                                        trade['exchange_sl_id'] = place_stop_loss(sym, updated_live_qty, opposite_side, trade['sl'], u_db['api_key'], u_db['api_secret'])
                                    
                                    with shared_mem.lock:
                                        shared_mem.last_triggered_setup_info[sym]["sl"] = f"₹{trade['sl']:,.2f} (TRAILED)"
                                        shared_mem.last_triggered_setup_info[sym]["status"] = status_str
                                    
                                    if target_idx == 21:
                                        cancel_all_orders_for_symbol(sym, u_db['api_key'], u_db['api_secret'])
                                        if updated_live_qty > 0: close_position_market(sym, u_db['api_key'], u_db['api_secret'])
                                        with shared_mem.lock:
                                            if trade in trades_list: trades_list.remove(trade)
                                    break
                
                with shared_mem.lock: shared_mem.last_triggered_setup_info[sym]["live_pnl"] = total_pnl
                if any_trade_ever_triggered and not any_user_active_on_exchange:
                    with shared_mem.lock:
                        shared_mem.active_trades[sym].clear()
                        shared_mem.last_triggered_setup_info[sym] = {"entry": "-", "sl": "-", "t1": "-", "t2": "-", "status": "🔵 SCANNING FOR SETUPS...", "live_pnl": 0.0}

            # =====================================================
            # 🚀 SIGNAL GEN MATRIX (SCANS ONLY TOP 10 MOMENTUM STOCKS)
            # =====================================================
            with shared_mem.lock:
                has_users = len(shared_mem.users_db) > 0
                processing_state = shared_mem.is_processing
            
            if has_users and not processing_state:
                active_syms = []
                with shared_mem.lock:
                    for sym in dynamic_top_10: # 🌟 ONLY THE 10 MOST VOLATILE STOCKS 🌟
                        if shared_mem.symbol_switches.get(sym, True): active_syms.append(sym)

                for sym in active_syms:
                    with shared_mem.lock:
                        valid_users = [u for u, data in shared_mem.users_db.items() if data.get('api_key') and data.get('active', True)]
                    if not valid_users: continue

                    time.sleep(0.3) 
                    df_15m = fetch_candles_df(sym, "15m", limit=100)
                    time.sleep(0.3) 
                    df_5m = fetch_candles_df(sym, "5m", limit=100)
                    time.sleep(0.3) 
                    df_1m = fetch_candles_df(sym, "1m", limit=100)
                    
                    if df_15m is None or df_5m is None or df_1m is None or df_1m.empty: continue
                    
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
                    
                    rsi_15, rsi_5, rsi_1, rsi_1_prev = df_15m["RSI"].iloc[-2], df_5m["RSI"].iloc[-2], df_1m["RSI"].iloc[-2], df_1m["RSI"].iloc[-3]
                    close_1m = df_1m["close"].iloc[-2]
                    c_time = df_1m["time"].iloc[-2]
                    
                    lowest_15 = df_1m["low"].rolling(15).min().iloc[-2]
                    highest_15 = df_1m["high"].rolling(15).max().iloc[-2]
                    
                    with shared_mem.lock:
                        already_ordered = sym in shared_mem.ordered_candles and shared_mem.ordered_candles[sym] == c_time
                    if already_ordered: continue
                    
                    s_key, side = "", ""
                    with shared_mem.lock: strat_switches = shared_mem.strategy_switches.copy()
                    
                    if strat_switches.get("5-STAR LONG", True) and rsi_15 >= 60 and rsi_5 >= 60 and rsi_1 > 40 and rsi_1 > rsi_1_prev and (43 >= rsi_1_prev >= 20):
                        s_key, side = "5-STAR LONG", "buy"
                    elif strat_switches.get("5-STAR BB BUY", True) and rsi_15 > 60 and rsi_5 > 60 and rsi_1_prev < 61 and rsi_1 >= 60 and close_1m > df_1m["BB_up"].iloc[-2]:
                        s_key, side = "5-STAR BB BUY", "buy"
                    elif strat_switches.get("5-STAR SHORT", True) and rsi_15 <= 40 and rsi_5 <= 40 and rsi_1 < 60 and rsi_1 < rsi_1_prev and (80 >= rsi_1_prev >= 57):
                        s_key, side = "5-STAR SHORT", "sell"
                    elif strat_switches.get("5-STAR BB SELL", True) and rsi_15 < 40 and rsi_5 < 40 and rsi_1_prev > 39 and rsi_1 <= 40 and close_1m < df_1m["BB_low"].iloc[-2]:
                        s_key, side = "5-STAR BB SELL", "sell"
                    elif strat_switches.get("2-STAR BUY", True) and rsi_1 > 60 and rsi_1_prev <= 60 and close_1m > df_1m["BB_up"].iloc[-2]:
                        s_key, side = "2-STAR BUY", "buy"
                    elif strat_switches.get("2-STAR SELL", True) and rsi_1 < 40 and rsi_1_prev >= 40 and close_1m < df_1m["BB_low"].iloc[-2]:
                        s_key, side = "2-STAR SELL", "sell"
                        
                    if s_key != "":
                        if s_key == "5-STAR LONG": raw_entry = float(df_1m["high"].iloc[-2]); raw_sl = float(lowest_15) 
                        elif s_key == "5-STAR SHORT": raw_entry = float(df_1m["low"].iloc[-2]); raw_sl = float(highest_15) 
                        else:
                            raw_entry = float(df_1m["high"].iloc[-2]) if side == "buy" else float(df_1m["low"].iloc[-2])
                            raw_sl = float(df_1m["low"].iloc[-2]) if side == "buy" else float(df_1m["high"].iloc[-2])
                        
                        entry, sl = round_to_tick(raw_entry), round_to_tick(raw_sl)
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
                                target_mesh[i] = round_to_tick(raw_target)

                            any_order_placed = False

                            for user, u_db in current_users_snapshot.items():
                                if not u_db.get("active", True): continue
                                user_sym_sw = u_db.get("symbol_switches", {})
                                user_strat_sw = u_db.get("strategy_switches", {})
                                if not user_sym_sw.get(sym, True) or not user_strat_sw.get(s_key, True): continue 

                                with shared_mem.lock:
                                    user_active_trades = shared_mem.active_trades.get(sym, {}).get(user, [])
                                    user_running_strats = [t.get('strategy') for t in user_active_trades]
                                    is_user_active = len(user_running_strats) > 0

                                user_can_trade = False
                                if is_user_active:
                                    if s_key == "5-STAR BB BUY" and "5-STAR LONG" in user_running_strats and "5-STAR BB BUY" not in user_running_strats: user_can_trade = True
                                    elif s_key == "5-STAR BB SELL" and "5-STAR SHORT" in user_running_strats and "5-STAR BB SELL" not in user_running_strats: user_can_trade = True
                                    else: user_can_trade = False
                                else: user_can_trade = True 

                                if not user_can_trade: continue 

                                if u_db.get("risk_mode", False):
                                    usd_risk = u_db.get("risk_value", 1000.0) 
                                    u_qty = max(1, int(usd_risk / risk))
                                else: u_qty = int(u_db.get("btc_qty", 10)) 

                                order_status = place_breakout_entry_order(sym, u_qty, side, entry, u_db['api_key'], u_db['api_secret'])
                                
                                if order_status["success"]:
                                    any_order_placed = True
                                    add_log(f"Setup [{s_key}] registered at ₹{entry} for {sym} | Qty: {u_qty} [{user}]", type_icon="⏳")
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
                                    if "MARGIN" in fail_reason.upper(): add_log(f"ORDER REJECTED for {user} on {sym}! Reason: INSUFFICIENT MARGIN.", type_icon="❌")

                            if any_order_placed:
                                with shared_mem.lock:
                                    shared_mem.last_triggered_setup_info[sym] = {
                                        "entry": f"₹{entry:,.2f} (PENDING)", "sl": f"₹{sl:,.2f} (PENDING)", "t1": f"₹{target_mesh[1]:,.2f}", "t2": f"₹{target_mesh[2]:,.2f}", "status": f"⏳ {s_key} ({side.upper()}) DETECTED", "live_pnl": 0.0
                                    }
            with shared_mem.lock: shared_mem.is_processing = False
            time.sleep(5) 
        except Exception: time.sleep(5)

# ✅ GHOST THREAD FIX
if not hasattr(st, "_global_thread_started"):
    threading.Thread(target=core_execution_engine, args=(mem,), daemon=True).start()
    st._global_thread_started = True

# =====================================================
# CALLBACK STATE CONTROL BUTTONS
# =====================================================
def trigger_stop_action():
    mem.global_engine_running = False
    add_log("Algorithmic System SCANNER Completely Stopped.", type_icon="🔴")

def trigger_start_action():
    mem.global_engine_running = True
    add_log("Algorithmic System RUNNER Activated.", type_icon="🟢")

# =====================================================
# RENDER LAYOUT
# =====================================================
st.markdown(f"""
<div class="quantum-header-box">
    <div class="header-main-title">⚡ QUANTUM MULTI-USER MATRIX (FYERS ACTIVE)</div>
    <div class="header-sub-ip">Whitelisting Server IP: <span class="ip-glow">{SERVER_IP}</span></div>
</div>
""", unsafe_allow_html=True)

@st.fragment(run_every=4) 
def render_live_widgets():
    with mem.lock:
        active_syms = [s for s in TOP_50_STOCKS if s in mem.active_trades and mem.active_trades[s]]
        if not active_syms: display_syms = TOP_50_STOCKS[:4]
        else: display_syms = active_syms[:4] 

    cols = st.columns(min(len(display_syms), 4))
    for idx, sym in enumerate(display_syms):
        with cols[idx]:
            with mem.lock:
                info = mem.last_triggered_setup_info[sym].copy()
                sw_val = mem.symbol_switches.get(sym, True)
                live_ltp = mem.ticker_feeds[sym]["ltp"]
                r_1m = mem.ticker_feeds[sym]["rsi_1m"]
                r_5m = mem.ticker_feeds[sym]["rsi_5m"]
                r_15m = mem.ticker_feeds[sym]["rsi_15m"]
                
            ticker_title = f"{sym.split(':')[1]} Live" if sw_val else f"{sym.split(':')[1]} (DISABLED)"
            st.markdown(f"""
            <div class="ticker-widget-card">
                <div><span class="ticker-dot-orange">●</span><span class="ticker-token-title">{ticker_title}</span></div>
                <div class="ticker-price-green">₹{live_ltp:,.2f}</div>
                <div class="rsi-grid-row">
                    <span class="rsi-tab-item-1m">{r_1m:.2f}</span>
                    <span class="rsi-tab-item-5m">{r_5m:.2f}</span>
                    <span class="rsi-tab-item-15m">{r_15m:.2f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            pnl_val = info.get("live_pnl", 0.0)
            pnl_class = "pnl-green" if pnl_val > 0 else ("pnl-red" if pnl_val < 0 else "pnl-gray")
            
            cls_entry = "signal-value-active" if info['entry'] != "-" else "signal-value-waiting"
            cls_sl = "signal-value-active" if info['sl'] != "-" else "signal-value-waiting"
            cls_t1 = "signal-value-active" if info['t1'] != "-" else "signal-value-waiting"
            cls_t2 = "signal-value-active" if info['t2'] != "-" else "signal-value-waiting"

            st.markdown(f"""
            <div class="pnl-analytics-card">
                <div style="font-size: 10px; color: #ffff00; font-weight: bold; margin-bottom: 2px;">Setup P&L:</div>
                <div class="live-pnl-text {pnl_class}">+₹{pnl_val:,.2f}</div>
            </div>
            <div class="signal-data-box">
                <div style="font-size: 9px; color: #ef4444; font-weight: bold; margin-bottom: 6px;">🔴 {info['status'] if sw_val else 'SYMBOL SWITCH OFF'}</div>
                <div class="signal-grid">
                    <div><span class="signal-metric">ENTRY:</span> <span class="{cls_entry}">{info['entry']}</span></div>
                    <div><span class="signal-metric">SL:</span> <span class="{cls_sl}">{info['sl']}</span></div>
                    <div><span class="signal-metric">T1:</span> <span class="{cls_t1}">{info['t1']}</span></div>
                    <div><span class="signal-metric">T2:</span> <span class="{cls_t2}">{info['t2']}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

render_live_widgets()

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

with mem.lock: current_users_db = mem.users_db.copy()

for u_name, u_data in list(current_users_db.items()):
    if not is_owner and str(current_usr).strip().lower() != str(u_name).strip().lower(): continue
        
    col_r1, col_r2, col_r3, col_r4, col_r5, col_r6, col_r7 = st.columns([1.5, 2, 2, 1.2, 1.2, 1.5, 1.2])
    with col_r1: st.markdown(f"<span style='color:#38bdf8; font-size:13px;'>{u_name}</span>", unsafe_allow_html=True)
    with col_r2: 
        status_txt = "🔵 SCANNING MESH" if u_data.get("active", True) else "⚪ UNAPPROVED (PAUSED)"
        st.markdown(f"<span style='color:#ffff00; font-size:12px;'>{status_txt}</span>", unsafe_allow_html=True)
    with col_r3: 
        if u_data.get("risk_mode", False): st.markdown(f"<span style='color:#00ff00; font-size:12px;'>AUTO RISK (₹{u_data.get('risk_value', 1000.0):.0f})</span>", unsafe_allow_html=True)
        else: st.markdown(f"<span style='color:#ffff00; font-size:12px;'>Base Qty: {u_data.get('btc_qty', 10)}</span>", unsafe_allow_html=True)
    with col_r4: st.markdown("<span style='color:#ffff00; font-size:12px;'>₹0.00</span>", unsafe_allow_html=True)
    with col_r5: st.markdown("<span style='color:#10b981; font-size:12px;'>₹0.00</span>", unsafe_allow_html=True)
    
    with col_r6:
        if is_owner:
            is_approved = st.checkbox("APPROVED", value=u_data.get("active", True), key=f"chk_active_{u_name}")
            if is_approved != u_data.get("active", True):
                with mem.lock: mem.users_db[u_name]["active"] = is_approved
                if u_name in all_u:
                    all_u[u_name]["active"] = is_approved
                    save_users(all_u)
                add_log(f"User {u_name} status updated to {'APPROVED' if is_approved else 'UNAPPROVED'}")
                st.rerun()
        else:
            status_color = "#00ff00" if u_data.get("active", True) else "#ef4444"
            status_text = "APPROVED" if u_data.get("active", True) else "PAUSED"
            st.markdown(f"<span style='color:{status_color}; font-size:12px; font-weight:bold;'>{status_text}</span>", unsafe_allow_html=True)
            
    with col_r7:
        if is_owner:
            if st.button("❌", key=f"btn_rm_{u_name}", use_container_width=True):
                existing_users = load_users()
                if u_name in existing_users:
                    del existing_users[u_name]
                    save_users(existing_users)
                with mem.lock:
                    if u_name in mem.users_db: del mem.users_db[u_name]
                add_log(f"Client {u_name} disconnected from terminal mesh.", type_icon="🛑")
                st.rerun()
        else: st.markdown("<span style='color:#555555; font-size:12px;'>🔒 Lck</span>", unsafe_allow_html=True)
            
    st.markdown("<hr style='border:1px solid #1e3a8a; opacity:0.3; margin-top:5px; margin-bottom:5px;'/>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# 🎛️ GLOBAL MASTER SWITCHES SECTION
# =====================================================
col_body_sw1, col_body_sw2 = st.columns(2)
with col_body_sw1:
    st.markdown('<div class="panel-heading">🎛️ ENGINE GLOBAL MASTER OVERRIDES</div>', unsafe_allow_html=True)
    engine_status_label = "ACTIVE (RUNNING)" if mem.global_engine_running else "DEACTIVATED (PAUSED)"
    st.markdown(f"### STATUS: <span style='color:#00ff00;'>{engine_status_label}</span>", unsafe_allow_html=True)
    if mem.global_engine_running: st.button("🔴 STOP SCANNER SYSTEM", on_click=trigger_stop_action, use_container_width=True)
    else: st.button("🟢 START SCANNER SYSTEM", on_click=trigger_start_action, use_container_width=True)
        
    st.markdown("<hr style='border:1px dashed #1e3a8a; margin: 12px 0;'/>", unsafe_allow_html=True)
    st.markdown("<span style='color:#38bdf8; font-size:12px; font-weight:bold; text-transform:uppercase;'>MASTER SYMBOL OVERRIDE (BATCH):</span>", unsafe_allow_html=True)
    
    c_all1, c_all2 = st.columns([0.1, 0.9])
    with c_all1: all_val = st.checkbox("ALL_SYM", value=True, key="chk_all_sym", label_visibility="collapsed")
    with c_all2:
        st.markdown('<span class="neon-blue-lbl" style="line-height: 1.8;">TOGGLE TOP 50 STOCKS (NIFTY 50)</span>', unsafe_allow_html=True)
        if all_val != mem.symbol_switches.get(TOP_50_STOCKS[0]):
            for sym in TOP_50_STOCKS: mem.symbol_switches[sym] = all_val

    st.markdown("<span style='color:#ef4444; font-size:11px;'>🚨 EMERGENCY OPERATIONS CONTROLLER:</span>", unsafe_allow_html=True)
    if st.button("💥 GLOBAL KILL SWITCH (SQUARE OFF ALL)", use_container_width=True):
        with mem.lock: current_users_snap = mem.users_db.copy()
        for sym in TOP_50_STOCKS:
            for usr, u_db in current_users_snap.items():
                cancel_all_orders_for_symbol(sym, u_db['api_key'], u_db['api_secret'])
                close_position_market(sym, u_db['api_key'], u_db['api_secret'])
        with mem.lock: mem.active_trades.clear()
        add_log("EMERGENCY SQUARED OFF TRIGGERED!", type_icon="💥")
        st.rerun()

with col_body_sw2:
    st.markdown('<div class="panel-heading">⚙️ MASTER STRATEGY PIPELINE SWITCHES</div>', unsafe_allow_html=True)
    
    c2b1, c2b2 = st.columns([0.1, 0.9])
    with c2b1: mem.strategy_switches["2-STAR BUY"] = st.checkbox("2B", value=mem.strategy_switches.get("2-STAR BUY", True), key="chk_2_buy", label_visibility="collapsed")
    with c2b2: st.markdown('<span class="neon-green-lbl" style="line-height: 2.0;">1. BUY BREAKOUT</span>', unsafe_allow_html=True)

    c2s1, c2s2 = st.columns([0.1, 0.9])
    with c2s1: mem.strategy_switches["2-STAR SELL"] = st.checkbox("2S", value=mem.strategy_switches.get("2-STAR SELL", True), key="chk_2_sell", label_visibility="collapsed")
    with c2s2: st.markdown('<span class="neon-red-lbl" style="line-height: 2.0;">2. SELL BREAKOUT</span>', unsafe_allow_html=True)

    cl1, cl2 = st.columns([0.1, 0.9])
    with cl1: mem.strategy_switches["5-STAR LONG"] = st.checkbox("5L", value=mem.strategy_switches.get("5-STAR LONG", True), key="chk_5_long", label_visibility="collapsed")
    with cl2: st.markdown('<span class="neon-green-lbl" style="line-height: 2.0;">3. 5-STAR LONG</span>', unsafe_allow_html=True)
        
    cs1, cs2 = st.columns([0.1, 0.9])
    with cs1: mem.strategy_switches["5-STAR SHORT"] = st.checkbox("5S", value=mem.strategy_switches.get("5-STAR SHORT", True), key="chk_5_short", label_visibility="collapsed")
    with cs2: st.markdown('<span class="neon-red-lbl" style="line-height: 2.0;">4. 5-STAR SHORT</span>', unsafe_allow_html=True)
        
    cb1, cb2 = st.columns([0.1, 0.9])
    with cb1: mem.strategy_switches["5-STAR BB BUY"] = st.checkbox("5BB", value=mem.strategy_switches.get("5-STAR BB BUY", True), key="chk_bb_buy", label_visibility="collapsed")
    with cb2: st.markdown('<span class="neon-green-lbl" style="line-height: 2.0;">5. 5-STAR BB BUY BREAKOUT</span>', unsafe_allow_html=True)
        
    cx1, cx2 = st.columns([0.1, 0.9])
    with cx1: mem.strategy_switches["5-STAR BB SELL"] = st.checkbox("5BBS", value=mem.strategy_switches.get("5-STAR BB SELL", True), key="chk_bb_sell", label_visibility="collapsed")
    with cx2: st.markdown('<span class="neon-red-lbl" style="line-height: 2.0;">6. 5-STAR BB SELL BREAKOUT</span>', unsafe_allow_html=True)

# BOTTOM NAVIGATION TAB CONTROLLER
tab_logs, tab_rms, tab_registration = st.tabs(["📊 LIVE DIAGNOSTICS LOGS", "🛡️ RISK CONTROLLER (RMS)", "👥 CLIENT REGISTRATION MATRIX"])

with tab_logs:
    st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">📊 LIVE TERMINAL DIAGNOSTIC REPORT</div>', unsafe_allow_html=True)
    
    @st.fragment(run_every=5) 
    def render_live_logs():
        with mem.lock: logs_html = "".join(mem.last_terminal_logs)
        st.markdown(f'<div class="diagnostic-logger-container">{logs_html}</div>', unsafe_allow_html=True)
        
    render_live_logs()
    st.markdown('</div>', unsafe_allow_html=True)

with tab_rms:
    st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">🛡️ RISK MANAGEMENT SYSTEM (RMS) CONTROLLER</div>', unsafe_allow_html=True)
    
    with mem.lock: current_users_rms = mem.users_db.copy()
        
    if not current_users_rms: st.info("No active clients found. Please register clients first.")
    else:
        for u_name, u_data in list(current_users_rms.items()):
            if not is_owner and str(current_usr).strip().lower() != str(u_name).strip().lower(): continue
                
            st.markdown(f"<span style='color:#38bdf8; font-size:14px; font-weight:bold; border-bottom: 1px solid #1e3a8a; display:block; padding-bottom:4px;'>👤 Client Configuration Profile: {u_name}</span>", unsafe_allow_html=True)
            
            with st.container():
                st.markdown("<span style='color:#ffff00; font-size:11px; font-weight:bold;'>🔐 UPDATE FYERS API KEYS (AppID / Token):</span>", unsafe_allow_html=True)
                ak_col, as_col = st.columns(2)
                with ak_col: new_ak = st.text_input("Fyers App ID (Client ID)", value=u_data.get("api_key", ""), type="password", key=f"up_ak_{u_name}")
                with as_col: new_as = st.text_input("Fyers Access Token", value=u_data.get("api_secret", ""), type="password", key=f"up_as_{u_name}")
                
                u_strat = u_data.get("strategy_switches", {})
                
                st.markdown("<span style='color:#38bdf8; font-size:11px; font-weight:bold;'>⚙️ PERSONAL PIPELINE STRATEGY SELECTION:</span>", unsafe_allow_html=True)
                ps_c1, ps_c2, ps_c3 = st.columns(3)
                with ps_c1:
                    p_2b = st.checkbox("1. 2-STAR BUY", value=u_strat.get("2-STAR BUY", True), key=f"pstr_2b_{u_name}")
                    p_2s = st.checkbox("2. 2-STAR SELL", value=u_strat.get("2-STAR SELL", True), key=f"pstr_2s_{u_name}")
                with ps_c2:
                    p_5l = st.checkbox("3. 5-STAR LONG", value=u_strat.get("5-STAR LONG", True), key=f"pstr_5l_{u_name}")
                    p_5s = st.checkbox("4. 5-STAR SHORT", value=u_strat.get("5-STAR SHORT", True), key=f"pstr_5s_{u_name}")
                with ps_c3:
                    p_5bb = st.checkbox("5. 5-STAR BB BUY", value=u_strat.get("5-STAR BB BUY", True), key=f"pstr_5bb_{u_name}")
                    p_5bs = st.checkbox("6. 5-STAR BB SELL", value=u_strat.get("5-STAR BB SELL", True), key=f"pstr_5bs_{u_name}")

                st.markdown("<span style='color:#ffff00; font-size:11px; font-weight:bold;'>📊 QUANTUM LOT & RISK PROFILES:</span>", unsafe_allow_html=True)
                rc1, rc2, rc3 = st.columns([1, 1, 2])
                with rc1: risk_mode = st.checkbox("AUTO RISK QTY", value=u_data.get("risk_mode", False), key=f"rmode_{u_name}")
                with rc2: risk_val = st.number_input("Max Risk (₹ INR)", value=float(u_data.get("risk_value", 1000.0)), key=f"rval_{u_name}", step=100.0)
                with rc3: btc_q = st.number_input("Equity Default Qty", min_value=1, value=int(u_data.get("btc_qty", 10)), key=f"rbtc_{u_name}")
                
                if st.button(f"💾 SAVE CONFIG & MATRICES FOR {u_name}", key=f"save_rms_{u_name}", use_container_width=True):
                    new_strat_dict = {
                        "2-STAR BUY": p_2b, "2-STAR SELL": p_2s,
                        "5-STAR LONG": p_5l, "5-STAR SHORT": p_5s, 
                        "5-STAR BB BUY": p_5bb, "5-STAR BB SELL": p_5bs
                    }
                    
                    with mem.lock:
                        mem.users_db[u_name]["api_key"] = new_ak
                        mem.users_db[u_name]["api_secret"] = new_as
                        mem.users_db[u_name]["strategy_switches"] = new_strat_dict
                        mem.users_db[u_name]["risk_mode"] = risk_mode
                        mem.users_db[u_name]["risk_value"] = risk_val
                        mem.users_db[u_name]["btc_qty"] = btc_q 
                    
                    existing_users = load_users()
                    if u_name in existing_users:
                        existing_users[u_name]["api_key"] = new_ak
                        existing_users[u_name]["api_secret"] = new_as
                        existing_users[u_name]["strategy_switches"] = new_strat_dict
                        existing_users[u_name]["risk_mode"] = risk_mode
                        existing_users[u_name]["risk_value"] = risk_val
                        existing_users[u_name]["btc_qty"] = btc_q
                        save_users(existing_users)
                    
                    add_log(f"Personalized Matrix saved successfully for {u_name}.", type_icon="🛡️")
                    st.success(f"Config Successfully Saved for {u_name}!")
                    time.sleep(0.5)
                    st.rerun()
            st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab_registration:
    st.markdown('<div class="grid-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-heading">👥 REGISTER NEW CLIENT GATEWAY</div>', unsafe_allow_html=True)
    with st.form("Client Registration Bottom Tab Form"):
        reg_username = st.text_input("Client ID / Username")
        reg_password = st.text_input("Terminal Trading Password", type="password")
        reg_key = st.text_input("Fyers App ID (Client ID)", type="password")
        reg_secret = st.text_input("Fyers Access Token", type="password")
        submit_registration = st.form_submit_button("🔒 REGISTER CLIENT SECURELY")
        if submit_registration:
            if not reg_username or not reg_password or not reg_key or not reg_secret: st.error("❌ Sabhi fields fill up karna anivarye hain!")
            else:
                default_strats = {"2-STAR BUY": True, "2-STAR SELL": True, "5-STAR LONG": True, "5-STAR SHORT": True, "5-STAR BB BUY": True, "5-STAR BB SELL": True}
                existing_users = load_users()
                existing_users[reg_username] = {
                    "password": reg_password, "api_key": reg_key, "api_secret": reg_secret, 
                    "btc_qty": 10, "risk_mode": False, "risk_value": 1000.0, "active": True,
                    "symbol_switches": {s: True for s in TOP_50_STOCKS}, "strategy_switches": default_strats
                }
                save_users(existing_users)
                with mem.lock: mem.users_db[reg_username] = existing_users[reg_username]
                add_log(f"New client deployment for {reg_username} verified on Fyers.", type_icon="👤")
                st.success(f"🎉 User added successfully!")
                time.sleep(1)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"Current Active User: `{current_usr} (Direct Admin Access)`")
