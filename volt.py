import requests
import json
import random
import time
import os
import shutil
import string
from concurrent.futures import ThreadPoolExecutor, as_completed

C = "\033[1;36m"
G = "\033[1;32m"
Y = "\033[1;33m"
R = "\033[1;31m"
M = "\033[1;35m"
W = "\033[1;37m"
RES = "\033[0m"

def clr():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_width():
    cols = shutil.get_terminal_size((50, 20)).columns
    return max(45, min(cols, 60))

def banner():
    clr()
    w = get_width()
    line = "═" * (w - 2)
    print(f"\033[38;5;51m╔{line}╗\033[0m")
    title = "⚡ VOLT MULTI-WORKER AUTO REFERRAL ⚡"
    pad1 = max(0, (w - 4 - len(title)) // 2)
    pad2 = max(0, (w - 4 - len(title)) - pad1)
    print(f"\033[38;5;51m║\033[0m " + " " * pad1 + f"\033[1;38;5;220m{title}\033[0m" + " " * pad2 + f" \033[38;5;51m║\033[0m")
    sub = "✨ SyndicateBot Net • Ecosystem v2.4 ✨"
    spad1 = max(0, (w - 4 - len(sub)) // 2)
    spad2 = max(0, (w - 4 - len(sub)) - spad1)
    print(f"\033[38;5;51m║\033[0m " + " " * spad1 + f"\033[38;5;201m{sub}\033[0m" + " " * spad2 + f" \033[38;5;51m║\033[0m")
    print(f"\033[38;5;51m╚{line}╝\033[0m")
    print(f"\033[38;5;51m" + "─" * w + "\033[0m")

def generate_random_user():
    first_names = [
        "Alex", "John", "Sarah", "Michael", "Emma", "David", "James", "Maria", "Leon", "Nina",
        "Budi", "Siti", "Andi", "Rina", "Kevin", "Diana", "Daniel", "Sophia", "William", "Olivia",
        "Robert", "Emily", "Thomas", "Ava", "Christopher", "Mia", "Matthew", "Isabella", "Anthony", "Amelia",
        "Joshua", "Harper", "Andrew", "Evelyn", "Joseph", "Abigail", "Samuel", "Ella", "Benjamin", "Elizabeth",
        "Lucas", "Sofia", "Henry", "Grace", "Alexander", "Chloe", "Nicholas", "Victoria", "Ethan", "Lily",
        "Jacob", "Hannah", "Logan", "Luna", "Jackson", "Zoe", "Sebastian", "Penelope", "Jack", "Layla",
        "Aiden", "Mila", "Owen", "Camila", "Daniel", "Aria", "Matthew", "Scarlett", "Wyatt", "Eleanor",
        "Carter", "Riley", "Julian", "Nora", "Grayson", "Hazel", "Leo", "Aurora", "Jayden", "Ellie",
        "Gabriel", "Violet", "Isaac", "Alice", "Lincoln", "Willow", "Anthony", "Lillian", "Dylan", "Paisley",
        "Ezra", "Addison", "Thomas", "Natalie", "Charles", "Emilia", "Caleb", "Naomi", "Ryan", "Elena",
        "Nathan", "Maya", "Adrian", "Stella", "Christian", "Isla", "Maverick", "Everleigh", "Elias", "Ivy",
        "Aaron", "Liliana", "Eli", "Samantha", "Connor", "Ruby", "Cameron", "Eva", "Miles", "Serenity",
        "Dominic", "Claire", "Jaxon", "Skylar", "Micah", "Lucy", "Ryder", "Paisley", "Asher", "Madison",
        "Cooper", "Bella", "Colton", "Aaliyah", "Jordan", "Kennedy", "Ian", "Kinsley", "Adam", "Savannah",
        "Carson", "Allison", "Xavier", "Hailey", "Easton", "Autumn", "Jace", "Nevaeh", "Nolan", "Valentina",
        "Adrian", "Genesis", "Miles", "Emery", "Jason", "Caroline", "Nathaniel", "Nova", "Kai", "Gabriella",
        "Ryan", "Arianna", "Leo", "Madelyn", "Evan", "Piper", "Isaiah", "Julia", "Landon", "Delilah",
        "Oliver", "Serena", "Max", "Celine", "Felix", "Bianca", "Oscar", "Clara", "Hugo", "Eva",
        "Bima", "Dimas", "Fajar", "Rizky", "Rafi", "Raka", "Reza", "Arif", "Bayu", "Yoga",
        "Agus", "Doni", "Eko", "Fikri", "Hendra", "Ilham", "Iqbal", "Joko", "Rian", "Rizal",
        "Taufik", "Wahyu", "Yusuf", "Zaki", "Aldi", "Alvin", "Bagas", "Daffa", "Farhan", "Galih",
        "Hafiz", "Imam", "Jefri", "Kurniawan", "Lutfi", "Miko", "Nanda", "Oki", "Rangga", "Sandi",
        "Satria", "Surya", "Vino", "Yuda", "Ayu", "Dewi", "Fitri", "Indah", "Lia", "Maya",
        "Nadia", "Putri", "Sari", "Wulan", "Anisa", "Citra", "Dinda", "Fani", "Intan", "Lestari",
        "Mila", "Nabila", "Nia", "Nurul", "Rani", "Ratna", "Rika", "Riska", "Shinta", "Tania",
        "Tiara", "Vina", "Yuni", "Zahra", "Aisyah", "Amelia", "Anita", "Bella", "Celine", "Della",
        "Dian", "Elsa", "Erika", "Fira", "Gita", "Hana", "Hilda", "Ika", "Jasmine", "Karina",
        "Laura", "Lina", "Melisa", "Monica", "Natasya", "Olivia", "Rachel", "Regina", "Selena", "Tania"
    ]

    last_names = [
        "Smith", "Doe", "Johnson", "Brown", "Taylor", "Miller", "Wilson", "Moore", "Wijaya", "Putra",
        "Pratama", "Wong", "Lim", "Hartono", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin",
        "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez", "Lewis", "Lee", "Walker", "Hall",
        "Allen", "Young", "Hernandez", "King", "Wright", "Lopez", "Hill", "Scott", "Green", "Adams",
        "Baker", "Nelson", "Carter", "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker",
        "Evans", "Edwards", "Collins", "Stewart", "Sanchez", "Morris", "Rogers", "Reed", "Cook", "Morgan",
        "Bell", "Murphy", "Bailey", "Rivera", "Cooper", "Richardson", "Cox", "Howard", "Ward", "Torres",
        "Peterson", "Gray", "Ramirez", "James", "Watson", "Brooks", "Kelly", "Sanders", "Price", "Bennett",
        "Wood", "Barnes", "Ross", "Henderson", "Coleman", "Jenkins", "Perry", "Powell", "Long", "Patterson",
        "Hughes", "Flores", "Washington", "Butler", "Simmons", "Foster", "Gonzalez", "Bryant", "Alexander", "Russell",
        "Griffin", "Diaz", "Hayes", "Myers", "Ford", "Hamilton", "Graham", "Sullivan", "Wallace", "Woods",
        "Cole", "West", "Jordan", "Owens", "Reynolds", "Fisher", "Ellis", "Harrison", "Gibson", "Mcdonald",
        "Cruz", "Marshall", "Ortiz", "Gomez", "Murray", "Freeman", "Wells", "Webb", "Simpson", "Stevens",
        "Tucker", "Porter", "Hunter", "Hicks", "Crawford", "Henry", "Boyd", "Mason", "Morales", "Kennedy",
        "Warren", "Dixon", "Ramos", "Reyes", "Burns", "Gordon", "Shaw", "Holmes", "Rice", "Robertson",
        "Hunt", "Black", "Daniels", "Palmer", "Mills", "Nichols", "Grant", "Knight", "Ferguson", "Rose",
        "Stone", "Hawkins", "Dunn", "Perkins", "Hudson", "Spencer", "Gardner", "Stephens", "Payne", "Pierce",
        "Berry", "Matthews", "Arnold", "Wagner", "Willis", "Ray", "Watkins", "Olson", "Carroll", "Duncan",
        "Snyder", "Hart", "Cunningham", "Bradley", "Lane", "Carpenter", "Weaver", "Greene", "Lawrence", "Elliott",
        "Chavez", "Sims", "Austin", "Peters", "Kelley", "Franklin", "Lawson", "Fields", "Gutierrez", "Ryan",
        "Schmidt", "Carr", "Vasquez", "Castillo", "Wheeler", "Chapman", "Oliver", "Montgomery", "Richards", "Williamson",
        "Johnston", "Banks", "Meyer", "Bishop", "Mccoy", "Howell", "Alvarez", "Morrison", "Hansen", "Fernandez",
        "Garza", "Harvey", "Little", "Burton", "Stanley", "Nguyen", "George", "Jacobs", "Reid", "Kim",
        "Fuller", "Lynch", "Dean", "Gilbert", "Garrett", "Romero", "Welch", "Larson", "Frazier", "Burke",
        "Wijaya", "Santoso", "Setiawan", "Kurniawan", "Saputra", "Hidayat", "Nugroho", "Wibowo", "Susanto", "Siregar",
        "Simanjuntak", "Manurung", "Sinaga", "Panjaitan", "Hutapea", "Sihombing", "Situmorang", "Nainggolan", "Saragih", "Lubis",
        "Hasibuan", "Nasution", "Harahap", "Tampubolon", "Pardede", "Gultom", "Purba", "Samosir", "Sembiring", "Tarigan",
        "Pranoto", "Wahyudi", "Firmansyah", "Ramadhan", "Maulana", "Permana", "Hakim", "Fauzi", "Akbar", "Maulana",
        "Gunawan", "Irawan", "Susilo", "Setiawan", "Hermawan", "Suharto", "Sutanto", "Purnomo", "Cahyono", "Kusuma"
    ]
    fn = random.choice(first_names)
    ln = f"{random.choice(last_names)}{random.randint(0, 99):02d}"

    uname = f"{fn.lower()}{ln.lower()}{random.randint(100, 99999)}"
    tid = random.randint(1000000000, 9999999999)

    return tid, fn, ln, uname

def get_random_ip():
    return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

def execute_worker(idx, url, ref_id):
    tid, fn, ln, uname = generate_random_user()
    rand_ip = get_random_ip()
    
    payload = {
        "telegramUser": {
            "id": tid,
            "first_name": fn,
            "last_name": ln,
            "username": uname,
            "language_code": "en",
            "allows_write_to_pm": True,
            "photo_url": ""
        },
        "referredBy": ref_id,
        "walletAddress": ""
    }
    
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.7922.170 Mobile Safari/537.36 Telegram-Android/12.9.2 (Samsung SM-A217F; Android 12; SDK 31; LOW)",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Not=A?Brand";v="99", "Android WebView";v="151", "Chromium";v="151"',
        'sec-ch-ua-mobile': "?1",
        'origin': "https://volt.crowntasks.xyz",
        'x-requested-with': "org.telegram.messenger.web",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://volt.crowntasks.xyz/",
        'accept-language': "en,id-ID;q=0.9,id;q=0.8,en-US;q=0.7",
        'priority': "u=1, i",
        'X-Forwarded-For': rand_ip
    }
    
    result_lines = []
    result_lines.append(f" \033[38;5;51m│\033[0m \033[1;38;5;220m[{idx}/100]\033[0m \033[38;5;201mWorker Executing...\033[0m")
    result_lines.append(f" \033[38;5;51m│\033[0m \033[38;5;45m├─ ID       :\033[0m \033[1;97m{tid}\033[0m")
    result_lines.append(f" \033[38;5;51m│\033[0m \033[38;5;45m├─ Name     :\033[0m \033[1;97m{fn} {ln}\033[0m")
    result_lines.append(f" \033[38;5;51m│\033[0m \033[38;5;45m├─ IP Spoof :\033[0m \033[38;5;220m{rand_ip}\033[0m")
    
    try:
        res = requests.post(url, data=json.dumps(payload), headers=headers, timeout=15)
        
        if res.status_code in [200, 201]:
            data = res.json()
            if data.get("success"):
                user_data = data.get("user", {})
                balance = user_data.get("inAppBalance", 0)
                result_lines.append(f" \033[38;5;51m│\033[0m \033[38;5;45m└─ Status   :\033[0m \033[1;38;5;46mSUCCESS\033[0m | Balance: \033[1;38;5;46m{balance}\033[0m")
            else:
                result_lines.append(f" \033[38;5;51m│\033[0m \033[38;5;45m└─ Status   :\033[0m \033[1;38;5;196mFAILED\033[0m | Res: {res.text}")
        else:
            result_lines.append(f" \033[38;5;51m│\033[0m \033[38;5;45m└─ Status   :\033[0m \033[1;38;5;196mHTTP {res.status_code}\033[0m")
            
    except Exception as e:
        result_lines.append(f" \033[38;5;51m│\033[0m \033[38;5;45m└─ Error    :\033[0m \033[1;38;5;196m{e}\033[0m")
        
    result_lines.append(f" \033[38;5;51m│\033[0m")
    return "\n".join(result_lines)

def main():
    banner()
    url = "https://volt.crowntasks.xyz/api/user/sync"
    ref_id = input(
        " \033[38;5;51m│\033[0m "
        "\033[1;38;5;220m▶ Enter Ref ID ( Only Number ) : \033[0m"
    ).strip()
    
    total_accounts = int(input(
    " \033[38;5;51m│\033[0m "
    "\033[1;38;5;220m▶ Enter Total Reff You need ( Only Number ) : \033[0m"
).strip())
    batch_size = 10
    
    for batch_start in range(1, total_accounts + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, total_accounts)
        print(f" \033[38;5;51m│\033[0m \033[1;38;5;220m▶ STARTING BATCH: {batch_start} to {batch_end}\033[0m")
        print(f" \033[38;5;51m│\033[0m")

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = {executor.submit(execute_worker, idx, url, ref_id): idx for idx in range(batch_start, batch_end + 1)}
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    print(result)
                except Exception as e:
                    print(f" \033[38;5;51m│\033[0m \033[1;38;5;196mWorker Exception: {e}\033[0m\n \033[38;5;51m│\033[0m")

        if batch_end < total_accounts:
            print(f"\033[38;5;51m" + "─" * get_width() + "\033[0m")
            for s in range(60, 0, -1):
                print(f"\r \033[38;5;51m│\033[0m \033[38;5;208m⏳ Batch {batch_start}-{batch_end} Finished! Sleeping {s}s to prevent FloodLimit...\033[0m\033[K", end="", flush=True)
                time.sleep(1)
            print("\r\033[K", end="")
            print(f"\033[38;5;51m" + "─" * get_width() + "\033[0m")

    print(f"\033[38;5;51m" + "─" * get_width() + "\033[0m")
    print(f" \033[1;38;5;46m[✔] {total_accounts} Iterations Completed.\033[0m")
    print(f"\033[38;5;51m" + "─" * get_width() + "\033[0m\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\033[1;38;5;196m[!] Automation session forcefully terminated.\033[0m")
