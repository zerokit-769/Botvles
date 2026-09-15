import requests
import time
import sys
import os
import json
import uuid

PROGRESS_FILE = "selesai.json"

class C:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner(account_info=None):
    clear_screen()
    print(f"{C.MAGENTA}{C.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}          🎬  D R A M A   W A T C H   E P I S O D E        {C.RESET}")
    print(f"{C.BLUE}{C.BOLD}                   By ZeinthHub Project                      {C.RESET}")
    if account_info:
        print(f"{C.YELLOW}{C.BOLD}   👤 Account : {account_info}{C.RESET}")
    print(f"{C.MAGENTA}{C.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}\n")

def cool_loading(text, duration=1.2):
    frames = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        sys.stdout.write(f"\r{C.CYAN}{C.BOLD} {frames[i % len(frames)]} {text} {C.RESET}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write("\r" + " " * 70 + "\r")

def countdown_timer(seconds=60):
    for remaining in range(seconds, 0, -1):
        sys.stdout.write(f"\r{C.YELLOW}{C.BOLD} ⏳ [DELAY] Waiting {remaining} seconds before next episode... {C.RESET}")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " " * 75 + "\r")

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_progress(progress_data):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress_data, f, indent=2)

def main():
    show_banner()
    
    user_cookie = input(f"{C.WHITE}{C.BOLD}Enter Your Cookie : {C.RESET}")
    
    show_banner()
    cool_loading("Syncing account...", 2.5)
    
    clear_screen()
    show_banner()
    print(f"{C.GREEN}{C.BOLD}✅ Connected! Starting logic...{C.RESET}\n")
    time.sleep(1)
    
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 12; SM-A217F Build/SP1A.210812.016) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.7977.87 Mobile Safari/537.36",
        'sec-ch-ua-platform': "\"Android\"",
        'sec-ch-ua': "\"Chromium\";v=\"152\", \"Not?A_Brand\";v=\"24\", \"Android WebView\";v=\"152\"",
        'sec-ch-ua-mobile': "?1",
        'x-requested-with': "qzbr.zpr.pt",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'accept-language': "en-US,en;q=0.9",
        'priority': "u=1, i",
        'Cookie': user_cookie
    }
    
    device_id = str(uuid.uuid4())
    
    cool_loading("Checking Account Authentication...", 1.5)
    
    auth_url = "https://drama.center/api/auth/me"
    try:
        auth_res = requests.get(auth_url, headers=headers)
        auth_json = auth_res.json()
        
        if not auth_json.get("success"):
            print(f"{C.RED}{C.BOLD}❌ Authentication Failed! Check your Cookie.{C.RESET}")
            return
            
        user_info = auth_json.get("user", {})
        account_id = user_info.get("id")
        email = user_info.get("email")
        wallet = user_info.get("wallet_address")
        
        account_type = email if email else (wallet if wallet else account_id)
        
    except Exception as e:
        print(f"{C.RED}{C.BOLD}❌ Authentication Error: {e}{C.RESET}")
        return

    show_banner(account_type)
    print(f"{C.GREEN}{C.BOLD}✅ Authentication Successful!{C.RESET}")
    print(f"{C.WHITE}   🆔 Account ID : {account_id}{C.RESET}")
    print(f"{C.WHITE}   📱 Device ID  : {device_id}{C.RESET}\n")

    all_progress = load_progress()
    if account_id not in all_progress:
        all_progress[account_id] = {}

    account_progress = all_progress[account_id]

    cool_loading("Fetching drama list from server...", 2)
    try:
        dramas_api_url = "https://drama.center/api/dramas?sort=popular&limit=1000&language=en"
        res = requests.get(dramas_api_url, headers=headers)
        dramas_data = res.json().get('data', [])
        
        if not dramas_data:
            print(f"{C.RED}{C.BOLD}❌ Failed to fetch drama list or data is empty!{C.RESET}")
            return

    except Exception as e:
        print(f"{C.RED}{C.BOLD}❌ Failed to connect to Drama API: {e}{C.RESET}")
        return

    try:
        for d_idx, drama in enumerate(dramas_data, start=1):
            drama_id = drama['id']
            drama_title = drama.get('title', 'Unknown Title')
            
            show_banner(account_type)
            print(f"{C.GREEN}{C.BOLD}✅ Found total {len(dramas_data)} Dramas!{C.RESET}\n")
            
            if drama_id in account_progress and account_progress[drama_id].get('completed'):
                print(f"{C.BLUE}{C.BOLD}⏩ Skipping Drama [{d_idx}/{len(dramas_data)}]: {drama_title} (Already Completed){C.RESET}")
                time.sleep(1)
                continue

            print(f"\n{C.CYAN}{C.BOLD}🎬 [{d_idx}/{len(dramas_data)}] PROCESSING DRAMA: {drama_title}{C.RESET}")
            print(f"{C.WHITE}   🆔 Drama ID: {drama_id}{C.RESET}")

            episodes_url = f"https://drama.center/api/dramas/{drama_id}"
            ep_res = requests.get(episodes_url, headers=headers)
            drama_detail = ep_res.json().get('data', {})
            episodes = drama_detail.get('episodes', [])

            if not episodes:
                print(f"{C.YELLOW}   ⚠️ No episodes found for this drama.{C.RESET}")
                time.sleep(1)
                continue

            total_episodes = len(episodes)
            last_saved_ep = account_progress.get(drama_id, {}).get('last_episode', 0)

            for ep_idx in range(last_saved_ep, total_episodes):
                ep = episodes[ep_idx]
                ep_id = ep['id']
                ep_number = ep_idx + 1

                print(f"{C.MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}")
                print(f"{C.YELLOW}{C.BOLD}▶️  Processing Episode {ep_number} / {total_episodes}{C.RESET}")
                print(f"{C.WHITE}   🆔 Episode ID: {ep_id}{C.RESET}")

                tick_url = f"https://drama.center/api/dramas/{drama_id}/episodes/watch-tick"
                payload = {"episodeId": ep_id, "deviceId": device_id}
                
                tick_res = requests.post(tick_url, headers=headers, json=payload)
                tick_data = tick_res.json().get('data', {})

                credited = tick_data.get('credited', 0)
                reject_reason = tick_data.get('rejectReason')

                should_delay = False

                if credited > 0:
                    print(f"{C.GREEN}{C.BOLD}   ✅ Credited       : {credited} 💰{C.RESET}")
                    
                    collect_url = "https://drama.center/api/watch-reward/collect"
                    collect_res = requests.post(collect_url, headers=headers, json={})
                    collect_data = collect_res.json().get('data', {})

                    collected = collect_data.get('collected', 0)
                    total_today = collect_data.get('totalToday', 0)
                    personal_dmc = collect_data.get('personalDmc', 0)

                    print(f"{C.CYAN}{C.BOLD}   💎 Collected      : {collected}{C.RESET}")
                    print(f"{C.BLUE}{C.BOLD}   📈 Total Today    : {total_today}{C.RESET}")
                    print(f"{C.MAGENTA}{C.BOLD}   🏆 Personal DMC   : {personal_dmc}{C.RESET}")
                    
                    should_delay = True

                else:
                    print(f"{C.RED}{C.BOLD}   ❌ Reject Reason  : {reject_reason} ⚠️{C.RESET}")

                is_drama_completed = (ep_number == total_episodes)
                account_progress[drama_id] = {
                    "title": drama_title,
                    "last_episode": ep_number,
                    "total_episodes": total_episodes,
                    "completed": is_drama_completed
                }
                all_progress[account_id] = account_progress
                save_progress(all_progress)

                if reject_reason == "episode_maxed":
                    continue
                elif should_delay:
                    countdown_timer(60)

            print(f"\n{C.GREEN}{C.BOLD}🎉 Drama '{drama_title}' COMPLETED! Progress saved.{C.RESET}")
            time.sleep(2)

    except KeyboardInterrupt:
        print(f"\n\n{C.YELLOW}{C.BOLD}⚠️ Stopped by user (Ctrl+C). Progress has been saved to '{PROGRESS_FILE}'.{C.RESET}")
        sys.exit(0)

    print(f"\n{C.GREEN}{C.BOLD}🏆 CONGRATULATIONS! All Dramas and Episodes processed! 🏆{C.RESET}\n")

if __name__ == "__main__":
    main()
