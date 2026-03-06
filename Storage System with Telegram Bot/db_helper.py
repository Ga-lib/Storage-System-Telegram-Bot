import sqlite3

# Initialize the database and create table for storing tokens
def init_db():
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            account_id TEXT PRIMARY KEY,
            google_access_token TEXT,
            google_refresh_token TEXT,
            dropbox_access_token TEXT,
            dropbox_refresh_token TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Store tokens securely in the database
def store_tokens(account_id, google_access_token, google_refresh_token, dropbox_access_token, dropbox_refresh_token):
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO tokens (account_id, google_access_token, google_refresh_token, dropbox_access_token, dropbox_refresh_token)
        VALUES (?, ?, ?, ?, ?)
    ''', (account_id, google_access_token, google_refresh_token, dropbox_access_token, dropbox_refresh_token))
    conn.commit()
    conn.close()

# Retrieve tokens for a specific account
def get_tokens(account_id):
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT google_access_token, google_refresh_token, dropbox_access_token, dropbox_refresh_token
        FROM tokens WHERE account_id = ?
    ''', (account_id,))
    result = cursor.fetchone()
    conn.close()
    return result if result else None
