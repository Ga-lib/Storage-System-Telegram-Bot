# main.py
import os
from google_drive_service import GoogleDriveService
from dropbox_service import DropboxService
from chunking_utils import chunk_and_upload_file, assemble_chunked_file_automatic

def smart_upload_combined(google_services, dropbox_services):
    """
    Uploads a file to the service (Google Drive or Dropbox) with the smallest remaining space that is still large enough.
    If no single service can hold the entire file, performs a chunked upload.
    """
    file_path = input("Enter the path of the file to upload: ").strip()
    if not os.path.exists(file_path):
        print("Error: The file does not exist.")
        return
    file_size = os.path.getsize(file_path)
    all_services = google_services + dropbox_services
    all_services.sort(key=lambda svc: svc.get_remaining_space())
    chosen = None
    for svc in all_services:
        if svc.get_remaining_space() >= file_size:
            chosen = svc
            break
    if chosen:
        print(f"Uploading file to account: {chosen.account_name}")
        chosen.upload_file(file_path)
    else:
        total_remaining = sum(svc.get_remaining_space() for svc in all_services)
        if total_remaining < file_size:
            print("Error: Total available space across all services is insufficient to upload this file.")
            return
        else:
            print("No single service can hold the entire file. Proceeding with chunked upload...")
            chunk_and_upload_file(file_path, file_size, all_services)

def smart_download_combined(google_services, dropbox_services):
    """
    Attempts to download a file by searching for its ID first in Google Drive services,
    then in Dropbox services.
    If a chunked file is detected (its name contains '_part'), automatically triggers reassembly.
    """
    file_id = input("Enter the file ID to download: ").strip()
    # Try Google Drive services first
    for svc in google_services:
        try:
            file_info = svc.service.files().get(fileId=file_id, fields="id, name").execute()
            print(f"DEBUG: Found file in Google Drive account '{svc.account_name}': {file_info.get('name')}")
            if "_part" in file_info.get("name", ""):
                print("DEBUG: Detected chunked file. Initiating automatic reassembly...")
                base_filename = file_info["name"].split("_part")[0]
                assemble_chunked_file_automatic(base_filename, google_services, dropbox_services)
                return
            else:
                save_dir = input("Enter the directory to save the file: ").strip()
                svc.download_file(file_id, save_dir)
                return
        except Exception as e:
            continue
    # Then try Dropbox services
    for svc in dropbox_services:
        try:
            file_info = svc.dbx.files_get_metadata(file_id)
            print(f"DEBUG: Found file in Dropbox account '{svc.account_name}': {file_info.name}")
            if "_part" in file_info.name:
                print("DEBUG: Detected chunked file. Initiating automatic reassembly...")
                base_filename = file_info.name.split("_part")[0]
                assemble_chunked_file_automatic(base_filename, google_services, dropbox_services)
                return
            else:
                save_dir = input("Enter the directory to save the file: ").strip()
                svc.download_file(file_id, save_dir)
                return
        except Exception as e:
            continue
    print("Error: File not found in any service.")

def main():
    # Load Google Drive services
    google_services = []
    credentials_folder = "credentials"
    if os.path.exists(credentials_folder) and os.path.isdir(credentials_folder):
        credential_files = [f for f in os.listdir(credentials_folder) if f.endswith(".json")]
        if credential_files:
            for cred_filename in credential_files:
                cred_path = os.path.join(credentials_folder, cred_filename)
                token_filename = f"token_{cred_filename}"
                token_path = os.path.join(credentials_folder, token_filename)
                account_name = os.path.splitext(cred_filename)[0]
                svc = GoogleDriveService(account_name, cred_path, token_path)
                google_services.append(svc)
        else:
            svc = GoogleDriveService()
            google_services.append(svc)
    else:
        svc = GoogleDriveService()
        google_services.append(svc)

    # Load Dropbox services
    dropbox_services = []
    tokens = {
        "dropbox_account_1": "give your dropbox token here",
        "dropbox_account_2": "give your dropbox token here",
        "dropbox_account_3": "give your dropbox token here"
    }
    for name, token in tokens.items():
        svc = DropboxService(name, token)
        dropbox_services.append(svc)

    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("Google Drive Storage:")
        for svc in google_services:
            used, total = svc.get_storage_info()
            print(f"  {svc.account_name}: {used} / {total}")
        print("\nDropbox Storage:")
        for svc in dropbox_services:
            used, allocated = svc.get_storage_info()
            used_str = svc.format_size(used) if used is not None else "Unknown"
            allocated_str = svc.format_size(allocated) if allocated is not None else "Unknown"
            print(f"  {svc.account_name}: {used_str} / {allocated_str}")

        print("\nOptions:")
        print("  1. List files (from all services)")
        print("  2. Upload a file (smart upload)")
        print("  3. Download a file (smart download)")
        print("  4. Exit")
        choice = input("\nEnter your choice: ").strip()
        if choice == "1":
            for svc in google_services:
                svc.list_files()
            for svc in dropbox_services:
                svc.list_files()
        elif choice == "2":
            smart_upload_combined(google_services, dropbox_services)
        elif choice == "3":
            smart_download_combined(google_services, dropbox_services)
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice, try again.")
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
