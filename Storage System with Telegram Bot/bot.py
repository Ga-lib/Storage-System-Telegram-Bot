import os
import json
from telegram.request import HTTPXRequest
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from telegram.constants import ChatAction
from google_auth_oauthlib.flow import InstalledAppFlow
from google_drive_service import GoogleDriveService
from dropbox_service import DropboxService
from user_db import init_db, register_user, get_user

# Init DB
init_db()

# Bot Token
BOT_TOKEN = "your bot token here"

# Memory session for tracking things like upload/download choice
user_sessions = {}

# Accounts config
accounts = {
    "acc_1": {
        "email": "your email here",
        "gdrive_cred": "credentials/drive1_credentials.json",
        "gdrive_token": "credentials/token_drive1_credentials.json",
        "dropbox_token": "Your dropbox token here"
    },
    "acc_2": {
        "email": "your email here",
        "gdrive_cred": "credentials/drive2_credentials.json",
        "gdrive_token": "credentials/token_drive2_credentials.json",
        "dropbox_token": "Your dropbox token here"
    },
    "acc_3": {
        "email": "your email here",
        "gdrive_cred": "credentials/drive3_credentials.json",
        "gdrive_token": "credentials/token_drive3_credentials.json",
        "dropbox_token": "Your dropbox token here"
    }
}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Use /register to begin.")

