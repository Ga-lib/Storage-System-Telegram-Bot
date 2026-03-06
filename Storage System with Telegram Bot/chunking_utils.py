# chunking_utils.py
import os
from googleapiclient.http import MediaFileUpload

# === **CHUNKING LOGIC FOR UPLOAD (chunk_and_upload_file) START** ===
def chunk_and_upload_file(file_path, file_size, sorted_services):
    """
    Splits the file into chunks based on each service's available capacity (with a safety margin)
    and uploads each chunk to the corresponding service.
    Temporary chunk files are saved in the 'chunk_files' folder and deleted after upload.
    
    'sorted_services' is a list of service objects (GoogleDriveService or DropboxService)
    sorted in ascending order by remaining space.
    """
    margin = 10240  # 10 KB margin
    base_file_name = os.path.basename(file_path)
    chunk_dir = "chunk_files"
    os.makedirs(chunk_dir, exist_ok=True)
    part_num = 1
    offset = 0

    with open(file_path, "rb") as f:
        for svc in sorted_services:
            if offset >= file_size:
                break
            effective_capacity = svc.get_remaining_space() - margin
            if effective_capacity <= 0:
                continue
            bytes_to_read = min(effective_capacity, file_size - offset)
            chunk_data = f.read(bytes_to_read)
            if not chunk_data:
                break
            temp_chunk_file = os.path.join(chunk_dir, f"{base_file_name}_part{part_num:03d}")
            with open(temp_chunk_file, "wb") as chunk_out:
                chunk_out.write(chunk_data)
            print(f"DEBUG: Created chunk {temp_chunk_file} with {len(chunk_data)} bytes for service {svc.account_name}")
            if hasattr(svc, 'service'):  # Google Drive
                file_metadata = {"name": f"{base_file_name}_part{part_num:03d}"}
                media = MediaFileUpload(temp_chunk_file, resumable=True)
                try:
                    file = svc.service.files().create(
                        body=file_metadata,
                        media_body=media
                    ).execute()
                    print(f"DEBUG: Uploaded chunk to Google Drive: {file.get('name')} ({file.get('id')})")
                except Exception as e:
                    print(f"DEBUG: Google Drive chunk upload failed: {e}")
            elif hasattr(svc, 'dbx'):  # Dropbox
                dest_path = "/" + f"{base_file_name}_part{part_num:03d}"
                try:
                    with open(temp_chunk_file, 'rb') as chunk_file:
                        data = chunk_file.read()
                    svc.dbx.files_upload(data, dest_path)
                    metadata = svc.dbx.files_get_metadata(dest_path)
                    print(f"DEBUG: Uploaded chunk to Dropbox: {metadata.name} (ID: {metadata.id})")
                except Exception as e:
                    print(f"DEBUG: Dropbox chunk upload failed: {e}")
            try:
                os.remove(temp_chunk_file)
                print(f"DEBUG: Deleted temporary chunk file {temp_chunk_file}")
            except Exception as e:
                print(f"DEBUG: Failed to delete temporary chunk file {temp_chunk_file}: {e}")
            offset += len(chunk_data)
            part_num += 1
    if offset < file_size:
        print("DEBUG: Warning - file was not completely uploaded. Remaining bytes:", file_size - offset)
    else:
        print("DEBUG: File chunked and uploaded successfully.")
# === **CHUNKING LOGIC FOR UPLOAD (chunk_and_upload_file) END** ===

# === **REASSEMBLY LOGIC FOR DOWNLOAD (assemble_chunked_file_automatic) START** ===
def assemble_chunked_file_automatic(base_filename, google_services, dropbox_services):
    """
    Automatically detects and downloads all chunk files with names following the convention
    "{base_filename}_partNNN" from both Google Drive and Dropbox services,
    reassembles them in order, and saves the combined file to a destination directory.
    Temporary chunk files are stored in 'downloaded_chunks' and deleted after reassembly.
    """
    temp_chunk_folder = "downloaded_chunks"
    os.makedirs(temp_chunk_folder, exist_ok=True)
    
    def download_chunks_from_google(svc):
        try:
            query = f"name contains '{base_filename}_part'"
            results = svc.service.files().list(q=query, fields="files(id, name)").execute()
            files = results.get("files", [])
            downloaded = []
            for file in files:
                local_path = os.path.join(temp_chunk_folder, file["name"])
                request = svc.service.files().get_media(fileId=file["id"])
                with open(local_path, "wb") as f:
                    f.write(request.execute())
                print(f"DEBUG: Downloaded chunk '{file['name']}' from Google Drive account '{svc.account_name}'.")
                downloaded.append(file["name"])
            return downloaded
        except Exception as e:
            print(f"DEBUG: Error downloading chunks from Google Drive account '{svc.account_name}': {e}")
            return []
    
    def download_chunks_from_dropbox(svc):
        try:
            result = svc.dbx.files_list_folder("", recursive=True)
            downloaded = []
            for entry in result.entries:
                if entry.name.startswith(f"{base_filename}_part"):
                    local_path = os.path.join(temp_chunk_folder, entry.name)
                    metadata, response = svc.dbx.files_download(entry.id)
                    with open(local_path, "wb") as f:
                        f.write(response.content)
                    print(f"DEBUG: Downloaded chunk '{entry.name}' from Dropbox account '{svc.account_name}'.")
                    downloaded.append(entry.name)
            return downloaded
        except Exception as e:
            print(f"DEBUG: Error downloading chunks from Dropbox account '{svc.account_name}': {e}")
            return []
    
    all_chunks = []
    for svc in google_services:
        chunks = download_chunks_from_google(svc)
        all_chunks.extend(chunks)
    for svc in dropbox_services:
        chunks = download_chunks_from_dropbox(svc)
        all_chunks.extend(chunks)
    
    if not all_chunks:
        print("DEBUG: No chunk files found for base filename:", base_filename)
        return
    
    def get_part_number(chunk_name):
        try:
            return int(chunk_name.split("_part")[-1])
        except Exception as e:
            print(f"DEBUG: Failed to extract part number from {chunk_name}: {e}")
            return 0

    all_chunks.sort(key=get_part_number)
    print("DEBUG: Sorted chunks:", all_chunks)
    
    output_dir = input("Enter the directory to save the reassembled file: ").strip()
    if not os.path.exists(output_dir):
        print("DEBUG: Output directory does not exist.")
        return
    output_path = os.path.join(output_dir, base_filename)
    
    with open(output_path, "wb") as outfile:
        for chunk_name in all_chunks:
            chunk_path = os.path.join(temp_chunk_folder, chunk_name)
            with open(chunk_path, "rb") as infile:
                data = infile.read()
                outfile.write(data)
            print(f"DEBUG: Appended chunk '{chunk_name}' to '{output_path}'.")
    
    print("DEBUG: File reassembled successfully at:", output_path)
    
    for chunk_name in all_chunks:
        try:
            os.remove(os.path.join(temp_chunk_folder, chunk_name))
            print(f"DEBUG: Deleted temporary chunk file '{chunk_name}'.")
        except Exception as e:
            print(f"DEBUG: Could not delete temporary chunk file '{chunk_name}': {e}")
# === **REASSEMBLY LOGIC FOR DOWNLOAD (assemble_chunked_file_automatic) END** ===
