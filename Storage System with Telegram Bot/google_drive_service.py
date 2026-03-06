# google_drive_service.py
import os
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload
from cloud_service import CloudService

SCOPES = [
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]
DEFAULT_CREDENTIALS_FILENAME = "credentials.json"
DEFAULT_TOKEN_FILENAME = "token.json"

class GoogleDriveService(CloudService):
    def __init__(self, account_name="default", cred_file=None, token_file=None):
        self.account_name = account_name
        if cred_file and token_file:
            self.creds = self.get_credentials_multi(cred_file, token_file)
        else:
            self.creds = self.get_credentials_single()
        self.service = build("drive", "v3", credentials=self.creds)

    def get_credentials_single(self):
        creds = None
        if os.path.exists(DEFAULT_TOKEN_FILENAME):
            try:
                with open(DEFAULT_TOKEN_FILENAME, "r") as f:
                    creds = Credentials.from_authorized_user_info(json.load(f), SCOPES)
            except Exception as e:
                print(f"Error loading token file {DEFAULT_TOKEN_FILENAME}: {e}")
                creds = None
        if creds and creds.valid:
            return creds
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Failed to refresh credentials from {DEFAULT_TOKEN_FILENAME}: {e}")
                creds = None
        if not creds:
            if os.path.exists(DEFAULT_TOKEN_FILENAME):
                os.remove(DEFAULT_TOKEN_FILENAME)
            flow = InstalledAppFlow.from_client_secrets_file(DEFAULT_CREDENTIALS_FILENAME, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(DEFAULT_TOKEN_FILENAME, "w") as f:
                f.write(creds.to_json())
        return creds

    def get_credentials_multi(self, cred_file, token_file):
        creds = None
        if os.path.exists(token_file):
            try:
                with open(token_file, "r") as f:
                    creds = Credentials.from_authorized_user_info(json.load(f), SCOPES)
            except Exception as e:
                print(f"Error loading token file {token_file}: {e}")
                creds = None
        if creds and creds.valid:
            return creds
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Failed to refresh credentials from {token_file}: {e}")
                creds = None
        if not creds:
            if os.path.exists(token_file):
                os.remove(token_file)
            flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_file, "w") as f:
                f.write(creds.to_json())
        return creds

    def list_files(self, page_size=10):
        print(f"\nAccount: {self.account_name}")
        used, total = self.get_storage_info()
        print(f"Storage: {used} / {total}")
        try:
            results = self.service.files().list(pageSize=page_size, fields="files(id, name)").execute()
            items = results.get("files", [])
            if not items:
                print("  No files found.")
            else:
                for item in items:
                    print(f"  {item['name']} ({item['id']})")
        except Exception as e:
            print(f"Error listing files: {e}")

    def upload_file(self, file_path):
        if not os.path.exists(file_path):
            print("Error: The file does not exist.")
            return False
        file_name = os.path.basename(file_path)
        file_metadata = {"name": file_name}
        media = MediaFileUpload(file_path, resumable=True)
        try:
            file = self.service.files().create(
                body=file_metadata,
                media_body=media
            ).execute()
            print(f"File uploaded successfully to Google Drive: {file.get('name')} ({file.get('id')})")
            return True
        except Exception as e:
            print(f"Google Drive upload failed: {e}")
            return False

    def download_file(self, file_id, save_dir):
        if not os.path.exists(save_dir):
            print("Error: The directory does not exist.")
            return False
        try:
            file_info = self.service.files().get(fileId=file_id, fields="id, name").execute()
            file_name = file_info.get("name")
            save_path = os.path.join(save_dir, file_name)
            request = self.service.files().get_media(fileId=file_id)
            with open(save_path, "wb") as f:
                f.write(request.execute())
            print(f"File downloaded successfully from Google Drive to: {save_path}")
            return True
        except Exception as e:
            # print(f"Error downloading file from Google Drive: {e}")
            return False

    def get_storage_info(self):
        try:
            about = self.service.about().get(fields="storageQuota").execute()
            used_bytes = int(about["storageQuota"]["usage"])
            total_bytes = int(about["storageQuota"]["limit"])
            used = self.format_size(used_bytes)
            total = self.format_size(total_bytes)
            return used, total
        except Exception as e:
            print(f"Error fetching storage info: {e}")
            return "Unknown", "Unknown"

    def get_remaining_space(self):
        try:
            about = self.service.about().get(fields="storageQuota").execute()
            used_bytes = int(about["storageQuota"]["usage"])
            total_bytes = int(about["storageQuota"]["limit"])
            return total_bytes - used_bytes
        except Exception as e:
            print(f"Error fetching storage info: {e}")
            return 0

    def format_size(self, size_in_bytes):
        if size_in_bytes >= 1_073_741_824:
            return f"{size_in_bytes / 1_073_741_824:.2f} GB"
        elif size_in_bytes >= 1_048_576:
            return f"{size_in_bytes / 1_048_576:.2f} MB"
        elif size_in_bytes >= 1024:
            return f"{size_in_bytes / 1024:.2f} KB"
        else:
            return f"{size_in_bytes} B"
