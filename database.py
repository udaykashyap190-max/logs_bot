import sqlite3
from pathlib import Path


DB_PATH = Path("database.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Uploaded files table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, filename)
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# USER FUNCTIONS
# =========================================================

def save_user(
    user_id,
    username=None,
    first_name=None
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users
        (
            user_id,
            username,
            first_name
        )
        VALUES (?, ?, ?)

        ON CONFLICT(user_id)
        DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            updated_at = CURRENT_TIMESTAMP
    """, (
        user_id,
        username,
        first_name
    ))

    conn.commit()
    conn.close()


def get_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    user = cursor.fetchone()

    conn.close()

    return user


def get_user_status(user_id):
    user = get_user(user_id)

    if not user:
        return None

    return user["status"]


def set_user_status(
    user_id,
    status
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (
        status,
        user_id
    ))

    conn.commit()
    conn.close()


# =========================================================
# FILE FUNCTIONS
# =========================================================

def add_file_owner(
    user_id,
    filename
):
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO user_files
        (
            user_id,
            filename
        )
        VALUES (?, ?)
    """, (
        user_id,
        filename
    ))

    conn.commit()
    conn.close()


def get_user_files(user_id):
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT filename
        FROM user_files
        WHERE user_id = ?
        ORDER BY uploaded_at DESC
    """, (
        user_id,
    ))

    files = [
        row["filename"]
        for row in cursor.fetchall()
    ]

    conn.close()

    return files


def user_owns_file(
    user_id,
    filename
):
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1
        FROM user_files
        WHERE user_id = ?
        AND filename = ?
        LIMIT 1
    """, (
        user_id,
        filename
    ))

    result = cursor.fetchone()

    conn.close()

    return result is not None


def remove_user_file(
    user_id,
    filename
):
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM user_files
        WHERE user_id = ?
        AND filename = ?
    """, (
        user_id,
        filename
    ))

    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return deleted


# =========================================================
# STATISTICS
# =========================================================

def get_user_file_count(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM user_files
        WHERE user_id = ?
    """, (
        user_id,
    ))

    count = cursor.fetchone()[0]

    conn.close()

    return count


def get_total_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
    """)

    count = cursor.fetchone()[0]

    conn.close()

    return count


def get_approved_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE status = 'approved'
    """)

    count = cursor.fetchone()[0]

    conn.close()

    return count


def get_pending_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE status = 'pending'
    """)

    count = cursor.fetchone()[0]

    conn.close()

    return count


def get_total_files():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM user_files
    """)

    count = cursor.fetchone()[0]

    conn.close()

    return count


# Initialize database when imported
init_db()
