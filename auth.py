import streamlit as st
import json
import os
import time  # 👈 Yeh import hona zaroori hai

# User data ko save karne ke liye file path
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
    # Session state variables ko initialize karna
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = None

    # Agar user pehle se logged in hai to kuch nahi dikhana, seedhe app chalegi
    if st.session_state["logged_in"]:
        return True

    st.markdown("<h2 style='text-align: center; color: #f59e0b;'>🔒 QUANTUM TERMINAL ACCESS CONTROL</h2>", unsafe_allow_html=True)
    
    # Login aur Sign Up ke liye tabs
    tab1, tab2 = st.tabs(["🔐 SIGN IN (LOGIN)", "📝 SIGN UP (REGISTER)"])
    
    users = load_users()

    with tab1:
        st.markdown("<h4 style='color: #38bdf8;'>Login to Secure Matrix</h4>", unsafe_allow_html=True)
        login_user = st.text_input("Username / Account Name", key="login_user_input")
        login_pass = st.text_input("Password", type="password", key="login_pass_input")
        
        if st.button("PROCEED TO TERMINAL", use_container_width=True):
            if login_user in users and users[login_user]["password"] == login_pass:
                st.session_state["logged_in"] = True
                st.session_state["current_user"] = login_user
                
                # Agar user ne pehle se API key save ki hai to session state me load karna
                if "mem_instance" in st.session_state and users[login_user]["api_key"]:
                    mem = st.session_state["mem_instance"]
                    mem.users_db[login_user] = {
                        "api_key": users[login_user]["api_key"],
                        "api_secret": users[login_user]["api_secret"],
                        "btc_qty": users[login_user].get("btc_qty", 4),
                        "eth_qty": users[login_user].get("eth_qty", 4),
                        "active": True
                    }
                st.success(f"Welcome back, {login_user}! Loading engine...")
                time.sleep(1)  # 👈 Yahan se 'st.' hata diya hai, ab ye sahi chalega
                st.rerun()
            else:
                st.error("❌ Invalid Username or Password")

    with tab2:
        st.markdown("<h4 style='color: #10b981;'>Create New Account</h4>", unsafe_allow_html=True)
        new_user = st.text_input("Choose Username", key="reg_user_input")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pass_input")
        
        st.markdown("<p style='font-size: 11px; color: #64748b;'>Optional: Aap trading credentials abhi ya baad me dashboard par bhi onboard kar sakte hain.</p>", unsafe_allow_html=True)
        reg_key = st.text_input("Delta Exchange API Key (Optional)", type="password", key="reg_key_input")
        reg_sec = st.text_input("Delta Exchange API Secret (Optional)", type="password", key="reg_sec_input")

        if st.button("CREATE ACCOUNT", use_container_width=True):
            if not new_user or not new_pass:
                st.error("❌ Username aur Password bharna zaroori hai!")
            elif new_user in users:
                st.error("❌ Ye username pehle se exist karta hai. Dusra select karein.")
            else:
                users[new_user] = {
                    "password": new_pass,
                    "api_key": reg_key,
                    "api_secret": reg_sec,
                    "btc_qty": 4,
                    "eth_qty": 4
                }
                save_users(users)
                st.success("✅ Account successfully created! Ab aap SIGN IN tab par jaakar login kar sakte hain.")
                
    return False
