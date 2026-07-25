import sqlite3
from datetime import datetime


DATABASE = "database.db"


def get_connection():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_database():

    conn = get_connection()

    cursor = conn.cursor()

    # USERS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            user_id INTEGER PRIMARY KEY,

            username TEXT,

            first_name TEXT,

            status TEXT NOT NULL
                DEFAULT 'pending',

            joined_at TEXT NOT NULL

        )
    """)

    # FILE OWNERSHIP
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_files (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            filename TEXT NOT NULL,

            uploaded_at TEXT NOT NULL,

            UNIQUE(
                user_id,
                filename
            )

        )
    """)

    conn.commit()

    conn.close()


# =========================================================
# USERS
# =========================================================

def save_user(
    user_id,
    username,
    first_name
):

    conn = get_connection()

    cursor = conn.cursor()

    existing = cursor.execute(
        """
        SELECT user_id
        FROM users
        WHERE user_id = ?
        """,
        (
            user_id,
        )
    ).fetchone()

    if existing:

        cursor.execute(
            """
            UPDATE users

            SET username = ?,
                first_name = ?

            WHERE user_id = ?
            """,
            (
                username,
                first_name,
                user_id
            )
        )

    else:

        cursor.execute(
            """
            INSERT INTO users (

                user_id,
                username,
                first_name,
                status,
                joined_at

            )

            VALUES (

                ?,
                ?,
                ?,
                'pending',
                ?

            )
            """,
            (
                user_id,
                username,
                first_name,
                datetime.now().isoformat()
            )
        )

    conn.commit()

    conn.close()


def get_user(
    user_id
):

    conn = get_connection()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE user_id = ?
        """,
        (
            user_id,
        )
    ).fetchone()

    conn.close()

    return user


def get_user_status(
    user_id
):

    user = get_user(
        user_id
    )

    if not user:

        return None

    return user["status"]


def set_user_status(
    user_id,
    status
):

    conn = get_connection()

    conn.execute(
        """
        UPDATE users

        SET status = ?

        WHERE user_id = ?
        """,
        (
            status,
            user_id
        )
    )

    conn.commit()

    conn.close()


# =========================================================
# USER LISTS
# =========================================================

def get_pending_users():

    conn = get_connection()

    users = conn.execute(
        """
        SELECT *

        FROM users

        WHERE status = 'pending'

        ORDER BY joined_at ASC
        """
    ).fetchall()

    conn.close()

    return users


def get_approved_users():

    conn = get_connection()

    users = conn.execute(
        """
        SELECT *

        FROM users

        WHERE status = 'approved'

        ORDER BY joined_at DESC
        """
    ).fetchall()

    conn.close()

    return users


def get_blocked_users():

    conn = get_connection()

    users = conn.execute(
        """
        SELECT *

        FROM users

        WHERE status IN (
            'blocked',
            'rejected'
        )

        ORDER BY joined_at DESC
        """
    ).fetchall()

    conn.close()

    return users


def delete_user(
    user_id
):

    conn = get_connection()

    conn.execute(
        """
        DELETE FROM user_files
        WHERE user_id = ?
        """,
        (
            user_id,
        )
    )

    conn.execute(
        """
        DELETE FROM users
        WHERE user_id = ?
        """,
        (
            user_id,
        )
    )

    conn.commit()

    conn.close()


# =========================================================
# FILE OWNERSHIP
# =========================================================

def add_file_owner(
    user_id,
    filename
):

    conn = get_connection()

    conn.execute(
        """
        INSERT OR IGNORE INTO user_files (

            user_id,
            filename,
            uploaded_at

        )

        VALUES (

            ?,
            ?,
            ?

        )
        """,
        (
            user_id,
            filename,
            datetime.now().isoformat()
        )
    )

    conn.commit()

    conn.close()


def get_user_files(
    user_id
):

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT filename

        FROM user_files

        WHERE user_id = ?

        ORDER BY uploaded_at DESC
        """,
        (
            user_id,
        )
    ).fetchall()

    conn.close()

    return [
        row["filename"]
        for row in rows
    ]


def user_owns_file(
    user_id,
    filename
):

    conn = get_connection()

    row = conn.execute(
        """
        SELECT id

        FROM user_files

        WHERE user_id = ?

        AND filename = ?

        LIMIT 1
        """,
        (
            user_id,
            filename
        )
    ).fetchone()

    conn.close()

    return row is not None


def remove_file_owner(
    user_id,
    filename
):

    conn = get_connection()

    conn.execute(
        """
        DELETE FROM user_files

        WHERE user_id = ?

        AND filename = ?
        """,
        (
            user_id,
            filename
        )
    )

    conn.commit()

    conn.close()


# =========================================================
# USER STATISTICS
# =========================================================

def get_user_file_count(
    user_id
):

    conn = get_connection()

    result = conn.execute(
        """
        SELECT COUNT(*)

        FROM user_files

        WHERE user_id = ?
        """,
        (
            user_id,
        )
    ).fetchone()

    conn.close()

    return result[0]


# =========================================================
# ADMIN STATISTICS
# =========================================================

def get_total_users():

    conn = get_connection()

    result = conn.execute(
        """
        SELECT COUNT(*)
        FROM users
        """
    ).fetchone()

    conn.close()

    return result[0]


def get_pending_count():

    conn = get_connection()

    result = conn.execute(
        """
        SELECT COUNT(*)

        FROM users

        WHERE status = 'pending'
        """
    ).fetchone()

    conn.close()

    return result[0]


def get_approved_count():

    conn = get_connection()

    result = conn.execute(
        """
        SELECT COUNT(*)

        FROM users

        WHERE status = 'approved'
        """
    ).fetchone()

    conn.close()

    return result[0]


def get_blocked_count():

    conn = get_connection()

    result = conn.execute(
        """
        SELECT COUNT(*)

        FROM users

        WHERE status IN (
            'blocked',
            'rejected'
        )
        """
    ).fetchone()

    conn.close()

    return result[0]


def get_total_files():

    conn = get_connection()

    result = conn.execute(
        """
        SELECT COUNT(*)

        FROM user_files
        """
    ).fetchone()

    conn.close()

    return result[0]


# =========================================================
# STARTUP
# =========================================================

init_database()