# /register
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Account 1", callback_data="acc_1")],
        [InlineKeyboardButton("Account 2", callback_data="acc_2")],
        [InlineKeyboardButton("Account 3", callback_data="acc_3")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select an account:", reply_markup=reply_markup)

# Account selection handler
async def account_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
       await query.answer()
    except Exception as e:
       print("Callback already answered or invalid:", e)

    account_id = query.data

    if account_id not in accounts:
        await query.edit_message_text("❌ Invalid account.")
        return

    acc = accounts[account_id]
    telegram_id = query.from_user.id
    register_user(telegram_id, acc['email'], acc['gdrive_cred'], acc['gdrive_token'], acc['dropbox_token'])

    keyboard = [
        [InlineKeyboardButton("Connect Google Drive", callback_data=f"connect_gdrive_{account_id}")]
    ]
    await query.edit_message_text(
        f"✅ Registered for {acc['email']}\nNow connect Google Drive:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# Step 1: Send Google OAuth URL to Telegram
async def connect_google_drive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
       await query.answer()
    except Exception as e:
       print("Callback already answered or invalid:", e)
    account_id = query.data.replace("connect_gdrive_", "")
    acc = accounts.get(account_id)

    if not acc:
        await query.edit_message_text("❌ Invalid account.")
        return

    try:
        # Initialize flow
        flow = InstalledAppFlow.from_client_secrets_file(
            acc["gdrive_cred"],
            scopes=[
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/drive.file",
                "https://www.googleapis.com/auth/drive.metadata.readonly"
            ],
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )

        # Get auth URL
        auth_url, _ = flow.authorization_url(prompt='consent')

        # Save flow & account info in user_data
        context.user_data["oauth_flow"] = flow
        context.user_data["account_id"] = account_id

        await query.edit_message_text(
            f"🔐 [Click here to authenticate Google Drive]({auth_url})\n\nAfter that, send me the code you get.",
            parse_mode="Markdown"
        )

    except Exception as e:
        await query.edit_message_text(f"❌ Google Drive auth error: {e}")


async def handle_auth_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    flow = context.user_data.get("oauth_flow")
    account_id = context.user_data.get("account_id")

    if not flow or not account_id:
        await update.message.reply_text("❌ No auth session found. Please use /register again.")
        return

    acc = accounts[account_id]

    try:
        creds = flow.fetch_token(code=code)

        with open(acc["gdrive_token"], "w") as f:
            f.write(flow.credentials.to_json())

        await update.message.reply_text("✅ Google Drive connected successfully!")

        # Clean up session
        context.user_data.pop("oauth_flow", None)
        context.user_data.pop("account_id", None)

    except Exception as e:
        await update.message.reply_text(f"❌ Failed to complete authentication: {e}")


# /storages
async def storages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Not registered.")
        return

    _, email, cred, token, dbx_token = user
    gdrive = GoogleDriveService(email, cred, token)
    dropbox = DropboxService(email, dbx_token)

    g_used, g_total = gdrive.get_storage_info()
    d_used, d_total = dropbox.get_storage_info()

    await update.message.reply_text(
        f"Google Drive: {g_used} / {g_total}\nDropbox: {dropbox.format_size(d_used)} / {dropbox.format_size(d_total)}"
    )

# /list
async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ You are not registered.")
        return

    _, email, cred, token, dbx_token = user
    gdrive = GoogleDriveService(email, cred, token)
    dropbox = DropboxService(email, dbx_token)

    msg = "📁 Google Drive files:\n"
    try:
        page_token = None
        while True:
            response = gdrive.service.files().list(
                pageSize=50,
                fields="nextPageToken, files(id, name)",
                pageToken=page_token
            ).execute()

            for f in response.get("files", []):
                msg += f"- {f['name']}\n"

            page_token = response.get("nextPageToken", None)
            if not page_token:
                break
    except Exception as e:
        msg += f"Error listing Drive files: {e}"

    msg += "\n📦 Dropbox files:\n"
    try:
        result = dropbox.dbx.files_list_folder("", recursive=True)
        for f in result.entries:
            msg += f"- {f.name}\n"
    except Exception as e:
        msg += f"Error listing Dropbox files: {e}"

    await update.message.reply_text(msg if msg.strip() else "No files found.")


# /upload
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📁 Upload to Google Drive", callback_data="upload_gdrive")],
        [InlineKeyboardButton("📦 Upload to Dropbox", callback_data="upload_dropbox")]
    ]
    await update.message.reply_text(
        "Where do you want to upload your file?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# Upload option selection
# Upload destination buttons handler
async def upload_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
       await query.answer()
    except Exception as e:
       print("Callback already answered or invalid:", e)
    telegram_id = query.from_user.id

    # Store user choice: either "upload_gdrive" or "upload_dropbox"
    user_sessions[telegram_id] = user_sessions.get(telegram_id, {})
    user_sessions[telegram_id]["upload_service"] = query.data

    await query.edit_message_text("📤 Now send a file to upload.")


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ You are not registered.")
        return

    _, email, cred, token, dbx_token = user
    gdrive = GoogleDriveService(email, cred, token)
    dropbox = DropboxService(email, dbx_token)

    telegram_id = update.effective_user.id
    upload_target = user_sessions.get(telegram_id, {}).get("upload_service")

    os.makedirs("temp", exist_ok=True)

    if update.message.document:
        doc = update.message.document
        file_path = f"temp/{doc.file_unique_id}_{doc.file_name}"
        telegram_file = await context.bot.get_file(doc.file_id)
        await telegram_file.download_to_drive(file_path)

    elif update.message.photo:
        photo = update.message.photo[-1]
        file_name = f"photo_{photo.file_unique_id}.jpg"
        file_path = f"temp/{file_name}"
        telegram_file = await context.bot.get_file(photo.file_id)
        await telegram_file.download_to_drive(file_path)
    else:
        await update.message.reply_text("❌ Unsupported file type.")
        return

    try:
        if upload_target == "upload_gdrive":
            gdrive.upload_file(file_path)
            await update.message.reply_text("✅ File uploaded to Google Drive.")
            user_sessions[telegram_id]["upload_service"] = None
        elif upload_target == "upload_dropbox":
            dropbox.upload_file(file_path)
            await update.message.reply_text("✅ File uploaded to Dropbox.")
            user_sessions[telegram_id]["upload_service"] = None
        else:
            await update.message.reply_text("❌ Upload destination not selected. Use /upload again.")
    except Exception as e:
        await update.message.reply_text(f"❌ Upload error: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# /download
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("❌ Usage: /download filename.ext")
        return

    filename = " ".join(context.args).strip()
    telegram_id = update.effective_user.id
    user_sessions[telegram_id] = {"download_filename": filename}

    keyboard = [
        [InlineKeyboardButton("📁 Google Drive", callback_data="download_drive")],
        [InlineKeyboardButton("📦 Dropbox", callback_data="download_dropbox")]
    ]
    await update.message.reply_text(
        f"Where do you want to download '{filename}' from?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# Download choice handler (exact format + size)
from telegram.constants import ChatAction
import io
from googleapiclient.http import MediaIoBaseDownload

import io
from telegram import InputFile
from telegram.constants import ChatAction
from googleapiclient.http import MediaIoBaseDownload

async def download_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
       await query.answer()
    except Exception as e:
       print("Callback already answered or invalid:", e)
    telegram_id = query.from_user.id

    user = get_user(telegram_id)
    if not user:
        await query.edit_message_text("❌ You are not registered.")
        return

    _, email, cred, token, dbx_token = user
    gdrive = GoogleDriveService(email, cred, token)
    dropbox = DropboxService(email, dbx_token)

    filename = user_sessions.get(telegram_id, {}).get("download_filename")
    if not filename:
        await query.edit_message_text("❌ No filename found. Use /download <filename> again.")
        return

    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)
    file_path = os.path.join(download_dir, filename)

    await query.message.chat.send_action(action=ChatAction.UPLOAD_DOCUMENT)

    try:
        if query.data == "download_drive":
            g_files = gdrive.service.files().list(
                q=f"name='{filename}'",
                spaces='drive',
                fields="files(id, name)"
            ).execute().get("files", [])

            for file in g_files:
                if file["name"] == filename:
                    request = gdrive.service.files().get_media(fileId=file["id"])
                    fh = io.FileIO(file_path, "wb")
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                    fh.close()

                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        with open(file_path, "rb") as f:
                            await query.message.reply_document(document=InputFile(f, filename=filename))
                        return
            await query.edit_message_text("❌ File not found in Google Drive.")

        elif query.data == "download_dropbox":
            result = dropbox.dbx.files_list_folder("", recursive=True)
            for entry in result.entries:
                if entry.name == filename:
                    metadata, response = dropbox.dbx.files_download(entry.path_display)
                    with open(file_path, "wb") as f:
                        f.write(response.content)

                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        with open(file_path, "rb") as f:
                            await query.message.reply_document(document=InputFile(f, filename=filename))
                        return
            await query.edit_message_text("❌ File not found in Dropbox.")

        else:
            await query.edit_message_text("❌ Invalid selection.")

    except Exception as e:
        await query.edit_message_text(f"❌ Download failed: {e}")




# Set up bot
from telegram.ext import Defaults
from telegram.request import HTTPXRequest

# Create a custom request with longer timeout
custom_request = HTTPXRequest(connect_timeout=20.0, read_timeout=60.0)

app = ApplicationBuilder().token("your bot token here").request(custom_request).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_auth_code))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("register", register))
app.add_handler(CallbackQueryHandler(account_selected, pattern="^acc_"))
app.add_handler(CallbackQueryHandler(connect_google_drive, pattern="^connect_gdrive_"))
app.add_handler(CommandHandler("storages", storages))
app.add_handler(CommandHandler("list", list_files))
app.add_handler(CommandHandler("upload", upload))
app.add_handler(CallbackQueryHandler(upload_choice_handler, pattern="upload_"))  
app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))
app.add_handler(CommandHandler("download", download))
app.add_handler(CallbackQueryHandler(download_choice_handler, pattern="download_"))

app.run_polling()

 