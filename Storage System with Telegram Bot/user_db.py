import sqlite3

DB_NAME = "users.db"

def init_db():
    """Initialize the database with the user table."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        email TEXT,
        gdrive_cred TEXT,
        gdrive_token TEXT,
        dropbox_token TEXT
    )
    """)
    conn.commit()
    conn.close()

def register_user(telegram_id, email, gdrive_cred, gdrive_token, dropbox_token):
    """Register a user (or update if they already exist)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    REPLACE INTO users (telegram_id, email, gdrive_cred, gdrive_token, dropbox_token)
    VALUES (?, ?, ?, ?, ?)""",
    (telegram_id, email, gdrive_cred, gdrive_token, dropbox_token))
    conn.commit()
    conn.close()

def get_user(telegram_id):
    """Get user data by Telegram ID."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()
    conn.close()
    return user
