import streamlit as st
import json
import os
import time

USER_DB_FILE = "users_database.json"

def load_users():
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_users(users):
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f, indent=4)

def auth_page():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = None
    if "auth_active_tab" not in st.session_state:
        st.session_state["auth_active_tab"] = 0  # 0 = Sign In, 1 = Sign Up

    if st.session_state["logged_in"]:
        return True

    st.markdown("<h2 style='text-align: center; color: #f59e0b;'>🔒 QUANTUM TERMINAL ACCESS CONTROL</h2>", unsafe_allow_html=True)
    
    # Active tab state synchronization
    active_tab = st.radio("NAVIGATION GATEWAY", ["🔐 SIGN IN (OLD USER)", "📝 SIGN UP (NEW USER)"], 
                          index=st.session_state["auth_active_tab"], horizontal=True, label_visibility="collapsed")
    
    users = load_users()

    if active_tab == "🔐 SIGN IN (OLD USER)":
        st.session_state["auth_active_tab"] = 0
        st.markdown("<h4 style='color: #38bdf8; margin-top:15px;'>Login to Secure Matrix</h4>", unsafe_allow_html=True)
        login_user = st.text_input("Username / Account Name", key="login_user_input")
        login_pass = st.text_input("Password", type="password", key="login_pass_input")
        
        if st.button("PROCEED TO TERMINAL", use_container_width=True):
            if login_user in users and users[login_user]["password"] == login_pass:
                st.session_state["logged_in"] = True
                st.session_state["current_user"] = login_user
                
                if "mem_instance" in st.session_state and users[login_user].get("api_key"):
                    mem = st.session_state["mem_instance"]
                    mem.users_db[login_user] = {
                        "api_key": users[login_user]["api_key"],
                        "api_secret": users[login_user]["api_secret"],
                        "btc_qty": users[login_user].get("btc_qty", 4),
                        "eth_qty": users[login_user].get("eth_qty", 4),
                        "active": True
                    }
                st.success(f"Welcome back, {login_user}! Loading dashboard...")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Invalid Username or Password")

    elif active_tab == "📝 SIGN UP (NEW USER)":
        st.session_state["auth_active_tab"] = 1
        st.markdown("<h4 style='color: #10b981; margin-top:15px;'>Create New Account</h4>", unsafe_allow_html=True)
        new_user = st.text_input("Choose Username", key="reg_user_input")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pass_input")
        
        if st.button("CREATE ACCOUNT", use_container_width=True):
            if not new_user or not new_pass:
                st.error("❌ Username aur Password bharna zaroori hai!")
            elif new_user in users:
                st.error("❌ Ye username pehle se exist karta hai.")
            else:
                users[new_user] = {
                    "password": new_pass,
                    "api_key": "",        
                    "api_secret": "",     
                    "btc_qty": 4,
                    "eth_qty": 4
                }
                save_users(users)
                st.toast("✅ Account successfully created! Redirecting to Sign In...", icon="🎯")
                st.session_state["auth_active_tab"] = 0  # Dynamic redirect trigger to Sign In
                time.sleep(0.5)
                st.rerun()
                
    return False
