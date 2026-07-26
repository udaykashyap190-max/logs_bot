# =========================================================
# FILE: database.py
# PART 9H
# Persistent Database Manager
# =========================================================

import os
import sqlite3
from datetime import datetime


# =========================================================
# DATABASE PATH
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE = os.path.join(
    BASE_DIR,
    "database.db"
)


# =========================================================
# CONNECTION
# =========================================================

def get_connection():

    conn = sqlite3.connect(
        DATABASE,

        timeout=30
    )

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_database():

    conn = get_connection()

    cursor = conn.cursor()


    # =====================================================
    # USERS
    # =====================================================

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


    # =====================================================
    # USER FILES
    # =====================================================

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


    # =====================================================
    # PROCESS METADATA
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_processes (

            user_id INTEGER NOT NULL,

            filename TEXT NOT NULL,

            status TEXT NOT NULL
                DEFAULT 'stopped',

            started_at TEXT,

            stopped_at TEXT,

            restart_count INTEGER NOT NULL
                DEFAULT 0,

            exit_code INTEGER,

            updated_at TEXT NOT NULL,

            PRIMARY KEY (
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

    existing = conn.execute(
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

        conn.execute(
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

        conn.execute(
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
        DELETE FROM file_processes
        WHERE user_id = ?
        """,
        (
            user_id,
        )
    )


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


    conn.execute(
        """
        DELETE FROM file_processes

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
# PROCESS METADATA
# =========================================================

def create_process_record(
    user_id,
    filename
):

    now = datetime.now().isoformat()

    conn = get_connection()

    conn.execute(
        """
        INSERT OR IGNORE INTO file_processes (

            user_id,
            filename,
            status,
            updated_at

        )

        VALUES (

            ?,
            ?,
            'stopped',
            ?

        )
        """,
        (
            user_id,
            filename,
            now
        )
    )

    conn.commit()

    conn.close()


def mark_process_started(
    user_id,
    filename,
    restart=False
):

    now = datetime.now().isoformat()

    conn = get_connection()


    create_process_record(

        user_id,

        filename

    )


    if restart:

        conn.execute(
            """
            UPDATE file_processes

            SET status = 'running',

                started_at = ?,

                stopped_at = NULL,

                exit_code = NULL,

                restart_count =
                    restart_count + 1,

                updated_at = ?

            WHERE user_id = ?

            AND filename = ?
            """,
            (
                now,
                now,
                user_id,
                filename
            )
        )


    else:

        conn.execute(
            """
            UPDATE file_processes

            SET status = 'running',

                started_at = ?,

                stopped_at = NULL,

                exit_code = NULL,

                updated_at = ?

            WHERE user_id = ?

            AND filename = ?
            """,
            (
                now,
                now,
                user_id,
                filename
            )
        )


    conn.commit()

    conn.close()


def mark_process_stopped(
    user_id,
    filename,
    exit_code=None
):

    now = datetime.now().isoformat()

    conn = get_connection()

    conn.execute(
        """
        UPDATE file_processes

        SET status = 'stopped',

            stopped_at = ?,

            exit_code = ?,

            updated_at = ?

        WHERE user_id = ?

        AND filename = ?
        """,
        (
            now,
            exit_code,
            now,
            user_id,
            filename
        )
    )

    conn.commit()

    conn.close()


def get_process_record(
    user_id,
    filename
):

    conn = get_connection()

    row = conn.execute(
        """
        SELECT *

        FROM file_processes

        WHERE user_id = ?

        AND filename = ?
        """,
        (
            user_id,
            filename
        )
    ).fetchone()

    conn.close()

    return row


def get_user_process_records(
    user_id
):

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *

        FROM file_processes

        WHERE user_id = ?

        ORDER BY updated_at DESC
        """,
        (
            user_id,
        )
    ).fetchall()

    conn.close()

    return rows


# =========================================================
# STATISTICS
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
