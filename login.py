import os
import glob
import json
import time
import requests
import asyncio
import random
import hmac
import hashlib
from urllib.parse import unquote
from telethon import TelegramClient, functions

IP_FILE = "session_ips.json"

GERMAN_RANGES = [
    (85, 214),
    (88, 198),
    (91, 198),
    (178, 63),
    (2, 201),
]
async def create_sessions_if_not_exist():
    session_files = glob.glob("sess*.session")

    if session_files:
        print(f"✅ Found {len(session_files)} existing session(s)")
        return

    print("⚠️ No session found!")
    total = int(input("How Many Account You Want Use: "))

    for i in range(1, total + 1):
        session_name = f"sess{i}"
        print(f"\n🔐 Login {session_name}")

        client = TelegramClient(session_name, API_ID, API_HASH)
        await client.connect()

        phone = input("📱 Phone Number: ")

        try:
            await client.send_code_request(phone)
            code = input("🔑 OTP Code: ")

            try:
                await client.sign_in(phone, code)
            except Exception:
                # kemungkinan 2FA
                password = input("🔒 2FA Password (if any): ")
                await client.sign_in(password=password)

            print(f"✅ {session_name} saved!")

        except Exception as e:
            print("❌ Login failed:", e)

        await client.disconnect()
def generate_german_ip():
    a, b = random.choice(GERMAN_RANGES)
    c = random.randint(0, 255)
    d = random.randint(1, 254)
    return f"{a}.{b}.{c}.{d}"


def load_ips():
    if os.path.exists(IP_FILE):
        with open(IP_FILE, "r") as f:
            return json.load(f)
    return {}


def save_ips(data):
    with open(IP_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_session_ip(session_name):
    data = load_ips()

    if session_name not in data:
        data[session_name] = generate_german_ip()
        save_ips(data)

    return data[session_name]
def save_account(session_token, token):
    file = "farmss.json"

    new_data = {
        "SESSION": session_token,
        "TOKEN": token
    }

    data = []

    if os.path.exists(file):
        try:
            with open(file, "r") as f:
                data = json.load(f)
        except:
            data = []

    # 🔥 FIX DI SINI
    for acc in data:
        if acc.get("SESSION") == session_token:
            print(f"⚠️ {session_token} sudah ada → update")
            acc["TOKEN"] = token
            break
    else:
        data.append(new_data)

    with open(file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"💾 Saved: {session_token}")

API_ID = 28752231
API_HASH = 'ec1c1f2c30e2f1855c3edee7e348480b'
BOT_USER = 'FreeFarmOnlineBot'

SECRET_KEY = "c6e2f7c2b7c44e8c9e3f1a2d4e6f8a1b"


# ================== RANDOM UA ==================
def random_ua():
    android_versions = ["12", "13", "14", "15"]
    devices = [
    "SM-S921B", "SM-S918B", "SM-A546E", "SM-A346E", "SM-A146B",
    "Pixel 6", "Pixel 6a", "Pixel 7 Pro", "Pixel 8", "Pixel 8 Pro",
    "Redmi Note 11", "Redmi Note 10", "Redmi Note 13",
    "Mi 11", "Mi 10", "Xiaomi 13",
    "POCO F5", "POCO X5 Pro",
    "Realme 11 Pro", "Vivo V29"
]
    av = random.choice(android_versions)
    dv = random.choice(devices)

    return f"Mozilla/5.0 (Linux; Android {av}; {dv}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.7680.{random.randint(100,200)} Mobile Safari/537.36 Telegram-Android/12.{random.randint(1,5)}"


# ================== SIGNATURE ==================
def generate_signature(payload, token):
    timestamp = str(int(time.time() * 1000))

    payload_with_ts = payload.copy()
    payload_with_ts["timestamp"] = timestamp

    ordered = dict(sorted(payload_with_ts.items()))
    json_str = json.dumps(ordered, separators=(",", ":"), ensure_ascii=False)

    base = f"{timestamp}:{token}:{json_str}"

    sig = hmac.new(
        SECRET_KEY.encode(),
        base.encode(),
        hashlib.sha256
    ).hexdigest()

    return sig, timestamp


# ================== PROCESS ==================
async def process_accounts():
    session_files = glob.glob("sess*.session")

    for i, session_file in enumerate(session_files, start=1):
        session_name = session_file.replace('.session', '')
    
        client = TelegramClient(session_name, API_ID, API_HASH)
        await client.start()

        me = await client.get_me()
        phone = me.phone if me.phone else "Hidden"
        first_name = me.first_name or ""
        last_name = me.last_name or ""
        full_name = f"{first_name} {last_name}".strip()


        print(f"\n🚀 Account #{i}")
        print(f"Session : {session_name}")
        print(f"👤 Name : {full_name}")
        print(f"Phone   : {phone}")

        try:
            bot = await client.get_input_entity(BOT_USER)

            web_view = await client(functions.messages.RequestWebViewRequest(
                peer=bot,
                bot=bot,
                platform='android',
                from_bot_menu=False,
                url="https://freefarm.online/"
            ))

            raw = web_view.url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]
            INIT_DATA = unquote(raw)

        except Exception as e:
            print("❌ initData error:", e)
            await client.disconnect()
            continue

        # ================= AUTH (SIGNED) =================
        session_ip = get_session_ip(session_name)

        headers = {
            "User-Agent": random_ua(),
            "Content-Type": "application/json",
            "Origin": "https://freefarm.online",
            "Referer": "https://freefarm.online/",
            "X-Requested-With": "org.telegram.messenger",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8",
            "X-Forwarded-For": session_ip
        }

        payload_auth = {
            "initData": INIT_DATA
        }

        # 🔥 SIGN AUTH (token kosong)
        sig, ts = generate_signature(payload_auth, "")

        payload_auth["timestamp"] = ts
        payload_auth["signature"] = sig

        res = requests.post(
            "https://freefarm.online/api/auth",
            json=payload_auth,
            headers=headers
        )

        print("AUTH RESP:", res.text)

        if res.status_code != 200:
            print("❌ auth gagal")
            await client.disconnect()
            continue

        data = res.json()
        token = data.get("token")

        if not token:
            print("❌ token kosong")
            await client.disconnect()
            continue

        print("✅ TOKEN:", token)

        # ================= CREATE SESSION =================
        payload = {
            "turnstile_token": "",
            "action": "create_session"
        }

        sig, ts = generate_signature(payload, token)

        payload["timestamp"] = ts
        payload["signature"] = sig

        headers["authorization"] = f"Bearer {token}"

        res2 = requests.post(
            "https://freefarm.online/api/session/create",
            json=payload,
            headers=headers
        )

        print("CREATE RESP:", res2.text)

        if res2.status_code == 200:
            js = res2.json()
            session_token = js.get("session_token")
            print("✅ TOKEN:", token)

            save_account(session_token, token)

        await client.disconnect()
        time.sleep(random.uniform(2, 2))


# ================= RUN =================
async def main():
    os.system("clear")
    await create_sessions_if_not_exist()
    os.system("clear")
    await process_accounts()

asyncio.run(main())