import streamlit as st
import json
import os

USER_FILE = "users.json" # Ya jo bhi aapki file ka naam ho

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def auth_page():
    # Injecting colorful professional neon styles for Auth
    st.markdown("""
        <style>
        .auth-container {
            background: linear-gradient(135deg, #0b132b 0%, #060913 100%);
            border: 2px solid #38bdf8;
            box-shadow: 0px 0px 20px rgba(56, 189, 248, 0.5);
            padding: 30px;
            border-radius: 12px;
            margin-top: 50px;
        }
        .auth-header {
            color: #00ff00;
            font-family: monospace;
            text-align: center;
            font-size: 24px;
            text-shadow: 0px 0px 8px rgba(0, 255, 0, 0.6);
            margin-bottom: 20px;
        }
        .auth-label {
            color: #ffff00 !important;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    users = load_users()

    # Initialize auth state if not present
    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "SIGN-IN"

    # ------------------ MODE 1: SIGN UP (REGISTRATION) ------------------
    if st.session_state["auth_mode"] == "SIGN-UP":
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown('<div class="auth-header">🛸 NEW CLIENT MATRIX SIGN-UP</div>', unsafe_allow_html=True)
        
        with st.form("signup_form"):
            new_user = st.text_input("Create Master Username")
            new_pass = st.text_input("Create Account Password", type="password")
            api_k = st.text_input("Delta India API Key (Optional during signup)", type="password")
            api_s = st.text_input("Delta India API Secret (Optional during signup)", type="password")
            
            signup_submit = st.form_submit_button("🔥 INITIATE SYSTEM SIGN-UP")
            
            if signup_submit:
                if not new_user or not new_pass:
                    st.error("Username aur Password fields mandatory hain!")
                elif new_user in users:
                    st.error("Yeh username pehle se registered hai!")
                else:
                    users[new_user] = {
                        "password": new_pass,
                        "api_key": api_k,
                        "api_secret": api_s,
                        "btc_qty": 4,
                        "eth_qty": 4
                    }
                    save_users(users)
                    st.success("Sign-up successful! Chaliye ab Sign-in karte hain.")
                    st.session_state["auth_mode"] = "SIGN-IN"
                    st.rerun()
                    
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("👉 Pehle se account hai? SIGN-IN KAREIN", use_container_width=True):
            st.session_state["auth_mode"] = "SIGN-IN"
            st.rerun()

    # ------------------ MODE 2: SIGN IN (LOGIN) ------------------
    elif st.session_state["auth_mode"] == "SIGN-IN":
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown('<div class="auth-header">🔐 ACCESS TERMINAL: SIGN-IN</div>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            login_user = st.text_input("Enter Registered Username")
            login_pass = st.text_input("Enter Password", type="password")
            
            login_submit = st.form_submit_button("🔓 UNLOCK QUANTUM DASHBOARD")
            
            if login_submit:
                if login_user in users and users[login_user]["password"] == login_pass:
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = login_user
                    st.success("Access Granted! Terminal loading...")
                    st.rerun()
                else:
                    st.error("Invalid Username ya Password! Kripya dubara check karein.")
                    
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ Naya account banana hai? SIGN-UP KAREIN", use_container_width=True):
            st.session_state["auth_mode"] = "SIGN-UP"
            st.rerun()
            
    return st.session_state.get("logged_in", False)


