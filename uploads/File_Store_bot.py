"""
╔══════════════════════════════════════════════════════════════════╗
║          PRO FILE STORE BOT — v5.2.0 PREMIUM ULTIMATE          ║
║          Channel Expiry | Auto Delete | Premium System          ║
╚══════════════════════════════════════════════════════════════════╝
"""

import telebot
import sqlite3
import time
import logging
import hashlib
import re
import threading
from telebot import types
from datetime import datetime
from functools import wraps
from collections import defaultdict

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
BOT_TOKEN = "8750619057:AAHoeFNNDMaRpfmHTkOQ49--qJ-9QYjOnSI"
SUPER_ADMIN_IDS = [7882074153]
OWNER_USERNAME = "ANXHERE777, TOYOTA03A"
FIXED_CHANNEL = "ANXHERE777_CHANNEL"
FIXED_GROUP = "ANXHERE777GC"
DB_FILE = "vk1.db"
LOG_FILE = "vk.log"
RATE_LIMIT_MSG = 10
RATE_LIMIT_WIN = 10
BOT_VERSION = "ANXHERE777 AARMY "

# ─────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  BOT INIT
# ─────────────────────────────────────────────
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ─────────────────────────────────────────────
#  HTML FORMATTING HELPERS
# ─────────────────────────────────────────────
def bold(t): return f"<b>{t}</b>"
def italic(t): return f"<i>{t}</i>"
def under(t): return f"<u>{t}</u>"
def code(t): return f"<code>{t}</code>"
def esc(t): return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ─────────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Files table
    c.execute("""CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT NOT NULL, file_id TEXT NOT NULL, type TEXT NOT NULL,
        caption TEXT DEFAULT '', label TEXT DEFAULT '',
        created INTEGER DEFAULT (strftime('%s','now')),
        expires INTEGER DEFAULT 0, hits INTEGER DEFAULT 0,
        max_hits INTEGER DEFAULT 0, is_premium INTEGER DEFAULT 0)""")

    c.execute("CREATE INDEX IF NOT EXISTS idx_files_key ON files(key)")

    # Extra channels table with expires_at column
    c.execute("""CREATE TABLE IF NOT EXISTS extra_channels (
        username TEXT PRIMARY KEY, button_name TEXT NOT NULL,
        custom_url TEXT DEFAULT '', added_by INTEGER,
        added_at INTEGER DEFAULT (strftime('%s','now')),
        expires_at INTEGER DEFAULT 0)""")

    # Users table
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        first_seen INTEGER DEFAULT (strftime('%s','now')),
        last_seen INTEGER DEFAULT (strftime('%s','now')),
        files_recv INTEGER DEFAULT 0, is_banned INTEGER DEFAULT 0,
        is_premium INTEGER DEFAULT 0, premium_expiry INTEGER DEFAULT 0,
        forward_count INTEGER DEFAULT 0, max_forward INTEGER DEFAULT 5)""")

    # Premium forwards table
    c.execute("""CREATE TABLE IF NOT EXISTS premium_forwards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user INTEGER, to_user INTEGER, file_key TEXT,
        forwarded_at INTEGER DEFAULT (strftime('%s','now')))""")

    # Stats table
    c.execute("""CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event TEXT, user_id INTEGER, detail TEXT,
        ts INTEGER DEFAULT (strftime('%s','now')))""")

    # Admins table
    c.execute("""CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY, username TEXT DEFAULT '',
        added_by INTEGER, added_at INTEGER DEFAULT (strftime('%s','now')))""")

    # Try to add expires_at column if it doesn't exist (for existing databases)
    try:
        c.execute("ALTER TABLE extra_channels ADD COLUMN expires_at INTEGER DEFAULT 0")
        log.info("Added expires_at column to extra_channels")
    except:
        pass

    conn.commit()
    conn.close()
    log.info("Premium Database initialised.")

init_db()

# ─────────────────────────────────────────────
#  CHANNEL EXPIRY HELPERS
# ─────────────────────────────────────────────
def parse_time_string(time_str):
    """Parse time string like 1d, 2h, 30m, 45s and return seconds"""
    time_str = time_str.lower().strip()
    
    if time_str.endswith('d'):
        return int(time_str[:-1]) * 24 * 3600
    elif time_str.endswith('h'):
        return int(time_str[:-1]) * 3600
    elif time_str.endswith('m'):
        return int(time_str[:-1]) * 60
    elif time_str.endswith('s'):
        return int(time_str[:-1])
    else:
        return 0

def format_time_duration(seconds):
    """Format seconds into readable string"""
    if seconds <= 0:
        return "Expired"
    
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 and days == 0:
        parts.append(f"{secs}s")
    
    return " ".join(parts) if parts else "0s"

def add_channel_with_expiry(username, button_name, added_by, custom_url="", duration_seconds=0):
    """Add channel with expiry time"""
    expires_at = int(time.time()) + duration_seconds if duration_seconds > 0 else 0
    conn = get_conn()
    conn.execute("""INSERT OR REPLACE INTO extra_channels 
                    (username, button_name, custom_url, added_by, added_at, expires_at) 
                    VALUES (?,?,?,?,strftime('%s','now'),?)""",
                 (username, button_name, custom_url, added_by, expires_at))
    conn.commit()
    conn.close()
    
    if expires_at > 0:
        # Schedule expiry check
        threading.Timer(duration_seconds, check_and_remove_expired_channel, args=[username]).start()
    
    return expires_at

def check_and_remove_expired_channel(username):
    """Check if channel expired and remove it"""
    try:
        conn = get_conn()
        row = conn.execute("SELECT expires_at FROM extra_channels WHERE username=?", (username,)).fetchone()
        if row:
            expires_at = row["expires_at"]
            if expires_at > 0 and time.time() >= expires_at:
                conn.execute("DELETE FROM extra_channels WHERE username=?", (username,))
                conn.commit()
                log.info(f"Channel {username} automatically removed due to expiry")
                
                # Notify admins
                admins = get_all_admin_ids()
                for admin_id in admins:
                    try:
                        bot.send_message(admin_id, 
                            f"⏰ <b>Channel Auto-Removed</b>\n\n"
                            f"🔗 Channel: <code>{username}</code>\n"
                            f"📅 Expired at: {datetime.fromtimestamp(expires_at).strftime('%d %b %Y %H:%M:%S')}\n\n"
                            f"<i>The channel has been automatically removed from force-subscribe list.</i>")
                    except:
                        pass
        conn.close()
    except Exception as e:
        log.error(f"Expiry check error for {username}: {e}")

def remove_channel(username):
    conn = get_conn()
    conn.execute("DELETE FROM extra_channels WHERE username=?", (username,))
    conn.commit()
    conn.close()

def get_channels():
    conn = get_conn()
    rows = conn.execute("SELECT username, button_name, custom_url, added_at, expires_at FROM extra_channels").fetchall()
    conn.close()
    return rows

def parse_channel_input(raw):
    raw = raw.strip()
    m = re.match(r"(?:https?://)?t\.me/(\+[\w-]+)", raw)
    if m:
        tok = m.group(1)
        return tok, f"https://t.me/{tok}"
    m = re.match(r"(?:https?://)?t\.me/([\w]+)", raw)
    if m:
        u = m.group(1)
        return u, f"https://t.me/{u}"
    u = raw.lstrip("@").strip()
    return u, f"https://t.me/{u}"

def check_expired_channels_background():
    """Background thread to check expired channels every minute"""
    while True:
        try:
            time.sleep(60)  # Check every minute
            conn = get_conn()
            now = int(time.time())
            expired = conn.execute("SELECT username FROM extra_channels WHERE expires_at > 0 AND expires_at <= ?", (now,)).fetchall()
            for row in expired:
                conn.execute("DELETE FROM extra_channels WHERE username=?", (row["username"],))
                log.info(f"Auto-removed expired channel: {row['username']}")
            conn.commit()
            conn.close()
        except Exception as e:
            log.error(f"Expiry check error: {e}")

# Start background expiry checker
def start_expiry_checker():
    thread = threading.Thread(target=check_expired_channels_background, daemon=True)
    thread.start()
    log.info("Channel expiry checker started")

# ─────────────────────────────────────────────
#  ADMIN HELPERS
# ─────────────────────────────────────────────
def get_all_admin_ids():
    conn = get_conn()
    rows = conn.execute("SELECT user_id FROM admins").fetchall()
    conn.close()
    return list(set(SUPER_ADMIN_IDS + [r["user_id"] for r in rows]))

def is_admin(uid): return uid in get_all_admin_ids()
def is_super_admin(uid): return uid in SUPER_ADMIN_IDS

def add_admin(uid, username, added_by):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO admins (user_id,username,added_by) VALUES (?,?,?)",
                 (uid, username or "", added_by))
    conn.commit()
    conn.close()

def remove_admin(uid):
    if uid in SUPER_ADMIN_IDS:
        return False
    conn = get_conn()
    conn.execute("DELETE FROM admins WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()
    return True

def list_admins():
    conn = get_conn()
    rows = conn.execute("SELECT user_id,username,added_by,added_at FROM admins ORDER BY added_at").fetchall()
    conn.close()
    return rows

# ─────────────────────────────────────────────
#  PREMIUM HELPERS
# ─────────────────────────────────────────────
def is_premium(user_id):
    conn = get_conn()
    row = conn.execute("SELECT is_premium, premium_expiry FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    if row and row["is_premium"]:
        if row["premium_expiry"] == 0 or row["premium_expiry"] > int(time.time()):
            return True
    return False

def set_premium(user_id, days, added_by):
    expiry = int(time.time()) + (days * 86400) if days > 0 else 0
    conn = get_conn()
    conn.execute("UPDATE users SET is_premium=1, premium_expiry=? WHERE user_id=?", (expiry, user_id))
    conn.commit()
    conn.close()
    log_event("premium_activated", user_id, f"days={days} by {added_by}")

def remove_premium(user_id):
    conn = get_conn()
    conn.execute("UPDATE users SET is_premium=0, premium_expiry=0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def can_forward_message(user_id):
    if is_super_admin(user_id) or is_premium(user_id):
        conn = get_conn()
        row = conn.execute("SELECT forward_count, max_forward FROM users WHERE user_id=?", (user_id,)).fetchone()
        conn.close()
        return row["forward_count"] < row["max_forward"]
    return False

def increment_forward(user_id):
    conn = get_conn()
    conn.execute("UPDATE users SET forward_count=forward_count+1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
#  USER HELPERS
# ─────────────────────────────────────────────
def upsert_user(u):
    conn = get_conn()
    conn.execute("""INSERT INTO users (user_id,username,first_name,last_seen)
        VALUES (?,?,?,strftime('%s','now'))
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            first_name=excluded.first_name,
            last_seen=excluded.last_seen""",
        (u.id, u.username or "", u.first_name or ""))
    conn.commit()
    conn.close()

def is_banned(uid):
    conn = get_conn()
    row = conn.execute("SELECT is_banned FROM users WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return bool(row and row["is_banned"])

def ban_user(uid):
    conn = get_conn()
    conn.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

def unban_user(uid):
    conn = get_conn()
    conn.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

def get_all_user_ids():
    conn = get_conn()
    rows = conn.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()
    conn.close()
    return [r["user_id"] for r in rows]

def get_all_users_with_details(offset=0, limit=10):
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    rows = conn.execute("""
        SELECT user_id, username, first_name, files_recv, is_banned, is_premium, premium_expiry,
               first_seen, last_seen
        FROM users 
        ORDER BY last_seen DESC 
        LIMIT ? OFFSET ?
    """, (limit, offset)).fetchall()
    conn.close()
    return total, rows

def get_premium_users_with_details(offset=0, limit=10):
    now = int(time.time())
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM users WHERE is_premium=1 AND (premium_expiry=0 OR premium_expiry>?)", (now,)).fetchone()[0]
    rows = conn.execute("""
        SELECT user_id, username, first_name, files_recv, premium_expiry, last_seen
        FROM users 
        WHERE is_premium=1 AND (premium_expiry=0 OR premium_expiry>?)
        ORDER BY premium_expiry DESC
        LIMIT ? OFFSET ?
    """, (now, limit, offset)).fetchall()
    conn.close()
    return total, rows

def get_banned_users_with_details(offset=0, limit=10):
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM users WHERE is_banned=1").fetchone()[0]
    rows = conn.execute("""
        SELECT user_id, username, first_name, files_recv, last_seen
        FROM users 
        WHERE is_banned=1
        ORDER BY last_seen DESC
        LIMIT ? OFFSET ?
    """, (limit, offset)).fetchall()
    conn.close()
    return total, rows

def search_users(query, offset=0, limit=10):
    conn = get_conn()
    search_pattern = f"%{query}%"
    try:
        user_id = int(query)
        rows = conn.execute("""
            SELECT user_id, username, first_name, files_recv, is_banned, is_premium, premium_expiry,
                   first_seen, last_seen
            FROM users 
            WHERE user_id = ?
            ORDER BY last_seen DESC
        """, (user_id,)).fetchall()
        total = len(rows)
    except:
        rows = conn.execute("""
            SELECT user_id, username, first_name, files_recv, is_banned, is_premium, premium_expiry,
                   first_seen, last_seen
            FROM users 
            WHERE username LIKE ? OR CAST(user_id AS TEXT) LIKE ?
            ORDER BY last_seen DESC
            LIMIT ? OFFSET ?
        """, (search_pattern, search_pattern, limit, offset)).fetchall()
        count_row = conn.execute("""
            SELECT COUNT(*) FROM users 
            WHERE username LIKE ? OR CAST(user_id AS TEXT) LIKE ?
        """, (search_pattern, search_pattern)).fetchone()
        total = count_row[0] if count_row else 0
    conn.close()
    return total, rows

def get_user_full_details(user_id):
    conn = get_conn()
    row = conn.execute("""
        SELECT u.*, 
               (SELECT COUNT(*) FROM stats WHERE event='file_delivered' AND user_id=u.user_id) as total_downloads
        FROM users u
        WHERE u.user_id = ?
    """, (user_id,)).fetchone()
    conn.close()
    return row

def format_user_card(user):
    premium_status = "⭐ PREMIUM" if user["is_premium"] else "🆓 FREE"
    banned_status = "🚫 BANNED" if user["is_banned"] else "✅ ACTIVE"
    
    if user["premium_expiry"] and user["premium_expiry"] > 0 and user["is_premium"]:
        expiry_date = datetime.fromtimestamp(user["premium_expiry"]).strftime("%d %b %Y")
        premium_text = f"📅 Expires: {expiry_date}"
    elif user["is_premium"]:
        premium_text = "♾️ Lifetime Premium"
    else:
        premium_text = "❌ No Premium"
    
    first_seen = datetime.fromtimestamp(user["first_seen"]).strftime("%d %b %Y")
    last_seen = datetime.fromtimestamp(user["last_seen"]).strftime("%d %b %Y, %H:%M")
    
    username_display = f"@{user['username']}" if user['username'] else "No Username"
    
    return f"""
