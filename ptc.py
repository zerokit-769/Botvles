import os
import sys
import asyncio
import glob
import urllib.parse
import aiohttp
import shutil
from telethon import TelegramClient
from telethon.tl.functions.messages import RequestWebViewRequest

API_ID = 39013074  
API_HASH = "f855b33fdd2797a6c8d1fa621b195011"
BOT_USERNAME = "pitbullcoinbot"
URL_WEBVIEW = "https://pitcoin.onrender.com"
REF_CODE = "6651107551"

INIT_DATA_CACHE = {}

class C:
    RES = '\033[0m'
    CYA = '\033[96m'
    GRE = '\033[92m'
    YEL = '\033[93m'
    RED = '\033[91m'
    MAG = '\033[95m'
    WHT = '\033[97m'
    BLD = '\033[1m'

def clr():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_term_width():
    cols = shutil.get_terminal_size((50, 20)).columns
    return min(cols, 65)

def print_banner():
    clr()
    w = get_term_width()
    print(f"{C.CYA}{C.BLD}┌{'─' * (w-2)}┐{C.RES}")
    print(f"{C.CYA}{C.BLD}│{C.WHT} P I T B U L L   A U T O M A T I O N {C.CYA}".center(w + 10) + f"{C.BLD}│{C.RES}")
    print(f"{C.CYA}{C.BLD}│{C.MAG} BY SYNDICATEBOT NET {C.CYA}".center(w + 10) + f"{C.BLD}│{C.RES}")
    print(f"{C.CYA}{C.BLD}├{'─' * (w-2)}┤{C.RES}")
    print(f"{C.CYA}{C.BLD}│ {C.WHT}SYSTEM : {C.GRE}ACTIVE PROTOCOL{C.CYA}".ljust(w + 10) + f"│{C.RES}")
    print(f"{C.CYA}{C.BLD}│ {C.WHT}TARGET : {C.GRE}PITBULL MINI APP{C.CYA}".ljust(w + 10) + f"│{C.RES}")
    print(f"{C.CYA}{C.BLD}└{'─' * (w-2)}┘{C.RES}\n")

async def extract_init_data(session_name):
    client = TelegramClient(session_name, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print(f"{C.RED}[{session_name}] ❌ SESSION UNAUTHORIZED.{C.RES}")
        await client.disconnect()
        return None

    try:
        bot_entity = await client.get_input_entity(BOT_USERNAME)
        result = await client(RequestWebViewRequest(
            peer=bot_entity,
            bot=bot_entity,
            platform='android',
            from_bot_menu=False,
            url=URL_WEBVIEW
        ))
        raw_init_data = result.url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]
        init_data = urllib.parse.unquote(raw_init_data)
        await client.disconnect()
        return init_data
    except Exception as e:
        print(f"{C.RED}[{session_name}] ❌ EXTRACTION ERROR: {e}{C.RES}")
        await client.disconnect()
        return None

