
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_active TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def add_or_update_user(user_id:int, username:str=None, first_name:str=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO users(user_id, username, first_name, last_active)
           VALUES (?, ?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(user_id) DO UPDATE SET
             username=excluded.username,
             first_name=excluded.first_name,
             last_active=CURRENT_TIMESTAMP
        """, (user_id, username, first_name)
    )
    conn.commit()
    conn.close()

def get_user_count():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    res = cur.fetchone()[0]
    conn.close()
    return res

def list_user_ids(limit=1000):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]
