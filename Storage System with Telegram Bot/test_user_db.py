from user_db import init_db, register_user, get_user

# Step 1: Initialize the database
init_db()

# Step 2: Register a test user
register_user(
    telegram_id=123456789,
    email="give your email here",
    gdrive_cred="credentials/drive1_credentials.json",
    gdrive_token="credentials/token_drive1_credentials.json",
    dropbox_token="DROPBOX_ACCESS_TOKEN_HERE"
)

# Step 3: Retrieve and print user info
user = get_user(123456789)
print("Fetched User Info:")
print(f"Telegram ID: {user[0]}")
print(f"Email: {user[1]}")
print(f"Google Drive Cred: {user[2]}")
print(f"Google Drive Token: {user[3]}")
print(f"Dropbox Token: {user[4]}")