async def execute_api_pipeline(session_name, init_data):
    headers = {
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Not=A?Brand";v="99", "Android WebView";v="151", "Chromium";v="151"',
        'sec-ch-ua-mobile': "?1",
        'x-telegram-init-data': init_data,
        'x-requested-with': "org.telegram.messenger.web",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://pitcoin.onrender.com/?tgWebAppStartParam=1757455348",
        'accept-language': "en,id-ID;q=0.9,id;q=0.8,en-US;q=0.7",
        'priority': "u=1, i"
    }

    async with aiohttp.ClientSession() as session:
        url_user = "https://pitcoin.onrender.com/api/user"
        try:
            async with session.get(url_user, headers=headers) as resp:
                data_user = await resp.json()
                if not data_user.get("success"):
                    return False
                username = data_user.get("user", {}).get("username", "Unknown")
                print(f"{C.CYA}[{session_name}]{C.RES} {C.WHT}Username :{C.RES} {C.GRE}{username}{C.RES}")
        except Exception:
            return False

        url_ref = "https://pitcoin.onrender.com/api/user/referral"
        payload_ref = {"referrerCode": "8973220376"}
        try:
            async with session.post(url_ref, headers=headers, json=payload_ref) as resp:
                data_ref = await resp.json()
                msg = data_ref.get("message", "Processed")
               # print(f"{C.CYA}[{session_name}]{C.RES} {C.WHT}Message :{C.RES} {C.MAG}{msg}{C.RES}")
        except Exception as e:
            print(f"{C.CYA}[{session_name}]{C.RES} {C.RED}Referral Error: {e}{C.RES}")

        url_claim = "https://pitcoin.onrender.com/api/mine/claim"
        try:
            async with session.post(url_claim, headers=headers) as resp:
                data_claim = await resp.json()
                if data_claim.get("success"):
                    claimed = data_claim.get("claimedAmount", 0)
                    balance = data_claim.get("newBalance", 0)
                    print(f"{C.CYA}[{session_name}]{C.RES} {C.WHT}Claim :{C.RES} {C.GRE}{claimed}{C.RES}")
                    print(f"{C.CYA}[{session_name}]{C.RES} {C.WHT}Balance :{C.RES} {C.YEL}{balance}{C.RES}")
                else:
                    print(f"{C.CYA}[{session_name}]{C.RES} {C.YEL}Claim Failed or Not Ready{C.RES}")
        except Exception as e:
            print(f"{C.CYA}[{session_name}]{C.RES} {C.RED}Claim Error: {e}{C.RES}")

        url_boost = "https://pitcoin.onrender.com/api/boost/overclock"
        try:
            async with session.post(url_boost, headers=headers) as resp:
                data_boost = await resp.json()
                is_success = data_boost.get("success") or data_boost.get("succes")
                if is_success:
                    print(f"{C.CYA}[{session_name}]{C.RES} {C.WHT}Boost With Ads :{C.RES} {C.GRE}success{C.RES}")
                else:
                    print(f"{C.CYA}[{session_name}]{C.RES} {C.WHT}Boost With Ads :{C.RES} {C.RED}Failed{C.RES}")
        except Exception as e:
            print(f"{C.CYA}[{session_name}]{C.RES} {C.RED}Boost Error: {e}{C.RES}")

        return True

async def process_account(session_name):
    init_data = INIT_DATA_CACHE.get(session_name)
    
    if not init_data:
        init_data = await extract_init_data(session_name)
        if init_data:
            INIT_DATA_CACHE[session_name] = init_data
        else:
            return

    success = await execute_api_pipeline(session_name, init_data)
    
    if not success:
        print(f"{C.CYA}[{session_name}]{C.RES} {C.YEL}InitData Expired. Re-extracting...{C.RES}")
        init_data = await extract_init_data(session_name)
        if init_data:
            INIT_DATA_CACHE[session_name] = init_data
            await execute_api_pipeline(session_name, init_data)
        else:
            print(f"{C.CYA}[{session_name}]{C.RES} {C.RED}Re-extraction Failed.{C.RES}")

async def main():
    while True:
        print_banner()
        sessions = glob.glob("*.session")
        
        if not sessions:
            print(f"{C.RED} ❌ NO SESSION FILES DETECTED IN DIRECTORY.{C.RES}")
            return
        
        print(f"{C.CYA} 🚀 EXECUTING AUTOMATION FOR {C.WHT}{len(sessions)}{C.CYA} NODES...{C.RES}\n")

        tasks = []
        for session_file in sessions:
            session_name = session_file.replace(".session", "")
            tasks.append(process_account(session_name))
            
        await asyncio.gather(*tasks)
        
        print(f"\n{C.GRE} ✅ CYCLE COMPLETED FOR ALL NODES.{C.RES}\n")

        total_seconds = 601
        for remaining in range(total_seconds, 0, -1):
            mins, secs = divmod(remaining, 60)
            timer_str = f"{mins:02d} : {secs:02d}"
            sys.stdout.write(f"\r{C.YEL} ⏳ Wait For {timer_str} To Claim and Boost Again{C.RES}")
            sys.stdout.flush()
            await asyncio.sleep(1)
        
        sys.stdout.write("\r" + " " * 65 + "\r")
        sys.stdout.flush()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{C.RED} ⛔ OVERRIDE DETECTED: TERMINATED BY USER.{C.RES}")
