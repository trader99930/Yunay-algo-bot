import streamlit as st
import json
import os

USER_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def auth_page():
    st.subheader("🔐 Terminal Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        users = load_users()
        if username in users and users[username].get("password") == password:
            st.session_state["logged_in"] = True
            st.session_state["current_user"] = username
            st.rerun()
        else:
            st.error("❌ Invalid Username or Password")
    return False
