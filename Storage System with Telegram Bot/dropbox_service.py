# dropbox_service.py
import os
import dropbox
from cloud_service import CloudService
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError

class DropboxService(CloudService):
    def __init__(self, account_name, token):
        self.account_name = account_name
        self.token = token
        self.dbx = self.connect_to_dropbox(token)

    def connect_to_dropbox(self, token):
        try:
            dbx = dropbox.Dropbox(oauth2_access_token=token, timeout=300)  # 5 minutes timeout
            dbx.users_get_current_account()
            print(f"✅ Connected to Dropbox ({self.account_name})")
            return dbx
        except Exception as e:
            print("Dropbox connection error:", e)
            return None

    def list_files(self, page_size=10):
        print(f"\nAccount: {self.account_name}")
        used, allocated = self.get_storage_info()
        used_str = self.format_size(used) if used is not None else "Unknown"
        allocated_str = self.format_size(allocated) if allocated is not None else "Unknown"
        print(f"Storage: {used_str} / {allocated_str}")
        try:
            result = self.dbx.files_list_folder("", recursive=True)
            items = result.entries
            if not items:
                print("  No files found.")
            else:
                for entry in items:
                    print(f"  {entry.path_display} ({entry.id})")
            while result.has_more:
                result = self.dbx.files_list_folder_continue(result.cursor)
                for entry in result.entries:
                    print(f"  {entry.path_display} ({entry.id})")
        except Exception as e:
            print(f"Error listing Dropbox files: {e}")

    def upload_file(self, file_path):
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} not found.")
            return False
        file_name = os.path.basename(file_path)
        dest_path = "/" + file_name
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            self.dbx.files_upload(data, dest_path, mode=WriteMode("overwrite"))
            metadata = self.dbx.files_get_metadata(dest_path)
            print(f"File uploaded successfully to Dropbox: {metadata.name} (ID: {metadata.id})")
            return True
        except Exception as e:
            print(f"Dropbox upload failed: {e}")
            return False

    def download_file(self, file_id, save_dir):
        if not os.path.exists(save_dir):
            print("Error: Save directory does not exist.")
            return False
        try:
            file_info = self.dbx.files_get_metadata(file_id)
            file_name = file_info.name
            save_path = os.path.join(save_dir, file_name)
            self.dbx.files_download_to_file(download_path=save_path, path=file_id)
            print(f"✅ Downloaded from Dropbox to: {save_path}")
            return True
        except Exception as e:
            print(f"Download failed: {e}")
            return False

    def get_storage_info(self):
        try:
            usage = self.dbx.users_get_space_usage()
            used = usage.used
            allocated = usage.allocation.get_individual().allocated
            return used, allocated
        except Exception as e:
            print(f"Error retrieving storage info from Dropbox: {e}")
            return None, None

    def get_remaining_space(self):
        used, allocated = self.get_storage_info()
        if used is not None and allocated is not None:
            return allocated - used
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
