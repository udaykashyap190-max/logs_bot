import sqlite3
from datetime import datetime


DATABASE = "database.db"


def get_connection():
    return sqlite3.connect(DATABASE)
    

def init_database():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            user_id INTEGER PRIMARY KEY,

            username TEXT,

            first_name TEXT,

            status TEXT NOT NULL DEFAULT 'pending',

            joined_at TEXT NOT NULL

        )
    """)

    conn.commit()

    conn.close()


def add_user(
    user_id,
    username,
    first_name
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (
            user_id,
            username,
            first_name,
            status,
            joined_at
        )

        VALUES (?, ?, ?, 'pending', ?)

        ON CONFLICT(user_id)
        DO UPDATE SET

            username = excluded.username,

            first_name = excluded.first_name
    """, (

        user_id,

        username,

        first_name,

        datetime.now().isoformat()

    ))

    conn.commit()

    conn.close()


def get_user_status(
    user_id
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT status
        FROM users
        WHERE user_id = ?
    """, (

        user_id,

    ))

    result = cursor.fetchone()

    conn.close()


    if result is None:

        return None


    return result[0]


def set_user_status(
    user_id,
    status
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET status = ?
        WHERE user_id = ?
    """, (

        status,

        user_id

    ))

    conn.commit()

    conn.close()


def get_pending_users():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            user_id,
            username,
            first_name,
            joined_at

        FROM users

        WHERE status = 'pending'

        ORDER BY joined_at ASC
    """)

    users = cursor.fetchall()

    conn.close()

    return users


def get_approved_users():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            user_id,
            username,
            first_name,
            joined_at

        FROM users

        WHERE status = 'approved'

        ORDER BY joined_at DESC
    """)

    users = cursor.fetchall()

    conn.close()

    return users


def get_blocked_users():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            user_id,
            username,
            first_name,
            joined_at

        FROM users

        WHERE status = 'blocked'

        ORDER BY joined_at DESC
    """)

    users = cursor.fetchall()

    conn.close()

    return users


def is_approved(
    user_id,
    owner_id
):

    # Admin always has access
    if user_id == owner_id:

        return True


    status = get_user_status(
        user_id
    )


    return status == "approved"