┌─────────────────────────┐
│  👤 <b>USER DETAILS</b>      │
└─────────────────────────┘

<b>🆔 ID:</b> <code>{user['user_id']}</code>
<b>📛 Name:</b> {esc(user['first_name'] or 'Unknown')}
<b>🔖 Username:</b> {username_display}

<b>📊 Statistics:</b>
• <b>Files Downloaded:</b> <code>{user['files_recv']}</code>
• <b>Total Downloads:</b> <code>{user.get('total_downloads', 0)}</code>

<b>⭐ Premium Status:</b> {premium_status}
• {premium_text}

<b>🚦 Account Status:</b> {banned_status}

<b>📅 Activity:</b>
• <b>First Seen:</b> {first_seen}
• <b>Last Seen:</b> {last_seen}
"""

# ─────────────────────────────────────────────
#  FILE HELPERS
# ─────────────────────────────────────────────
def save_files(key, file_list, ttl=0, max_hits=0, is_premium=0):
    expires = int(time.time()) + ttl * 3600 if ttl > 0 else 0
    conn = get_conn()
    conn.execute("DELETE FROM files WHERE key=?", (key,))
    for item in file_list:
        conn.execute("""INSERT INTO files (key,file_id,type,caption,label,expires,max_hits,is_premium) 
                        VALUES (?,?,?,?,?,?,?,?)""",
                     (key, item[0], item[1], item[2], item[3], expires, max_hits, is_premium))
    conn.commit()
    conn.close()

def get_files(key):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM files WHERE key=? ORDER BY id", (key,)).fetchall()
    conn.close()
    return rows

def increment_hits(key):
    conn = get_conn()
    conn.execute("UPDATE files SET hits=hits+1 WHERE key=?", (key,))
    conn.commit()
    conn.close()

def get_file_hits(key):
    conn = get_conn()
    row = conn.execute("SELECT hits, max_hits FROM files WHERE key=? LIMIT 1", (key,)).fetchone()
    conn.close()
    return row["hits"] if row else 0, row["max_hits"] if row else 0

def delete_file_key(key):
    conn = get_conn()
    conn.execute("DELETE FROM files WHERE key=?", (key,))
    conn.commit()
    conn.close()

def delete_all_files():
    conn = get_conn()
    conn.execute("DELETE FROM files")
    conn.commit()
    conn.close()

def list_all_keys():
    conn = get_conn()
    rows = conn.execute(
        "SELECT key,label,type,hits,created,expires,max_hits,is_premium FROM files GROUP BY key ORDER BY created DESC"
    ).fetchall()
    conn.close()
    return rows

# ─────────────────────────────────────────────
#  STATS / LOG
# ─────────────────────────────────────────────
def log_event(event, user_id=None, detail=""):
    conn = get_conn()
    conn.execute("INSERT INTO stats (event,user_id,detail) VALUES (?,?,?)", (event, user_id, detail))
    conn.commit()
    conn.close()

def get_stats():
    conn = get_conn()
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_files = conn.execute("SELECT COUNT(DISTINCT key) FROM files").fetchone()[0]
    total_served = conn.execute("SELECT SUM(hits) FROM files").fetchone()[0] or 0
    banned_count = conn.execute("SELECT COUNT(*) FROM users WHERE is_banned=1").fetchone()[0]
    premium_count = conn.execute("SELECT COUNT(*) FROM users WHERE is_premium=1").fetchone()[0]
    today = int(datetime.now().replace(hour=0, minute=0, second=0).timestamp())
    new_today = conn.execute("SELECT COUNT(*) FROM users WHERE first_seen>=?", (today,)).fetchone()[0]
    conn.close()
    return dict(users=total_users, files=total_files, served=total_served,
                banned=banned_count, premium=premium_count, new_today=new_today)

# ─────────────────────────────────────────────
#  RATE LIMITER
# ─────────────────────────────────────────────
_buckets = defaultdict(list)

def check_rate(uid):
    now = time.time()
    bkt = _buckets[uid]
    bkt[:] = [t for t in bkt if now - t < RATE_LIMIT_WIN]
    if len(bkt) >= RATE_LIMIT_MSG:
        return False
    bkt.append(now)
    return True

# ─────────────────────────────────────────────
#  DECORATORS
# ─────────────────────────────────────────────
def private_only(fn):
    @wraps(fn)
    def w(message, *a, **k):
        if message.chat.type in ("group", "supergroup", "channel"):
            return
        return fn(message, *a, **k)
    return w

def admin_only(fn):
    @wraps(fn)
    def w(message, *a, **k):
        if message.chat.type in ("group", "supergroup", "channel"):
            return
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔ <b>You are not authorized.</b>")
            return
        return fn(message, *a, **k)
    return w

def rate_limited(fn):
    @wraps(fn)
    def w(message, *a, **k):
        if not is_admin(message.from_user.id):
            if not check_rate(message.from_user.id):
                bot.reply_to(message, "⏳ <i>Slow down! Too many requests.</i>")
                return
        return fn(message, *a, **k)
    return w

def not_banned(fn):
    @wraps(fn)
    def w(message, *a, **k):
        if is_banned(message.from_user.id):
            bot.reply_to(message, "🚫 <b>You have been banned from this bot.</b>")
            return
        return fn(message, *a, **k)
    return w

# ─────────────────────────────────────────────
#  KEYBOARDS
# ─────────────────────────────────────────────
TYPE_EMOJI = {"document": "📄", "video": "🎬", "photo": "🖼️", "audio": "🎵", "voice": "🎤", "text": "📝"}

def get_admin_reply_keyboard():
    kb = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        "📤 Upload File", "📂 My Files",
        "📊 Stats", "📡 Channels",
        "📣 Broadcast", "👥 Users",
        "👑 Manage Admins", "⭐ Premium",
        "📎 Get Link", "❌ Close Keyboard"
    ]
    kb.add(*buttons)
    return kb

def get_user_reply_keyboard(user_id):
    kb = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = ["📁 Get File", "ℹ️ About"]
    if is_premium(user_id) or is_super_admin(user_id):
        buttons.append("🔄 Forward Message")
    buttons.append("❌ Close Keyboard")
    kb.add(*buttons)
    return kb

def remove_reply_keyboard():
    return types.ReplyKeyboardRemove()

def join_keyboard(file_key):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("📢 Join Official Channel", url=f"https://t.me/{FIXED_CHANNEL}"))
    kb.add(types.InlineKeyboardButton("👥 Join Official Group", url=f"https://t.me/{FIXED_GROUP}"))
    for row in get_channels():
        url = row["custom_url"] if row["custom_url"] else f"https://t.me/{row['username']}"
        kb.add(types.InlineKeyboardButton(row["button_name"], url=url))
    kb.add(types.InlineKeyboardButton("✅ I've Joined — Give Me The File!", callback_data=f"verify_{file_key}"))
    return kb

def get_user_management_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("📋 List Users", callback_data="user_list_1"),
        types.InlineKeyboardButton("🔍 Search User", callback_data="user_search"),
        types.InlineKeyboardButton("⭐ Premium Users", callback_data="user_premium_list_1"),
        types.InlineKeyboardButton("🚫 Banned Users", callback_data="user_banned_list_1"),
        types.InlineKeyboardButton("📊 User Stats", callback_data="user_stats"),
        types.InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_home")
    ]
    kb.add(*buttons)
    return kb

def get_caption_keyboard(file_index, total_files, collected_data):
    kb = types.InlineKeyboardMarkup(row_width=2)
    
    if file_index < total_files - 1:
        kb.add(
            types.InlineKeyboardButton("📝 Add Caption", callback_data=f"caption_add_{file_index}"),
            types.InlineKeyboardButton("⏭️ Skip Caption", callback_data=f"caption_skip_{file_index}")
        )
        kb.add(types.InlineKeyboardButton("❌ Cancel Upload", callback_data="upload_cancel"))
    else:
        kb.add(
            types.InlineKeyboardButton("📝 Add Caption", callback_data=f"caption_add_{file_index}"),
            types.InlineKeyboardButton("⏭️ Skip Caption", callback_data=f"caption_skip_{file_index}")
        )
        kb.add(types.InlineKeyboardButton("✅ Finish & Continue", callback_data="caption_finish"))
        kb.add(types.InlineKeyboardButton("❌ Cancel Upload", callback_data="upload_cancel"))
    
    return kb

# ─────────────────────────────────────────────
#  GROUP WELCOME
# ─────────────────────────────────────────────
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new_member(message):
    for new_user in message.new_chat_members:
        if new_user.is_bot:
            continue
        name = esc(new_user.first_name or "Member")
        if new_user.username:
            mention = f'<a href="https://t.me/{new_user.username}">@{esc(new_user.username)}</a>'
        else:
            mention = f'<a href="tg://user?id={new_user.id}">{name}</a>'
        group_name = esc(message.chat.title or "this group")
        text = (
            "┌─────────────────────────┐\n"
            "│   🌟  <b>WELCOME ABOARD!</b>     │\n"
            "└─────────────────────────┘\n\n"
            f"<b>Hello,</b> {mention} <b>— glad to have you here!</b> 🎉\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>You are now a member of</i> <b>{group_name}</b>\n\n"
            "📌 <i>Please read the group rules.</i>\n"
            "💬 <i>Feel free to introduce yourself!</i>\n"
            "🤝 <i>Respect everyone in this community.</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "<b><u>We are happy to have you with us!</u></b> ✨"
        )
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("📢 Our Channel", url=f"https://t.me/{FIXED_CHANNEL}"),
            types.InlineKeyboardButton("🤖 Our Bot", url=f"https://t.me/{bot.get_me().username}")
        )
        try:
            bot.send_message(message.chat.id, text, reply_markup=kb)
        except Exception as e:
            log.error(f"Welcome error: {e}")

# ─────────────────────────────────────────────
#  /start COMMAND
# ─────────────────────────────────────────────
@bot.message_handler(commands=["start"])
@private_only
@not_banned
@rate_limited
def cmd_start(message):
    upsert_user(message.from_user)
    chat_id = message.chat.id
    parts = message.text.split()

    if len(parts) > 1:
        file_key = parts[1].strip()
        files = get_files(file_key)
        if not files:
            bot.send_message(chat_id, "❌ <b>File Not Found</b>\n\n<i>This link is invalid or has expired.</i>",
                             reply_markup=remove_reply_keyboard())
            return

        if files[0]["expires"] and time.time() > files[0]["expires"]:
            bot.send_message(chat_id, "⌛ <b>Link Expired</b>\n\n<i>This file link has expired.</i>",
                             reply_markup=remove_reply_keyboard())
            return

        hits, max_hits = get_file_hits(file_key)
        if max_hits > 0 and hits >= max_hits:
            bot.send_message(chat_id, "🚫 <b>Link Expired</b>\n\n<i>This file has reached its maximum download limit.</i>",
                             reply_markup=remove_reply_keyboard())
            return

        if files[0]["is_premium"] == 1 and not (is_premium(message.from_user.id) or is_admin(message.from_user.id)):
            bot.send_message(chat_id,
                             "⭐ <b>PREMIUM FILE</b> ⭐\n\n"
                             "<i>This file is only available for premium users.</i>\n\n"
                             f"Contact @{OWNER_USERNAME} to get premium access! 💎",
                             reply_markup=remove_reply_keyboard())
            return

        label = esc(files[0]["label"] or "Unnamed File")
        file_count = len(files)
        type_icon = TYPE_EMOJI.get(files[0]["type"], "📦")
        premium_badge = " ⭐ PREMIUM" if files[0]["is_premium"] else ""

        bot.send_message(chat_id,
                         "┌──────────────────────┐\n"
                         f"│  {type_icon}  <b>FILE STORE BOT</b>{premium_badge}     │\n"
                         "└──────────────────────┘\n\n"
                         f"📦 <b>{label}</b>\n"
                         f"<i>📁 {file_count} file(s) waiting for you</i>\n"
                         f"<i>📊 Downloads left: {max_hits - hits if max_hits > 0 else '∞'}</i>\n\n"
                         "━━━━━━━━━━━━━━━━━━━━━━━\n"
                         "⚠️ <b>To unlock your file:</b>\n\n"
                         "  1️⃣  <i>Join ALL channels below</i>\n"
                         "  2️⃣  <i>Tap ✅ Verify &amp; Get File</i>\n"
                         "  3️⃣  <i>File delivered instantly!</i>\n"
                         "━━━━━━━━━━━━━━━━━━━━━━━",
                         reply_markup=join_keyboard(file_key))
        log_event("start_file", message.from_user.id, file_key)
        return

    if is_admin(chat_id):
        s = get_stats()
        bot_name = bot.get_me().username
        bot.send_message(chat_id,
                         f"╔════════════════════════╗\n"
                         f"║   👑  <b>ADMIN PANEL</b>        ║\n"
                         f"║   🤖  <i>v{BOT_VERSION}</i>      ║\n"
                         f"║   👤  @{OWNER_USERNAME}         ║\n"
                         "╚════════════════════════╝\n\n"
                         f"<b>👤 Users:</b> <code>{s['users']}</code>  <b>🆕 Today:</b> <code>{s['new_today']}</code>\n"
                         f"<b>📁 Files:</b> <code>{s['files']}</code>  <b>📬 Served:</b> <code>{s['served']}</code>\n"
                         f"<b>⭐ Premium:</b> <code>{s['premium']}</code>  <b>🚫 Banned:</b> <code>{s['banned']}</code>\n\n"
                         f"<b>🔗 Bot Link:</b>\n<code>https://t.me/{bot_name}?start=</code>\n\n"
                         "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                         "<i>Tap any button below 👇</i>",
                         reply_markup=get_admin_reply_keyboard())
    else:
        user_id = message.from_user.id
        premium_status = "⭐ <b>PREMIUM USER</b> ⭐" if is_premium(user_id) else "🆓 <b>Free User</b>"
        bot.send_message(chat_id,
                         "┌───────────────────────┐\n"
                         "│  🤖  <b>FILE STORE BOT</b>     │\n"
                         "└───────────────────────┘\n\n"
                         f"{premium_status}\n\n"
                         "<b>Welcome!</b> <i>I securely deliver files.</i>\n\n"
                         "📎 <i>Use a valid file link to get started.</i>\n"
                         f"<i>Contact @{OWNER_USERNAME} for premium access.</i>",
                         reply_markup=get_user_reply_keyboard(user_id))
    log_event("start", message.from_user.id)

# ─────────────────────────────────────────────
#  REPLY KEYBOARD HANDLERS
# ─────────────────────────────────────────────
@bot.message_handler(func=lambda m: m.text == "📤 Upload File")
@private_only
@admin_only
def reply_upload(message):
    _upload_ask_type(message.chat.id)

@bot.message_handler(func=lambda m: m.text == "📂 My Files")
@private_only
@admin_only
def reply_my_files(message):
    keys = list_all_keys()
    if not keys:
        bot.reply_to(message, "📂 <b>No files found!</b>\n\nUse Upload File button to add files.",
                     reply_markup=get_admin_reply_keyboard())
        return

    bot_name = bot.get_me().username
    lines = ["📂 <b>Your Stored Files:</b>\n"]
    for i, row in enumerate(keys, 1):
        exp = "∞" if not row["expires"] else datetime.fromtimestamp(row["expires"]).strftime("%d/%m %H:%M")
        premium = " ⭐" if row["is_premium"] else ""
        max_hits_info = f" | 🔢 {row['max_hits']}" if row['max_hits'] > 0 else ""
        link = f"https://t.me/{bot_name}?start={row['key']}"
        lines.append(f"{i}. <code>{row['key']}</code>{premium}\n"
                     f"   📝 {esc(row['label'] or '—')} | ⬇️ {row['hits']}{max_hits_info} | ⌛ {exp}\n"
                     f"   🔗 <code>{link}</code>\n")

    lines.append("\n<b>Commands:</b>\n<code>/delkey &lt;key&gt;</code> - Delete a file\n<code>/delall</code> - Delete all files")
    bot.reply_to(message, "\n".join(lines)[:4096], reply_markup=get_admin_reply_keyboard())

@bot.message_handler(func=lambda m: m.text == "📊 Stats")
@private_only
@admin_only
def reply_stats(message):
    s = get_stats()
    bot.reply_to(message,
                 f"📊 <b>Bot Statistics</b>\n"
                 f"━━━━━━━━━━━━━━━━━━━━\n"
                 f"<b>👤 Total Users:</b>   <code>{s['users']}</code>\n"
                 f"<b>🆕 New Today:</b>     <code>{s['new_today']}</code>\n"
                 f"<b>⭐ Premium Users:</b>  <code>{s['premium']}</code>\n"
                 f"<b>📁 File Keys:</b>     <code>{s['files']}</code>\n"
                 f"<b>📬 Files Served:</b>  <code>{s['served']}</code>\n"
                 f"<b>🚫 Banned Users:</b>  <code>{s['banned']}</code>\n"
                 f"━━━━━━━━━━━━━━━━━━━━\n"
                 f"<i>🕐 {datetime.now().strftime('%d %b %Y %H:%M')}</i>",
                 reply_markup=get_admin_reply_keyboard())

@bot.message_handler(func=lambda m: m.text == "📡 Channels")
@private_only
@admin_only
def reply_channels(message):
    chans = get_channels()
    lines = ["📡 <b>Extra Force-Subscribe Channels:</b>\n"]
    for row in chans:
        url = row["custom_url"] if row["custom_url"] else f"https://t.me/{row['username']}"
        tag = "🔒" if row["username"].startswith("+") else "📢"
        
        # Show expiry info
        if row["expires_at"] and row["expires_at"] > 0:
            remaining = row["expires_at"] - int(time.time())
            if remaining > 0:
                expiry_text = f"⏰ Expires in: {format_time_duration(remaining)}"
            else:
                expiry_text = "⌛ EXPIRED"
        else:
            expiry_text = "♾️ No expiry"
        
        lines.append(f"{tag} <i>{esc(row['button_name'])}</i>\n"
                     f"   <code>{url}</code>\n"
                     f"   <i>{expiry_text}</i>")
    if not chans:
        lines.append("<i>None added yet.</i>")
    lines.append("\n<b>Commands:</b>")
    lines.append("<code>/add Button Name @username 1d/1h/1m/1s</code> — Add channel with expiry")
    lines.append("<code>/add Button Name @username</code> — Add permanent channel")
    lines.append("<code>/remove @username</code> — Remove channel")
    lines.append("\n<b>Examples:</b>")
    lines.append("<code>/add My Channel @channel 1d</code> — Expires in 1 day")
    lines.append("<code>/add VIP Channel @vip 2h</code> — Expires in 2 hours")
    bot.reply_to(message, "\n".join(lines), reply_markup=get_admin_reply_keyboard())

@bot.message_handler(func=lambda m: m.text == "📣 Broadcast")
@private_only
@admin_only
def reply_broadcast(message):
    msg = bot.reply_to(message,
                       "📣 <b>Broadcast Mode</b>\n\n"
                       "<i>Send your broadcast message.</i>\n"
                       "<i>Supports: text, photo, video, document.</i>\n\n"
                       "<i>Type /cancel to abort.</i>",
                       reply_markup=get_admin_reply_keyboard())
    bot.register_next_step_handler(msg, do_broadcast)

@bot.message_handler(func=lambda m: m.text == "👥 Users")
@private_only
@admin_only
def reply_users(message):
    s = get_stats()
    bot.send_message(message.chat.id,
                     f"👥 <b>User Management Panel</b>\n\n"
                     f"📊 <b>Quick Stats:</b>\n"
                     f"• <b>Total Users:</b> <code>{s['users']}</code>\n"
                     f"• <b>⭐ Premium:</b> <code>{s['premium']}</code>\n"
                     f"• <b>🚫 Banned:</b> <code>{s['banned']}</code>\n"
                     f"• <b>🆕 Today:</b> <code>{s['new_today']}</code>\n\n"
                     f"<i>Select an option below 👇</i>",
                     reply_markup=get_user_management_keyboard())

@bot.message_handler(func=lambda m: m.text == "👑 Manage Admins")
@private_only
@admin_only
def reply_admins(message):
    db_admins = list_admins()
    lines = ["👑 <b>Admin Management</b>\n", "<b>🔐 Super Admins:</b>"]
    for sid in SUPER_ADMIN_IDS:
        lines.append(f"  • <code>{sid}</code>")
    lines.append("\n<b>👮 Panel Admins:</b>")
    if db_admins:
        for row in db_admins:
            uname = f"@{esc(row['username'])}" if row["username"] else "Unknown"
            lines.append(f"  • <code>{row['user_id']}</code> {uname}")
    else:
        lines.append("  <i>None added yet.</i>")
    lines.append("\n<b>Commands:</b>\n<code>/addadmin &lt;id&gt;</code>\n<code>/removeadmin &lt;id&gt;</code>\n<code>/listadmins</code>")
    bot.reply_to(message, "\n".join(lines), reply_markup=get_admin_reply_keyboard())

@bot.message_handler(func=lambda m: m.text == "⭐ Premium")
@private_only
@admin_only
def reply_premium(message):
    total, premium_users = get_premium_users_with_details(0, 50)
    lines = ["⭐ <b>Premium Users List:</b>\n"]
    if premium_users:
        for row in premium_users:
            expiry = "Lifetime" if row["premium_expiry"] == 0 else datetime.fromtimestamp(row["premium_expiry"]).strftime("%d %b %Y")
            uname = f"@{row['username']}" if row['username'] else str(row['user_id'])
            lines.append(f"• <code>{row['user_id']}</code> {uname} | <i>{expiry}</i>")
    else:
        lines.append("<i>No premium users yet.</i>")

    lines.append(f"\n<b>Total Premium:</b> {total}")
    lines.append("\n<b>Commands:</b>")
    lines.append("<code>/premium &lt;user_id&gt; &lt;days&gt;</code> — Add premium (0 for lifetime)")
    lines.append("<code>/removepremium &lt;user_id&gt;</code> — Remove premium")

    bot.reply_to(message, "\n".join(lines), reply_markup=get_admin_reply_keyboard())

@bot.message_handler(func=lambda m: m.text == "📎 Get Link")
@private_only
@admin_only
def reply_get_link(message):
    bot.reply_to(message,
                 "🔗 <b>Get File Link</b>\n\n"
                 "<i>Send me the file key:</i>\n"
                 "Example: <code>8551188a46</code>\n\n"
                 "<i>Type /cancel to abort.</i>",
                 reply_markup=get_admin_reply_keyboard())
    bot.register_next_step_handler(message, _get_link_by_key)

def _get_link_by_key(message):
    if _is_cancel(message):
        return
    key = message.text.strip()
    files = get_files(key)
    if not files:
        bot.reply_to(message, f"❌ <b>Key not found:</b> <code>{key}</code>", reply_markup=get_admin_reply_keyboard())
        return

    bot_name = bot.get_me().username
    link = f"https://t.me/{bot_name}?start={key}"
    label = files[0]["label"] or "No label"

    bot.reply_to(message,
                 f"🔗 <b>File Link Generated!</b>\n\n"
                 f"<b>🏷️ Label:</b> <i>{esc(label)}</i>\n"
                 f"<b>🔑 Key:</b> <code>{key}</code>\n\n"
                 f"<b>📎 Share Link:</b>\n<code>{link}</code>\n\n"
                 f"<i>Tap and hold to copy the link</i>",
                 reply_markup=get_admin_reply_keyboard())

@bot.message_handler(func=lambda m: m.text == "🔄 Forward Message")
@private_only
@not_banned
def reply_forward(message):
    if not can_forward_message(message.from_user.id):
        bot.reply_to(message,
                     "❌ <b>Cannot Forward</b>\n\n"
                     "<i>You have reached your forward limit or don't have premium access.</i>\n\n"
                     f"Contact @{OWNER_USERNAME} to get premium! ⭐",
                     reply_markup=get_user_reply_keyboard(message.from_user.id))
        return

    msg = bot.reply_to(message,
                       "🔄 <b>Forward Mode</b>\n\n"
                       "<i>Forward any message from this bot to another user!</i>\n\n"
                       "<b>How to use:</b>\n"
                       "1. Forward the message you want to share\n"
                       "2. Forward it to me\n"
                       "3. I'll ask for recipient\n\n"
                       "<i>Type /cancel to abort.</i>",
                       reply_markup=get_user_reply_keyboard(message.from_user.id))
    bot.register_next_step_handler(msg, _forward_get_message)

def _forward_get_message(message):
    if _is_cancel(message):
        return
    if not message.forward_from:
        bot.reply_to(message, "❌ <i>Please forward a message from the bot!</i>",
                     reply_markup=get_user_reply_keyboard(message.from_user.id))
        return

    original_sender = message.forward_from.id
    bot.reply_to(message,
                 "📝 <i>Now send me the recipient's user ID or username:</i>\n"
                 "Example: <code>123456789</code> or @username",
                 reply_markup=get_user_reply_keyboard(message.from_user.id))
    bot.register_next_step_handler(message, _forward_send, original_sender, message.message_id)

def _forward_send(message, original_sender, original_msg_id):
    if _is_cancel(message):
        return
    target = message.text.strip()
    target_id = None

    if target.startswith("@"):
        target = target[1:]
        conn = get_conn()
        row = conn.execute("SELECT user_id FROM users WHERE username=?", (target,)).fetchone()
        conn.close()
        if row:
            target_id = row["user_id"]
    else:
        try:
            target_id = int(target)
        except:
            pass

    if not target_id:
        bot.reply_to(message, "❌ <i>Invalid user ID or username!</i>",
                     reply_markup=get_user_reply_keyboard(message.from_user.id))
        return

    try:
        bot.copy_message(target_id, message.chat.id, original_msg_id)
        increment_forward(message.from_user.id)
        bot.reply_to(message, f"✅ <b>Message forwarded successfully!</b>\n\n<i>Sent to:</i> <code>{target_id}</code>",
                     reply_markup=get_user_reply_keyboard(message.from_user.id))
        log_event("premium_forward", message.from_user.id, f"to={target_id}")
    except Exception as e:
        bot.reply_to(message, f"❌ <i>Failed to forward: {str(e)}</i>",
                     reply_markup=get_user_reply_keyboard(message.from_user.id))

@bot.message_handler(func=lambda m: m.text == "📁 Get File")
@private_only
@not_banned
def reply_get_file(message):
    bot.reply_to(message,
                 "🔗 <b>Send me a file link!</b>\n\n"
                 f"<i>Example:</i> <code>https://t.me/{bot.get_me().username}?start=8551188a46</code>\n\n"
                 f"<i>Contact @{OWNER_USERNAME} for premium access.</i>",
                 reply_markup=get_user_reply_keyboard(message.from_user.id))

@bot.message_handler(func=lambda m: m.text == "ℹ️ About")
@private_only
def reply_about(message):
    is_prem = is_premium(message.from_user.id)
    bot.reply_to(message,
                 f"🤖 <b>File Store Bot</b> <i>v{BOT_VERSION}</i>\n\n"
                 f"<b>Owner:</b> @{OWNER_USERNAME}\n\n"
                 "<b>Features:</b>\n"
                 "• Secure file storage\n"
                 "• Force channel subscription\n"
                 "• Channel expiry system\n"
                 "• Premium membership\n"
                 "• Message forwarding (Premium)\n"
                 "• File links with expiry\n"
                 "• User management with pagination\n"
                 "• Caption support for files\n\n"
                 f"<b>Your Status:</b> {'⭐ PREMIUM' if is_prem else '🆓 Free User'}\n\n"
                 f"<i>Contact @{OWNER_USERNAME} for premium upgrade! 💎</i>",
                 reply_markup=get_user_reply_keyboard(message.from_user.id))

@bot.message_handler(func=lambda m: m.text == "❌ Close Keyboard")
@private_only
def reply_close_keyboard(message):
    bot.send_message(message.chat.id, "⌨️ <b>Keyboard closed!</b>\n\nSend /start to open again.",
                     reply_markup=remove_reply_keyboard())

# ─────────────────────────────────────────────
#  USER MANAGEMENT CALLBACKS
# ─────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("user_"))
def user_management_callbacks(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ Not authorized.", show_alert=True)
        return

    data = call.data
    cid = call.message.chat.id
    mid = call.message.message_id

    if data.startswith("user_list_"):
        page = int(data.split("_")[2]) if len(data.split("_")) > 2 else 1
        _show_user_list(cid, mid, page, call)

    elif data.startswith("user_premium_list_"):
        page = int(data.split("_")[3]) if len(data.split("_")) > 3 else 1
        _show_premium_users(cid, mid, page, call)

    elif data.startswith("user_banned_list_"):
        page = int(data.split("_")[3]) if len(data.split("_")) > 3 else 1
        _show_banned_users(cid, mid, page, call)

    elif data == "user_search":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(cid,
                               "🔍 <b>Search User</b>\n\n"
                               "<i>Send me the user ID or username to search:</i>\n"
                               "Example: <code>123456789</code> or <code>@username</code>\n\n"
                               "<i>Type /cancel to cancel.</i>")
        bot.register_next_step_handler(msg, _search_user_handler, cid, mid)

    elif data.startswith("user_search_page_"):
        parts = data.split("_")
        page = int(parts[3])
        query = "_".join(parts[4:])
        _show_search_results(cid, mid, query, page, call)

    elif data == "user_stats":
        s = get_stats()
        bot.edit_message_text(
            f"📊 <b>User Statistics</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>👤 Total Users:</b>   <code>{s['users']}</code>\n"
            f"<b>🆕 New Today:</b>     <code>{s['new_today']}</code>\n"
            f"<b>⭐ Premium Users:</b>  <code>{s['premium']}</code>\n"
            f"<b>🚫 Banned Users:</b>  <code>{s['banned']}</code>\n"
            f"<b>📬 Total Served:</b>  <code>{s['served']}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Average new users/day: {s['new_today']}</i>",
            cid, mid, reply_markup=get_user_management_keyboard())
        bot.answer_callback_query(call.id)

    elif data == "user_back":
        s = get_stats()
        bot.edit_message_text(
            f"👥 <b>User Management Panel</b>\n\n"
            f"📊 <b>Quick Stats:</b>\n"
            f"• <b>Total Users:</b> <code>{s['users']}</code>\n"
            f"• <b>⭐ Premium:</b> <code>{s['premium']}</code>\n"
            f"• <b>🚫 Banned:</b> <code>{s['banned']}</code>\n"
            f"• <b>🆕 Today:</b> <code>{s['new_today']}</code>\n\n"
            f"<i>Select an option below 👇</i>",
            cid, mid, reply_markup=get_user_management_keyboard())
        bot.answer_callback_query(call.id)

    elif data.startswith("user_give_premium_"):
        user_id = int(data.split("_")[3])
        bot.answer_callback_query(call.id)
        msg = bot.send_message(cid,
                               f"⭐ <b>Give Premium to</b> <code>{user_id}</code>\n\n"
                               f"<i>Enter number of days (0 for lifetime):</i>\n"
                               f"Example: <code>30</code> or <code>0</code>\n\n"
                               f"<i>Type /cancel to cancel.</i>")
        bot.register_next_step_handler(msg, _give_premium_handler, user_id, cid, mid)

    elif data.startswith("user_ban_"):
        user_id = int(data.split("_")[2])
        ban_user(user_id)
        bot.answer_callback_query(call.id, f"✅ User {user_id} banned!", show_alert=True)
        _show_user_list(cid, mid, 1, call)

    elif data.startswith("user_full_stats_"):
        user_id = int(data.split("_")[3])
        user = get_user_full_details(user_id)
        if user:
            card = format_user_card(user)
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(
                types.InlineKeyboardButton("⭐ Give Premium", callback_data=f"user_give_premium_{user_id}"),
                types.InlineKeyboardButton("🚫 Ban User", callback_data=f"user_ban_{user_id}")
            )
            kb.add(
                types.InlineKeyboardButton("🔙 Back", callback_data="user_back"),
                types.InlineKeyboardButton("🏠 Home", callback_data="admin_home")
            )
            bot.edit_message_text(card, cid, mid, reply_markup=kb)
        bot.answer_callback_query(call.id)

    elif data == "noop":
        bot.answer_callback_query(call.id)

def _show_user_list(cid, mid, page, call):
    limit = 10
    offset = (page - 1) * limit
    total, users = get_all_users_with_details(offset, limit)

    if not users:
        bot.answer_callback_query(call.id, "No users found!")
        return

    total_pages = (total + limit - 1) // limit

    lines = ["👥 <b>USER LIST</b>\n"]
    lines.append(f"📊 <i>Total: {total} users | Page {page}/{total_pages}</i>\n")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    for i, user in enumerate(users, start=offset + 1):
        premium_icon = "⭐" if user["is_premium"] else "⬜"
        banned_icon = "🚫" if user["is_banned"] else "✅"
        username_display = f"@{user['username']}" if user['username'] else "No username"

        lines.append(f"{i}. <b>{premium_icon} {banned_icon} ID:</b> <code>{user['user_id']}</code>")
        lines.append(f"   📛 <i>{esc(user['first_name'] or 'Unknown')}</i> | {username_display}")
        lines.append(f"   📥 Downloads: {user['files_recv']} | 📅 Last: {datetime.fromtimestamp(user['last_seen']).strftime('%d/%m')}")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("<i>Click on a user to see full details 👇</i>")

    kb = types.InlineKeyboardMarkup(row_width=3)

    for user in users:
        kb.add(types.InlineKeyboardButton(f"👤 {user['user_id']}", callback_data=f"user_full_stats_{user['user_id']}"))

    nav_buttons = []
    if page > 1:
        nav_buttons.append(types.InlineKeyboardButton("◀️ Previous", callback_data=f"user_list_{page-1}"))
    nav_buttons.append(types.InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_buttons.append(types.InlineKeyboardButton("Next ▶️", callback_data=f"user_list_{page+1}"))

    kb.row(*nav_buttons)
    kb.add(types.InlineKeyboardButton("🔙 Back to Menu", callback_data="user_back"))
    kb.add(types.InlineKeyboardButton("🏠 Admin Home", callback_data="admin_home"))

    bot.edit_message_text("\n".join(lines), cid, mid, reply_markup=kb)
    bot.answer_callback_query(call.id)

def _show_premium_users(cid, mid, page, call):
    limit = 10
    offset = (page - 1) * limit
    total, users = get_premium_users_with_details(offset, limit)

    if not users:
        bot.edit_message_text("⭐ <b>No premium users found!</b>", cid, mid, reply_markup=get_user_management_keyboard())
        bot.answer_callback_query(call.id)
        return

    total_pages = (total + limit - 1) // limit

    lines = ["⭐ <b>PREMIUM USERS</b>\n"]
    lines.append(f"📊 <i>Total: {total} premium | Page {page}/{total_pages}</i>\n")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    for i, user in enumerate(users, start=offset + 1):
        if user["premium_expiry"] == 0:
            expiry = "LIFETIME ♾️"
        else:
            expiry = datetime.fromtimestamp(user["premium_expiry"]).strftime("%d %b %Y")

        username_display = f"@{user['username']}" if user['username'] else "No username"

        lines.append(f"{i}. <b>ID:</b> <code>{user['user_id']}</code>")
        lines.append(f"   📛 {esc(user['first_name'] or 'Unknown')} | {username_display}")
        lines.append(f"   📥 Downloads: {user['files_recv']} | ⭐ Expires: {expiry}")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    kb = types.InlineKeyboardMarkup(row_width=5)
    nav_buttons = []

    if page > 1:
        nav_buttons.append(types.InlineKeyboardButton("◀️", callback_data=f"user_premium_list_{page-1}"))
    nav_buttons.append(types.InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_buttons.append(types.InlineKeyboardButton("▶️", callback_data=f"user_premium_list_{page+1}"))

    kb.row(*nav_buttons)
    kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="user_back"))
    kb.add(types.InlineKeyboardButton("🏠 Home", callback_data="admin_home"))

    bot.edit_message_text("\n".join(lines), cid, mid, reply_markup=kb)
    bot.answer_callback_query(call.id)

def _show_banned_users(cid, mid, page, call):
    limit = 10
    offset = (page - 1) * limit
    total, users = get_banned_users_with_details(offset, limit)

    if not users:
        bot.edit_message_text("🚫 <b>No banned users found!</b>", cid, mid, reply_markup=get_user_management_keyboard())
        bot.answer_callback_query(call.id)
        return

    total_pages = (total + limit - 1) // limit

    lines = ["🚫 <b>BANNED USERS</b>\n"]
    lines.append(f"📊 <i>Total: {total} banned | Page {page}/{total_pages}</i>\n")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    for i, user in enumerate(users, start=offset + 1):
        username_display = f"@{user['username']}" if user['username'] else "No username"

        lines.append(f"{i}. <b>ID:</b> <code>{user['user_id']}</code>")
        lines.append(f"   📛 {esc(user['first_name'] or 'Unknown')} | {username_display}")
        lines.append(f"   📥 Downloads: {user['files_recv']}")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("<i>Use /unban &lt;id&gt; to unban users</i>")

    kb = types.InlineKeyboardMarkup(row_width=5)
    nav_buttons = []

    if page > 1:
        nav_buttons.append(types.InlineKeyboardButton("◀️", callback_data=f"user_banned_list_{page-1}"))
    nav_buttons.append(types.InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_buttons.append(types.InlineKeyboardButton("▶️", callback_data=f"user_banned_list_{page+1}"))

    kb.row(*nav_buttons)
    kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="user_back"))
    kb.add(types.InlineKeyboardButton("🏠 Home", callback_data="admin_home"))

    bot.edit_message_text("\n".join(lines), cid, mid, reply_markup=kb)
    bot.answer_callback_query(call.id)

def _search_user_handler(message, original_cid, original_mid):
    if _is_cancel(message):
        s = get_stats()
        bot.send_message(original_cid,
                         f"👥 <b>User Management Panel</b>\n\n"
                         f"📊 <b>Quick Stats:</b>\n"
                         f"• <b>Total Users:</b> <code>{s['users']}</code>\n"
                         f"• <b>⭐ Premium:</b> <code>{s['premium']}</code>\n"
                         f"• <b>🚫 Banned:</b> <code>{s['banned']}</code>\n\n"
                         f"<i>Select an option below 👇</i>",
                         reply_markup=get_user_management_keyboard())
        return

    query = message.text.strip()
    _show_search_results(original_cid, original_mid, query, 1, None)

def _show_search_results(cid, mid, query, page, call):
    limit = 10
    offset = (page - 1) * limit
    total, users = search_users(query, offset, limit)

    if not users:
        if call:
            bot.answer_callback_query(call.id, "No users found!")
        bot.edit_message_text(
            f"🔍 <b>Search Results</b>\n\n"
            f"<i>No users found for:</i> <code>{esc(query)}</code>\n\n"
            f"Try searching by ID or username.",
            cid, mid, reply_markup=get_user_management_keyboard())
        return

    total_pages = (total + limit - 1) // limit

    lines = [f"🔍 <b>SEARCH RESULTS: {esc(query)}</b>\n"]
    lines.append(f"📊 <i>Found: {total} users | Page {page}/{total_pages}</i>\n")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    for i, user in enumerate(users, start=offset + 1):
        premium_icon = "⭐" if user["is_premium"] else "⬜"
        banned_icon = "🚫" if user["is_banned"] else "✅"
        username_display = f"@{user['username']}" if user['username'] else "No username"

        lines.append(f"{i}. <b>{premium_icon} {banned_icon} ID:</b> <code>{user['user_id']}</code>")
        lines.append(f"   📛 <i>{esc(user['first_name'] or 'Unknown')}</i> | {username_display}")
        lines.append(f"   📥 Downloads: {user['files_recv']}")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    kb = types.InlineKeyboardMarkup(row_width=5)
    nav_buttons = []

    if page > 1:
        nav_buttons.append(types.InlineKeyboardButton("◀️", callback_data=f"user_search_page_{page-1}_{query}"))
    nav_buttons.append(types.InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_buttons.append(types.InlineKeyboardButton("▶️", callback_data=f"user_search_page_{page+1}_{query}"))

    kb.row(*nav_buttons)
    kb.add(types.InlineKeyboardButton("🔍 New Search", callback_data="user_search"))
    kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="user_back"))

    if call:
        bot.edit_message_text("\n".join(lines), cid, mid, reply_markup=kb)
        bot.answer_callback_query(call.id)
    else:
        bot.send_message(cid, "\n".join(lines), reply_markup=kb)

def _give_premium_handler(message, user_id, original_cid, original_mid):
    if _is_cancel(message):
        bot.send_message(original_cid, "❌ Cancelled.")
        return

    try:
        days = int(message.text.strip())
        set_premium(user_id, days, message.from_user.id)

        if days == 0:
            expiry_text = "LIFETIME ⭐"
        else:
            expiry_text = f"{days} days"

        bot.send_message(original_cid,
                         f"✅ <b>Premium Activated!</b>\n\n"
                         f"<b>User:</b> <code>{user_id}</code>\n"
                         f"<b>Duration:</b> {expiry_text}")

        try:
            bot.send_message(user_id,
                             f"🎉 <b>CONGRATULATIONS!</b> 🎉\n\n"
                             f"You have been upgraded to <b>PREMIUM</b>!\n\n"
                             f"<b>Duration:</b> {expiry_text}\n\n"
                             f"<b>Premium Features:</b>\n"
                             f"• Forward messages from bot\n"
                             f"• Access premium files\n"
                             f"• Priority support\n\n"
                             f"Thanks for using our bot! 💎")
        except:
            pass

        _show_user_list(original_cid, original_mid, 1, None)

    except ValueError:
        bot.send_message(original_cid, "❌ <i>Invalid number! Please enter a valid number of days.</i>")

# ─────────────────────────────────────────────
#  ADMIN PANEL CALLBACKS
# ─────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_"))
def admin_callbacks(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ Not authorized.", show_alert=True)
        return

    action = call.data
    cid = call.message.chat.id
    mid = call.message.message_id

    if action == "admin_upload":
        bot.answer_callback_query(call.id)
        _upload_ask_type(cid, edit_msg=call.message)
        return
    elif action == "admin_home":
        bot.delete_message(cid, mid)
        s = get_stats()
        bot.send_message(cid,
                         "╔═══════════════════════╗\n"
                         "║   👑  <b>ADMIN PANEL</b>        ║\n"
                         f"║   🤖  <i>v{BOT_VERSION}</i>      ║\n"
                         "╚═══════════════════════╝\n\n"
                         f"<b>👤 Users:</b> <code>{s['users']}</code>  <b>🆕 Today:</b> <code>{s['new_today']}</code>\n"
                         f"<b>📁 Files:</b> <code>{s['files']}</code>  <b>📬 Served:</b> <code>{s['served']}</code>\n"
                         f"<b>⭐ Premium:</b> <code>{s['premium']}</code>\n\n"
                         "<i>Tap any button below 👇</i>",
                         reply_markup=get_admin_reply_keyboard())
    bot.answer_callback_query(call.id)

# ─────────────────────────────────────────────
#  FILE UPLOAD FLOW WITH CAPTION OPTION
# ─────────────────────────────────────────────
upload_sessions = {}

def _upload_ask_type(chat_id, edit_msg=None):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("📁 File / Media", callback_data="utype_file"),
           types.InlineKeyboardButton("📝 Text Message", callback_data="utype_text"))
    kb.add(types.InlineKeyboardButton("⭐ Premium Only", callback_data="utype_premium"),
           types.InlineKeyboardButton("❌ Cancel", callback_data="admin_home"))
    text = ("╔═════════════════════╗\n"
            "║   📤  <b>NEW UPLOAD</b>     ║\n"
            "╚═════════════════════╝\n\n"
            "<b>Step 1 of 4</b> — <i>Choose content type:</i>\n\n"
            "📁 <b>File / Media</b> — <i>document, video, photo, audio</i>\n"
            "📝 <b>Text Message</b> — <i>plain text / announcement</i>\n"
            "⭐ <b>Premium Only</b> — <i>Only premium users can access</i>")
    if edit_msg:
        try:
            bot.edit_message_text(text, edit_msg.chat.id, edit_msg.message_id, reply_markup=kb)
        except:
            pass
    else:
        bot.send_message(chat_id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("utype_"))
def upload_type_chosen(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ Not authorized.", show_alert=True)
        return

    is_premium_file = 1 if call.data[6:] == "premium" else 0
    chat_id = call.message.chat.id

    if call.data[6:] == "text" or call.data[6:] == "premium":
        msg = bot.edit_message_text(
            "╔════════════════════╗\n║   📝  <b>TEXT UPLOAD</b>    ║\n╚════════════════════╝\n\n"
            "<b>Step 2 of 4</b> — <i>Send your text message:</i>\n\n"
            "<i>Type or paste the text you want to store.</i>\n<i>Type /cancel to abort.</i>",
            chat_id, call.message.message_id)
        bot.register_next_step_handler(msg, _text_got_content, is_premium_file)
    else:
        upload_sessions[chat_id] = {
            'files': [],
            'captions': [],
            'is_premium': is_premium_file,
            'current_index': 0
        }
        
        msg = bot.edit_message_text(
            "╔════════════════════╗\n║   📁  <b>FILE UPLOAD</b>    ║\n╚════════════════════╝\n\n"
            "<b>Step 2 of 4</b> — <i>Send your file(s):</i>\n\n"
            "• <i>Document, Video, Photo, Audio — all supported</i>\n"
            "• <i>Send multiple files one by one</i>\n"
            "• <i>Type</i> <code>DONE</code> <i>when finished</i>\n\n"
            "<i>Type /cancel to abort.</i>",
            chat_id, call.message.message_id)
        bot.register_next_step_handler(msg, _file_collect, chat_id)
    
    bot.answer_callback_query(call.id)

def _text_got_content(message, is_premium_file=0):
    if not is_admin(message.chat.id):
        return
    if _is_cancel(message):
        return
    if not message.text:
        m = bot.send_message(message.chat.id, "❌ <i>Send a text message. Type /cancel to abort.</i>")
        bot.register_next_step_handler(m, _text_got_content, is_premium_file)
        return
    msg = bot.send_message(message.chat.id,
                           "╔════════════════════╗\n║   🏷️  <b>LABEL</b>          ║\n╚════════════════════╝\n\n"
                           "<b>Step 3 of 4</b> — <i>Give it a label/title:</i>\n\n"
                           "<i>This is shown to users before they download.</i>\n"
                           "Example: <code>Important Announcement</code>")
    bot.register_next_step_handler(msg, _text_finalize, message.text.strip(), is_premium_file)

def _text_finalize(message, content, is_premium_file=0):
    if not is_admin(message.chat.id):
        return
    if _is_cancel(message):
        return
    label = message.text.strip() if message.text else "Text Message"
    key = hashlib.md5(f"t{time.time()}{message.chat.id}".encode()).hexdigest()[:10]
    save_files(key, [(content, "text", "", label)], is_premium=is_premium_file)
    conn = get_conn()
    conn.execute("UPDATE files SET label=?, is_premium=? WHERE key=?", (label, is_premium_file, key))
    conn.commit()
    conn.close()
    _send_success(message, key, label, 1, is_premium_file)

def _file_collect(message, chat_id):
    if not is_admin(message.chat.id):
        return
    
    session = upload_sessions.get(chat_id)
    if not session:
        return
    
    if _is_cancel(message):
        upload_sessions.pop(chat_id, None)
        return
    
    if message.text and message.text.strip().upper() == "DONE":
        if not session['files']:
            bot.send_message(chat_id, "<i>⚠️ No files yet. Send at least one or /cancel.</i>")
            bot.register_next_step_handler(message, _file_collect, chat_id)
            return
        
        msg = bot.send_message(chat_id,
                               "╔════════════════════╗\n║   🏷️  <b>LABEL</b>          ║\n╚════════════════════╝\n\n"
                               f"<b>Step 3 of 4</b> — <i>{len(session['files'])} file(s) ready!</i>\n\n"
                               "<i>Give this batch a label/title:</i>\nExample: <code>Math Notes Ch3</code>\n\n"
                               "<b>Step 4 of 4:</b> <i>Set max downloads (0 for unlimited):</i>\nExample: <code>100</code>")
        bot.register_next_step_handler(msg, _file_finalize_with_captions, chat_id)
        return
    
    item = _extract_file(message)
    if item:
        file_id, ftype, caption, fname = item
        session['files'].append((file_id, ftype, caption, fname))
        session['captions'].append(caption)
        
        file_num = len(session['files'])
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("📝 Add Caption", callback_data=f"caption_add_{chat_id}_{file_num-1}"),
            types.InlineKeyboardButton("⏭️ Skip Caption", callback_data=f"caption_skip_{chat_id}_{file_num-1}")
        )
        kb.add(types.InlineKeyboardButton("❌ Cancel Upload", callback_data="upload_cancel"))
        
        bot.send_message(chat_id,
                         f"<b>✅ File {file_num} added!</b>\n"
                         f"{TYPE_EMOJI.get(ftype, '📎')} <code>{esc(fname)}</code>\n\n"
                         f"<i>Do you want to add a caption for this file?</i>",
                         reply_markup=kb)
    else:
        bot.reply_to(message,
                     "<i>❓ Not a file. Send document/video/photo/audio.\nType</i> <code>DONE</code> <i>when finished.</i>")
        bot.register_next_step_handler(message, _file_collect, chat_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("caption_"))
def caption_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ Not authorized.", show_alert=True)
        return
    
    data = call.data
    chat_id = call.message.chat.id
    
    if data == "upload_cancel":
        upload_sessions.pop(chat_id, None)
        bot.edit_message_text("❌ <b>Upload cancelled.</b>", chat_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return
    
    parts = data.split("_")
    action = parts[1]
    file_chat_id = int(parts[2])
    file_index = int(parts[3])
    
    session = upload_sessions.get(file_chat_id)
    if not session:
        bot.answer_callback_query(call.id, "Session expired!", show_alert=True)
        return
    
    if action == "add":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, 
                               f"📝 <b>Add Caption for File {file_index + 1}</b>\n\n"
                               f"<i>Send me the caption text for this file.</i>\n"
                               f"<i>Type /skip to skip this caption.</i>")
        bot.register_next_step_handler(msg, _save_caption, file_chat_id, file_index)
    elif action == "skip":
        bot.answer_callback_query(call.id)
        _continue_upload(file_chat_id, file_index, call.message)

def _save_caption(message, chat_id, file_index):
    if _is_cancel(message):
        return
    
    session = upload_sessions.get(chat_id)
    if not session:
        return
    
    if message.text and message.text.strip().lower() == "/skip":
        caption = ""
    else:
        caption = message.text.strip() if message.text else ""
    
    if file_index < len(session['captions']):
        session['captions'][file_index] = caption
    
    file_id, ftype, _, fname = session['files'][file_index]
    session['files'][file_index] = (file_id, ftype, caption, fname)
    
    _continue_upload(chat_id, file_index, message)

def _continue_upload(chat_id, file_index, msg):
    session = upload_sessions.get(chat_id)
    if not session:
        return
    
    if file_index == len(session['files']) - 1:
        bot.send_message(chat_id, 
                         f"<b>✅ Caption saved for file {file_index + 1}!</b>\n\n"
                         f"<i>You have added {len(session['files'])} file(s).</i>\n"
                         f"<i>Type</i> <code>DONE</code> <i>when finished or send more files.</i>")
        bot.register_next_step_handler(msg, _file_collect, chat_id)
    else:
        next_index = file_index + 1
        next_file = session['files'][next_index]
        next_fname = next_file[3]
        
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("📝 Add Caption", callback_data=f"caption_add_{chat_id}_{next_index}"),
            types.InlineKeyboardButton("⏭️ Skip Caption", callback_data=f"caption_skip_{chat_id}_{next_index}")
        )
        kb.add(types.InlineKeyboardButton("❌ Cancel Upload", callback_data="upload_cancel"))
        
        bot.send_message(chat_id,
                         f"📁 <b>File {next_index + 1}</b>\n"
                         f"{TYPE_EMOJI.get(next_file[1], '📎')} <code>{esc(next_fname)}</code>\n\n"
                         f"<i>Do you want to add a caption for this file?</i>",
                         reply_markup=kb)

def _file_finalize_with_captions(message, chat_id):
    if not is_admin(message.chat.id):
        return
    if _is_cancel(message):
        upload_sessions.pop(chat_id, None)
        return
    
    session = upload_sessions.get(chat_id)
    if not session:
        return
    
    label = message.text.strip() if message.text else "File Pack"
    
    max_hits = 0
    if message.text:
        try:
            parts = message.text.split()
            if len(parts) > 1:
                try:
                    max_hits = int(parts[-1])
                    label = " ".join(parts[:-1])
                except:
                    max_hits = 0
        except:
            max_hits = 0
    
    if max_hits == 0 and label != message.text.strip():
        msg = bot.send_message(chat_id,
                               "<b>Step 4 of 4:</b> <i>Set max downloads (0 for unlimited):</i>\n"
                               "Example: <code>100</code>")
        bot.register_next_step_handler(msg, _set_max_hits, chat_id, label, session)
        return
    
    _finalize_upload(chat_id, label, max_hits, session)

def _set_max_hits(message, chat_id, label, session):
    if _is_cancel(message):
        upload_sessions.pop(chat_id, None)
        return
    
    try:
        max_hits = int(message.text.strip())
    except:
        max_hits = 0
    
    _finalize_upload(chat_id, label, max_hits, session)

def _finalize_upload(chat_id, label, max_hits, session):
    key = hashlib.md5(f"f{time.time()}{chat_id}".encode()).hexdigest()[:10]
    
    files_to_save = []
    for file_id, ftype, caption, fname in session['files']:
        files_to_save.append((file_id, ftype, caption, fname))
    
    save_files(key, files_to_save, max_hits=max_hits, is_premium=session['is_premium'])
    
    conn = get_conn()
    conn.execute("UPDATE files SET label=?, max_hits=?, is_premium=? WHERE key=?", 
                 (label, max_hits, session['is_premium'], key))
    conn.commit()
    conn.close()
    
    upload_sessions.pop(chat_id, None)
    
    _send_success_with_captions(chat_id, key, label, len(session['files']), session['is_premium'], max_hits, session['captions'])

def _send_success_with_captions(chat_id, key, label, count, is_premium, max_hits, captions):
    bot_name = bot.get_me().username
    link = f"https://t.me/{bot_name}?start={key}"
    premium_badge = " ⭐ PREMIUM" if is_premium else ""
    limit_info = f"\n<b>🔢 Max Downloads:</b> <code>{max_hits if max_hits > 0 else 'Unlimited'}</code>"
    
    caption_preview = ""
    if any(captions):
        caption_preview = "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n<b>📝 Captions:</b>\n"
        for i, cap in enumerate(captions, 1):
            if cap:
                caption_preview += f"{i}. {esc(cap[:50])}{'...' if len(cap) > 50 else ''}\n"
    
    bot.send_message(chat_id,
                     "╔══════════════════════╗\n║   🎉  <b>UPLOAD SUCCESS!</b>    ║\n╚══════════════════════╝\n\n"
                     f"<b>🏷️ Label:</b> <i>{esc(label)}</i>{premium_badge}\n"
                     f"<b>📦 Items:</b> <code>{count}</code>{limit_info}\n"
                     f"<b>🔑 Key:</b> <code>{key}</code>\n"
                     f"{caption_preview}\n"
                     "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                     f"<b>🔗 Share Link:</b>\n<code>{link}</code>\n"
                     "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                     "<i>Tap the link to copy &amp; share</i>",
                     reply_markup=get_admin_reply_keyboard())
    log_event("file_upload", chat_id, key)

def _send_success(message, key, label, count, is_premium=0, max_hits=0):
    bot_name = bot.get_me().username
    link = f"https://t.me/{bot_name}?start={key}"
    premium_badge = " ⭐ PREMIUM" if is_premium else ""
    limit_info = f"\n<b>🔢 Max Downloads:</b> <code>{max_hits if max_hits > 0 else 'Unlimited'}</code>"

    bot.send_message(message.chat.id,
                     "╔══════════════════════╗\n║   🎉  <b>UPLOAD SUCCESS!</b>    ║\n╚══════════════════════╝\n\n"
                     f"<b>🏷️ Label:</b> <i>{esc(label)}</i>{premium_badge}\n"
                     f"<b>📦 Items:</b> <code>{count}</code>{limit_info}\n"
                     f"<b>🔑 Key:</b> <code>{key}</code>\n\n"
                     "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                     f"<b>🔗 Share Link:</b>\n<code>{link}</code>\n"
                     "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                     "<i>Tap the link to copy &amp; share</i>",
                     reply_markup=get_admin_reply_keyboard())
    log_event("file_upload", message.chat.id, key)

def _extract_file(message):
    if message.document:
        return (message.document.file_id, "document", message.caption or "", message.document.file_name or "Document")
    if message.video:
        return (message.video.file_id, "video", message.caption or "", message.video.file_name or "Video")
    if message.photo:
        return (message.photo[-1].file_id, "photo", message.caption or "", "Photo")
    if message.audio:
        return (message.audio.file_id, "audio", message.caption or "", message.audio.title or "Audio")
    if message.voice:
        return (message.voice.file_id, "voice", "", "Voice Message")
    return None

def _is_cancel(message):
    if message.text and message.text.strip().lower() in ("/cancel", "cancel"):
        kb = get_admin_reply_keyboard() if is_admin(message.chat.id) else get_user_reply_keyboard(message.chat.id)
        bot.send_message(message.chat.id, "❌ <b>Cancelled.</b>", reply_markup=kb)
        return True
    return False

# ─────────────────────────────────────────────
#  VERIFY & DELIVER
# ─────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("verify_"))
def verify_callback(call):
    file_key = call.data[7:]
    user_id = call.from_user.id
    upsert_user(call.from_user)

    if is_banned(user_id):
        bot.answer_callback_query(call.id, "🚫 You are banned.", show_alert=True)
        return

    files = get_files(file_key)
    if not files:
        bot.answer_callback_query(call.id, "❌ File not found or expired.", show_alert=True)
        return

    if files[0]["expires"] and time.time() > files[0]["expires"]:
        bot.answer_callback_query(call.id, "⌛ This link has expired.", show_alert=True)
        return

    hits, max_hits = get_file_hits(file_key)
    if max_hits > 0 and hits >= max_hits:
        bot.answer_callback_query(call.id, "🚫 This file has reached its download limit.", show_alert=True)
        return

    if files[0]["is_premium"] == 1 and not (is_premium(user_id) or is_admin(user_id)):
        bot.answer_callback_query(call.id, "⭐ This is a PREMIUM file! Upgrade to access.", show_alert=True)
        return

    all_channels = [FIXED_CHANNEL, FIXED_GROUP] + [r["username"] for r in get_channels()]
    not_joined = []
    for uname in all_channels:
        if uname.startswith("+"):
            continue
        try:
            status = bot.get_chat_member(f"@{uname}", user_id).status
            if status not in ("member", "administrator", "creator"):
                not_joined.append(uname)
        except Exception as e:
            log.warning(f"Channel check failed @{uname}: {e}")
            bot.answer_callback_query(call.id, f"⚠️ Bot not admin in @{uname}.", show_alert=True)
            return

    if not_joined:
        bot.answer_callback_query(call.id,
                                  f"❌ You haven't joined: {', '.join('@' + u for u in not_joined)}", show_alert=True)
        return

    try:
        bot.answer_callback_query(call.id, "✅ Verified! Sending your file(s)…")
        for row in files:
            _send_file(user_id, row["file_id"], row["type"], row["caption"])
            time.sleep(0.3)
        increment_hits(file_key)

        conn = get_conn()
        conn.execute("UPDATE users SET files_recv=files_recv+1 WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()

        log_event("file_delivered", user_id, file_key)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        bot.send_message(user_id,
                         "┌──────────────────────┐\n│  ✅  <b>ACCESS GRANTED!</b>     │\n└──────────────────────┘\n\n"
                         "<i>Your file(s) have been sent above</i> ☝️\n\n"
                         "━━━━━━━━━━━━━━━━━━━━━━━\n<b>💡 Share this bot with friends!</b>\n━━━━━━━━━━━━━━━━━━━━━━━",
                         reply_markup=get_user_reply_keyboard(user_id))
    except Exception as e:
        log.error(f"Delivery error: {e}")
        bot.send_message(user_id, "<i>⚠️ Error sending file. Please try the link again.</i>")

def _send_file(chat_id, file_id, f_type, caption):
    cap = caption or ""
    if f_type == "document":
        bot.send_document(chat_id, file_id, caption=cap)
    elif f_type == "video":
        bot.send_video(chat_id, file_id, caption=cap)
    elif f_type == "photo":
        bot.send_photo(chat_id, file_id, caption=cap)
    elif f_type == "audio":
        bot.send_audio(chat_id, file_id, caption=cap)
    elif f_type == "voice":
        bot.send_voice(chat_id, file_id)
    elif f_type == "text":
        bot.send_message(chat_id, file_id)

# ─────────────────────────────────────────────
#  ADMIN TEXT COMMANDS WITH EXPIRY
# ─────────────────────────────────────────────
@bot.message_handler(commands=["setfile"])
@private_only
@admin_only
def cmd_setfile(message):
    _upload_ask_type(message.chat.id)

@bot.message_handler(commands=["add"])
@private_only
@admin_only
def cmd_add(message):
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message,
                     "📌 <b>Usage:</b>\n"
                     "<code>/add Button Name @username [time]</code>\n\n"
                     "<b>Examples:</b>\n"
                     "<code>/add My Channel @channel 1d</code> — Expires in 1 day\n"
                     "<code>/add VIP Channel @vip 2h</code> — Expires in 2 hours\n"
                     "<code>/add Permanent @perm</code> — No expiry\n\n"
                     "<b>Time formats:</b>\n"
                     "<code>1d</code> = 1 day | <code>2h</code> = 2 hours\n"
                     "<code>30m</code> = 30 minutes | <code>45s</code> = 45 seconds",
                     reply_markup=get_admin_reply_keyboard())
        return
    
    # Check if time parameter is provided
    time_param = None
    button_name_parts = []
    username = None
    
    # Check last part for time format
    last_part = parts[-1]
    if re.match(r'^\d+[dhms]$', last_part.lower()):
        time_param = last_part
        username = parts[-2]
        button_name = " ".join(parts[1:-2])
    else:
        username = parts[-1]
        button_name = " ".join(parts[1:-1])
    
    # Parse username
    username_key, final_url = parse_channel_input(username)
    
    # Parse time if provided
    duration_seconds = 0
    if time_param:
        duration_seconds = parse_time_string(time_param)
        if duration_seconds == 0:
            bot.reply_to(message, "❌ <b>Invalid time format!</b>\n\nUse: 1d, 2h, 30m, 45s", 
                         reply_markup=get_admin_reply_keyboard())
            return
    
    # Add channel with expiry
    expires_at = add_channel_with_expiry(username_key, button_name, message.from_user.id, final_url, duration_seconds)
    
    note = "<i>⚠️ Private link — membership check skipped.</i>" if username_key.startswith("+") else ""
    
    if expires_at > 0:
        expiry_text = f"⏰ Expires in: {format_time_duration(duration_seconds)}"
        auto_remove_note = "\n\n<i>✅ Channel will be automatically removed after expiry!</i>"
    else:
        expiry_text = "♾️ No expiry (permanent)"
        auto_remove_note = ""
    
    bot.reply_to(message,
                 f"<b>✅ Channel Added!</b>\n\n"
                 f"<b>🏷️ Button:</b> <i>{esc(button_name)}</i>\n"
                 f"<b>🔗 Link:</b> <code>{final_url}</code>\n"
                 f"<b>⏰ Status:</b> {expiry_text}\n"
                 f"{note}{auto_remove_note}",
                 reply_markup=get_admin_reply_keyboard())

@bot.message_handler(commands=["remove"])
@private_only
@admin_only
def cmd_remove(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "<i>Usage:</i> <code>/remove @username</code>", reply_markup=get_admin_reply_keyboard())
        return
    username_key, _ = parse_channel_input(parts[1])
    remove_channel(username_key)
    bot.reply_to(message, f"<b>🗑️ Removed</b> <code>{username_key}</code>", reply_markup=get_admin_reply_keyboard())

@bot.message_handler(commands=["delkey", "delfile"])
@private_only
@admin_only
def cmd_delete_key(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "<b>Usage:</b> <code>/delkey &lt;key&gt;</code>\n\nExample: <code>/delkey 8551188a46</code>",
                     reply_markup=get_admin_reply_keyboard())
        return

    key = parts[1].strip()
    files = get_files(key)
    if not files:
        bot.reply_to(message, f"❌ <b>Key not found:</b> <code>{key}</code>", reply_markup=get_admin_reply_keyboard())
        return

    label = files[0]["label"] or "Unknown"
    delete_file_key(key)
    bot.reply_to(message,
                 f"🗑️ <b>File Deleted!</b>\n\n"
                 f"<b>Key:</b> <code>{key}</code>\n"
                 f"<b>Label:</b> <i>{esc(label)}</i>",
                 reply_markup=get_admin_reply_keyboard())

@bot.message_handler(commands=["delall"])
@private_only
@admin_only
def cmd_delete_all(message):
    keys = list_all_keys()
    if not keys:
        bot.reply_to(message, "📂 <b>No files to delete!</b>", reply_markup=get_admin_reply_keyboard())
        return

    count = len(keys)
    delete_all_files()
    bot.reply_to(message,
                 f"🗑️ <b>All Files Deleted!</b>\n\n"
                 f"<b>Total files removed:</b> <code>{count}</code>",
                 reply_markup=get_admin_reply_keyboard())

@bot.message_handler(commands=["link"])
@private_only
@admin_only
def cmd_get_link(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "<b>Usage:</b> <code>/link &lt;key&gt;</code>\n\nExample: <code>/link 8551188a46</code>",
                     reply_markup=get_admin_reply_keyboard())
        return

    key = parts[1].strip()
    files = get_files(key)
    if not files:
        bot.reply_to(message, f"❌ <b>Key not found:</b> <code>{key}</code>", reply_markup=get_admin_reply_keyboard())
        return

    bot_name = bot.get_me().username
    link = f"https://t.me/{bot_name}?start={key}"
    label = files[0]["label"] or "No label"

    bot.reply_to(message,
                 f"🔗 <b>File Link Generated!</b>\n\n"
                 f"<b>🏷️ Label:</b> <i>{esc(label)}</i>\n"
                 f"<b>🔑 Key:</b> <code>{key}</code>\n\n"
                 f"<b>📎 Share Link:</b>\n<code>{link}</code>",
                 reply_markup=get_admin_reply_keyboard())

@bot.message_handler(commands=["files"])
@private_only
@admin_only
def cmd_list_files(message):
    reply_my_files(message)

@bot.message_handler(commands=["ban"])
@private_only
@admin_only
def cmd_ban(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "<i>Usage:</i> <code>/ban &lt;user_id&gt;</code>", reply_markup=get_admin_reply_keyboard())
        return
    try:
        uid = int(parts[1])
        ban_user(uid)
        bot.reply_to(message, f"<b>🚫 User</b> <code>{uid}</code> <b>banned.</b>", reply_markup=get_admin_reply_keyboard())
        try:
            bot.send_message(uid, "🚫 <b>You have been banned from this bot.</b>")
        except:
            pass
    except ValueError:
        bot.reply_to(message, "❌ <i>Invalid user ID.</i>", reply_markup=get_admin_reply_keyboard())

@bot.message_handler(commands=["unban"])
@private_only
@admin_only
def cmd_unban(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "<i>Usage:</i> <code>/unban &lt;user_id&gt;</code>", reply_markup=get_admin_reply_keyboard())
        return
    try:
        uid = int(parts[1])
        unban_user(uid)
        bot.reply_to(message, f"<b>✅ User</b> <code>{uid}</code> <b>unbanned.</b>", reply_markup=get_admin_reply_keyboard())
        try:
            bot.send_message(uid, "✅ <b>You have been unbanned.</b>")
        except:
            pass
    except ValueError:
        bot.reply_to(message, "❌ <i>Invalid user ID.</i>", reply_markup=get_admin_reply_keyboard())

@bot.message_handler(commands=["userinfo"])
@private_only
@admin_only
def cmd_userinfo(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "<i>Usage:</i> <code>/userinfo &lt;user_id&gt;</code>", reply_markup=get_admin_reply_keyboard())
        return
    try:
        uid = int(parts[1])
        user = get_user_full_details(uid)
        if not user:
            bot.reply_to(message, "❌ <i>User not found.</i>", reply_markup=get_admin_reply_keyboard())
            return
        card = format_user_card(user)
        bot.reply_to(message, card, reply_markup=get_admin_reply_keyboard())
    except ValueError:
        bot.reply_to(message, "❌ <i>Invalid user ID.</i>", reply_markup=get_admin_reply_keyboard())

@bot.message_handler(commands=["stats"])
@private_only
@admin_only
def cmd_stats(message):
    s = get_stats()
    bot.reply_to(message,
                 f"📊 <b>Stats</b>\n"
                 f"<b>Users:</b> <code>{s['users']}</code> <i>(+{s['new_today']} today)</i>\n"
                 f"<b>Premium:</b> <code>{s['premium']}</code>\n"
                 f"<b>Files:</b> <code>{s['files']}</code>\n"
                 f"<b>Served:</b> <code>{s['served']}</code>\n"
                 f"<b>Banned:</b> <code>{s['banned']}</code>",
                 reply_markup=get_admin_reply_keyboard())

@bot.message_handler(commands=["premium"])
@private_only
@admin_only
def cmd_give_premium(message):
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message,
                     "⭐ <b>Give Premium Access</b>\n\n"
                     "<code>/premium &lt;user_id&gt; &lt;days&gt;</code>\n\n"
                     "<b>Examples:</b>\n"
                     "<code>/premium 123456789 30</code> — 30 days\n"
                     "<code>/premium 123456789 0</code> — Lifetime\n\n"
                     "<i>Use 0 days for lifetime premium</i>",
                     reply_markup=get_admin_reply_keyboard())
        return

    try:
        user_id = int(parts[1])
        days = int(parts[2])

        set_premium(user_id, days, message.from_user.id)

        if days == 0:
            expiry_text = "LIFETIME ⭐"
        else:
            expiry_text = f"{days} days"

        bot.reply_to(message,
                     f"✅ <b>Premium Activated!</b>\n\n"
                     f"<b>User:</b> <code>{user_id}</code>\n"
                     f"<b>Duration:</b> {expiry_text}\n\n"
                     f"<i>User can now forward messages and access premium files.</i>",
                     reply_markup=get_admin_reply_keyboard())

        try:
            bot.send_message(user_id,
                             f"🎉 <b>CONGRATULATIONS!</b> 🎉\n\n"
                             f"You have been upgraded to <b>PREMIUM</b>!\n\n"
                             f"<b>Duration:</b> {expiry_text}\n\n"
                             f"<b>Premium Features:</b>\n"
                             f"• Forward messages from bot\n"
                             f"• Access premium files\n"
                             f"• Priority support\n\n"
                             f"Thanks for using @{OWNER_USERNAME}'s bot! 💎",
                             reply_markup=get_user_reply_keyboard(user_id))
        except:
            pass

    except ValueError:
        bot.reply_to(message, "❌ <i>Invalid user ID or days!</i>", reply_markup=get_admin_reply_keyboard())

@bot.message_handler(commands=["removepremium"])
@private_only
@admin_only
def cmd_remove_premium(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "<b>Usage:</b> <code>/removepremium &lt;user_id&gt;</code>", reply_markup=get_admin_reply_keyboard())
        return

    try:
        user_id = int(parts[1])
        remove_premium(user_id)
        bot.reply_to(message, f"✅ <b>Premium removed for</b> <code>{user_id}</code>", reply_markup=get_admin_reply_keyboard())
        try:
            bot.send_message(user_id, f"⚠️ <b>Your premium access has expired!</b>\n\nContact @{OWNER_USERNAME} to renew. 💎")
        except:
            pass
    except ValueError:
        bot.reply_to(message, "❌ <i>Invalid user ID!</i>", reply_markup=get_admin_reply_keyboard())

@bot.message_handler(commands=["addadmin"])
@private_only
@admin_only
def cmd_addadmin(message):
    if not is_super_admin(message.from_user.id):
        bot.reply_to(message, "⛔ <b>Only super admins can add new admins.</b>", reply_markup=get_admin_reply_keyboard())
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message,
                     "<b>Usage:</b> <code>/addadmin &lt;user_id&gt;</code>\n\n"
                     "<i>Ask the user to send /start to the bot first.</i>", reply_markup=get_admin_reply_keyboard())
        return
    try:
        new_id = int(parts[1])
        if new_id in SUPER_ADMIN_IDS:
            bot.reply_to(message, "<i>ℹ️ Already a super admin.</i>", reply_markup=get_admin_reply_keyboard())
            return
        if is_admin(new_id):
            bot.reply_to(message, "<i>ℹ️ Already an admin.</i>", reply_markup=get_admin_reply_keyboard())
            return
        conn = get_conn()
        row = conn.execute("SELECT username FROM users WHERE user_id=?", (new_id,)).fetchone()
        conn.close()
        uname = row["username"] if row else ""
        add_admin(new_id, uname, message.from_user.id)
        bot.reply_to(message,
                     f"<b>✅ Admin added!</b>\n\n"
                     f"<b>👤 ID:</b> <code>{new_id}</code>\n"
                     f"<b>Username:</b> @{esc(uname) if uname else 'Unknown'}",
                     reply_markup=get_admin_reply_keyboard())
        try:
            bot.send_message(new_id,
                             "👑 <b>You have been promoted to Admin!</b>\n\n"
                             f"<i>Added by:</i> <code>{message.from_user.id}</code>\n\n"
                             "<i>Use /start to open the Admin Panel.</i>",
                             reply_markup=get_admin_reply_keyboard())
        except:
            pass
    except ValueError:
        bot.reply_to(message, "❌ <i>Invalid user ID.</i>", reply_markup=get_admin_reply_keyboard())

@bot.message_handler(commands=["removeadmin"])
@private_only
@admin_only
def cmd_removeadmin(message):
    if not is_super_admin(message.from_user.id):
        bot.reply_to(message, "⛔ <b>Only super admins can remove admins.</b>", reply_markup=get_admin_reply_keyboard())
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "<b>Usage:</b> <code>/removeadmin &lt;user_id&gt;</code>", reply_markup=get_admin_reply_keyboard())
        return
    try:
        target = int(parts[1])
        if target in SUPER_ADMIN_IDS:
            bot.reply_to(message, "⛔ <b>Cannot remove a super admin.</b>", reply_markup=get_admin_reply_keyboard())
            return
        if not is_admin(target):
            bot.reply_to(message, "❌ <i>Not an admin.</i>", reply_markup=get_admin_reply_keyboard())
            return
        remove_admin(target)
        bot.reply_to(message, f"<b>🗑️ Admin</b> <code>{target}</code> <b>removed.</b>", reply_markup=get_admin_reply_keyboard())
        try:
            bot.send_message(target, "<i>ℹ️ Your admin access has been revoked.</i>", reply_markup=get_user_reply_keyboard(target))
        except:
            pass
    except ValueError:
        bot.reply_to(message, "❌ <i>Invalid user ID.</i>", reply_markup=get_admin_reply_keyboard())

@bot.message_handler(commands=["listadmins"])
@private_only
@admin_only
def cmd_listadmins(message):
    db_admins = list_admins()
    lines = ["👑 <b>Admin List</b>\n", "<b>🔐 Super Admins (permanent):</b>"]
    for sid in SUPER_ADMIN_IDS:
        lines.append(f"  • <code>{sid}</code>")
    lines.append("\n<b>👮 Panel Admins:</b>")
    if db_admins:
        for row in db_admins:
            uname = f"@{esc(row['username'])}" if row["username"] else "Unknown"
            dt = datetime.fromtimestamp(row['added_at']).strftime('%d %b %Y')
            lines.append(f"  • <code>{row['user_id']}</code> {uname} <i>(added {dt})</i>")
    else:
        lines.append("  <i>None added yet.</i>")
    bot.reply_to(message, "\n".join(lines), reply_markup=get_admin_reply_keyboard())

@bot.message_handler(commands=["help"])
@private_only
@admin_only
def cmd_help(message):
    bot.reply_to(message,
                 "📋 <b>Admin Commands</b>\n\n"
                 "<b>📤 File Management</b>\n"
                 "<code>/setfile</code> — Upload file(s)\n"
                 "<code>/delkey &lt;key&gt;</code> — Delete a file\n"
                 "<code>/delall</code> — Delete all files\n"
                 "<code>/link &lt;key&gt;</code> — Get file link\n"
                 "<code>/files</code> — List all files\n\n"
                 "<b>📡 Channel Management (NEW!)</b>\n"
                 "<code>/add &lt;name&gt; @username [time]</code> — Add channel with expiry\n"
                 "<code>/remove @username</code> — Remove channel\n\n"
                 "<b>⏰ Time Formats:</b>\n"
                 "<code>1d</code> = 1 day | <code>2h</code> = 2 hours\n"
                 "<code>30m</code> = 30 minutes | <code>45s</code> = 45 seconds\n\n"
                 "<b>⭐ Premium Management</b>\n"
                 "<code>/premium &lt;id&gt; &lt;days&gt;</code> — Give premium (0=lifetime)\n"
                 "<code>/removepremium &lt;id&gt;</code> — Remove premium\n\n"
                 "<b>👥 User Management</b>\n"
                 "<code>/ban &lt;id&gt;</code> — Ban user\n"
                 "<code>/unban &lt;id&gt;</code> — Unban user\n"
                 "<code>/userinfo &lt;id&gt;</code> — User details\n\n"
                 "<b>👑 Admin Management</b>\n"
                 "<code>/addadmin &lt;id&gt;</code> — Add admin\n"
                 "<code>/removeadmin &lt;id&gt;</code> — Remove admin\n"
                 "<code>/listadmins</code> — List all admins\n\n"
                 "<b>📣 Broadcast</b>\n"
                 "<code>/broadcast &lt;text&gt;</code> — Send to all users\n\n"
                 "<b>📊 Other</b>\n"
                 "<code>/stats</code> — Bot statistics\n"
                 "<code>/help</code> — This menu\n\n"
                 "<b>📝 New Features:</b>\n"
                 "<i>• Channel auto-expiry system\n"
                 "• Caption support for files\n"
                 "• Premium user management</i>",
                 reply_markup=get_admin_reply_keyboard())

# ─────────────────────────────────────────────
#  BROADCAST
# ─────────────────────────────────────────────
@bot.message_handler(commands=["broadcast"])
@private_only
@admin_only
def cmd_broadcast_text(message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "<i>Usage:</i> <code>/broadcast &lt;message&gt;</code>", reply_markup=get_admin_reply_keyboard())
        return
    _do_text_broadcast(message, args[1])

def do_broadcast(message):
    if message.text and message.text.strip().lower() == "cancel":
        bot.send_message(message.chat.id, "❌ <b>Broadcast cancelled.</b>", reply_markup=get_admin_reply_keyboard())
        return
    _do_broadcast_message(message)

def _do_text_broadcast(message, text):
    uids = get_all_user_ids()
    ok = fail = 0
    sm = bot.reply_to(message, f"<i>📣 Broadcasting to {len(uids)} users…</i>")
    for uid in uids:
        try:
            bot.send_message(uid, text)
            ok += 1
        except:
            fail += 1
        time.sleep(0.05)
    bot.edit_message_text(
        f"<b>✅ Broadcast done!</b>\n<i>Sent:</i> <code>{ok}</code> <i>| Failed:</i> <code>{fail}</code>",
        sm.chat.id, sm.message_id)
    log_event("broadcast", message.chat.id, f"sent={ok}")

def _do_broadcast_message(message):
    uids = get_all_user_ids()
    ok = fail = 0
    sm = bot.send_message(message.chat.id, f"<i>📣 Broadcasting to {len(uids)} users…</i>")
    for uid in uids:
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            ok += 1
        except:
            fail += 1
        time.sleep(0.05)
    bot.edit_message_text(
        f"<b>✅ Broadcast done!</b>\n<i>Sent:</i> <code>{ok}</code> <i>| Failed:</i> <code>{fail}</code>",
        sm.chat.id, sm.message_id)

# ─────────────────────────────────────────────
#  FALLBACK
# ─────────────────────────────────────────────
@bot.message_handler(func=lambda m: True)
@private_only
@not_banned
@rate_limited
def fallback(message):
    upsert_user(message.from_user)
    if is_admin(message.chat.id):
        bot.reply_to(message, "🤷 <i>Unknown command. Use the buttons below 👇</i>", reply_markup=get_admin_reply_keyboard())
    else:
        bot.reply_to(message,
                     "ℹ️ <b>Use a valid file link to get files.</b>\n\n"
                     f"<i>Example:</i> <code>https://t.me/{bot.get_me().username}?start=8551188a46</code>\n\n"
                     "<i>Or use the buttons below 👇</i>",
                     reply_markup=get_user_reply_keyboard(message.from_user.id))

# ─────────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    log.info(f"🤖 Pro File Store Bot {BOT_VERSION} starting…")
    
    # Start background expiry checker
    start_expiry_checker()
    
    try:
        me = bot.get_me()
        log.info(f"Bot: @{me.username} ({me.first_name})")
    except Exception as e:
        log.critical(f"Failed to connect: {e}")
        exit(1)

    bot.infinity_polling(
        timeout=30,
        long_polling_timeout=20,
        logger_level=logging.WARNING,
        allowed_updates=["message", "callback_query", "chat_member"]
    )