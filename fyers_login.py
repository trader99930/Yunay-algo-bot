import json
import requests
import pyotp
from urllib import parse
import sys
import hashlib

# Bot ke database module ko import kar rahe hain 
from auth import load_users, save_users

# Client Info (ENTER YOUR OWN INFO HERE)
FY_ID = "FS3309"
APP_ID_TYPE = "2"
TOTP_KEY = "5OGDFE2GODRIBA5C7RBI5BNQV4HTQ3JS" 
PIN = "0099" 
APP_ID = "R2CNABKH5F" 
REDIRECT_URI = "https://trade.fyers.in/api-login/redirect-uri/index.html" 
APP_TYPE = "100" 
APP_SECRET = "LTL2NXG9CE" 

a_string = f"{APP_ID}-{APP_TYPE}:{APP_SECRET}"
APP_ID_HASH = hashlib.sha256(a_string.encode("utf-8")).hexdigest()

# API endpoints
BASE_URL = "https://api-t2.fyers.in/vagator/v2"
BASE_URL_2 = "https://api-t1.fyers.in/api/v3"
URL_SEND_LOGIN_OTP = BASE_URL + "/send_login_otp"
URL_VERIFY_TOTP = BASE_URL + "/verify_otp"
URL_VERIFY_PIN = BASE_URL + "/verify_pin"
URL_TOKEN = BASE_URL_2 + "/token"
URL_VALIDATE_AUTH_CODE = BASE_URL_2 + "/validate-authcode"

SUCCESS = 1
ERROR = -1

def send_login_otp(fy_id, app_id):
    try:
        payload = {"fy_id": fy_id, "app_id": app_id}
        result_string = requests.post(url=URL_SEND_LOGIN_OTP, json=payload)
        if result_string.status_code != 200: return [ERROR, result_string.text]
        return [SUCCESS, json.loads(result_string.text)["request_key"]]
    except Exception as e: return [ERROR, str(e)]

def generate_totp(secret):
    try: return [SUCCESS, pyotp.TOTP(secret).now()]
    except Exception as e: return [ERROR, str(e)]

def verify_totp(request_key, totp):
    try:
        payload = {"request_key": request_key, "otp": totp}
        result_string = requests.post(url=URL_VERIFY_TOTP, json=payload)
        if result_string.status_code != 200: return [ERROR, result_string.text]
        return [SUCCESS, json.loads(result_string.text)["request_key"]]
    except Exception as e: return [ERROR, str(e)]

def verify_PIN(request_key, pin):
    try:
        payload = {"request_key": request_key, "identity_type": "pin", "identifier": pin}
        result_string = requests.post(url=URL_VERIFY_PIN, json=payload)
        if result_string.status_code != 200: return [ERROR, result_string.text]
        return [SUCCESS, json.loads(result_string.text)["data"]["access_token"]]
    except Exception as e: return [ERROR, str(e)]

def token(fy_id, app_id, redirect_uri, app_type, access_token):
    try:
        payload = {
            "fyers_id": fy_id, "app_id": app_id, "redirect_uri": redirect_uri, "appType": app_type,
            "code_challenge": "", "state": "sample_state", "scope": "", "nonce": "",
            "response_type": "code", "create_cookie": True,
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        result_string = requests.post(url=URL_TOKEN, json=payload, headers=headers)
        if result_string.status_code != 308: return [ERROR, result_string.text]
        url = json.loads(result_string.text)["Url"]
        return [SUCCESS, parse.parse_qs(parse.urlparse(url).query)["auth_code"][0]]
    except Exception as e: return [ERROR, str(e)]

def validate_authcode(app_id_hash, auth_code):
    try:
        payload = {"grant_type": "authorization_code", "appIdHash": app_id_hash, "code": auth_code}
        result_string = requests.post(url=URL_VALIDATE_AUTH_CODE, json=payload)
        if result_string.status_code != 200: return [ERROR, result_string.text]
        return [SUCCESS, json.loads(result_string.text)["access_token"]]
    except Exception as e: return [ERROR, str(e)]

def main():
    print("🔄 Starting Fyers Auto-Login Process...")
    
    send_otp_result = send_login_otp(fy_id=FY_ID, app_id=APP_ID_TYPE)
    if send_otp_result[0] != SUCCESS: sys.exit(f"❌ send_login_otp failure: {send_otp_result[1]}")
    
    generate_totp_result = generate_totp(secret=TOTP_KEY)
    if generate_totp_result[0] != SUCCESS: sys.exit(f"❌ generate_totp failure: {generate_totp_result[1]}")

    verify_totp_result = verify_totp(request_key=send_otp_result[1], totp=generate_totp_result[1])
    if verify_totp_result[0] != SUCCESS: sys.exit(f"❌ verify_totp failure: {verify_totp_result[1]}")

    verify_pin_result = verify_PIN(request_key=verify_totp_result[1], pin=PIN)
    if verify_pin_result[0] != SUCCESS: sys.exit(f"❌ verify_PIN failure: {verify_pin_result[1]}")

    token_result = token(FY_ID, APP_ID, REDIRECT_URI, APP_TYPE, verify_pin_result[1])
    if token_result[0] != SUCCESS: sys.exit(f"❌ token_result failure: {token_result[1]}")

    validate_authcode_result = validate_authcode(APP_ID_HASH, token_result[1])
    if validate_authcode_result[0] != SUCCESS: sys.exit(f"❌ validate_authcode failure: {validate_authcode_result[1]}")

    # Success: Got the tokens!
    appid1 = f"{APP_ID}-{APP_TYPE}"
    token1 = validate_authcode_result[1]
    print(f"✅ Token Generated Successfully!")

    # 🚀 CONNECTION TO BOT.PY (MAGIC HAPPENS HERE) 🚀
    print("\n🔗 Injecting Token into bot's Database (users_database.json)...")
    try:
        users_db = load_users()
        
        # ✅ YAHAN TARGET USER YUNAY KAR DIYA HAI
        TARGET_USER = "Yunay" 
        
        if TARGET_USER not in users_db:
            print(f"⚠️ User '{TARGET_USER}' not found. Initializing profile...")
            users_db[TARGET_USER] = {
                "password": "admin", 
                "btc_qty": 10, "eth_qty": 10, 
                "risk_mode": False, "risk_value": 1000.0, 
                "active": True, 
                "symbol_switches": {}, "strategy_switches": {}
            }

        # Injection step
        users_db[TARGET_USER]["api_key"] = appid1
        users_db[TARGET_USER]["api_secret"] = token1
        users_db[TARGET_USER]["active"] = True  # Automatically approve the user

        # Save to users_database.json
        save_users(users_db)
        print(f"🎉 SUCCESS! Token safely injected for user: {TARGET_USER}")
        print("▶️ You can now run your bot using: streamlit run bot.py")
        
    except Exception as e:
        print(f"❌ Database Injection Failed: {e}")

if __name__ == "__main__":
    main()
