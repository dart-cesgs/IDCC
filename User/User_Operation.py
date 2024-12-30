import pandas as pd
import streamlit as st
import zipfile
import os
from io import BytesIO
import base64
import json
from pydrive2.drive import GoogleDrive
from pydrive2.auth import GoogleAuth

### LOGIN FUNCTION ###
# Decode service account
# def get_account_credentials(key):
#     base64_encoded_service_account = key
#     # Step 1: Decode the Base64-encoded string
#     decoded_service_account = base64.b64decode(base64_encoded_service_account).decode('utf-8')
#     # Step 2: Parse the decoded string as JSON
#     service_credentials = json.loads(decoded_service_account)
#     return service_credentials

# def login_with_service_account():
#     settings = {
#                 "client_config_backend": "service",
#                 "service_config": {
#                     "client_json_dict": get_account_credentials(st.secrets.BASE64_ENCODED_SERVICE_ACCOUNT), # from secrets.toml
#                 }
#             }
#     gauth = GoogleAuth(settings=settings)
#     gauth.ServiceAuth()
#     return gauth

# ### LOGIN ###
# drive = GoogleDrive(login_with_service_account())
# print('successful login with user role')

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# Autentikasi Google Drive
gauth = GoogleAuth()
gauth.LoadCredentialsFile("credentials.json") 
if gauth.access_token_expired:
    # Refresh token jika sudah kadaluarsa
    gauth.Refresh()
else:
    # Otorisasi jika token masih valid
    gauth.Authorize()

# Koneksi ke Google Drive
drive = GoogleDrive(gauth)
print("Login successful with cesgs.unair@gmail.com")

### FUNCTIONNNNNNN ###
# Function to get file id by title
def get_file_id_by_title(file_title):
    try:
        files = drive.ListFile({'q': f"title = '{file_title}'"}).GetList()
        return files[0]['id'] if files else None
    except Exception as e:
        print(f"Error retrieving file ID: {e}")
        return None

# Function to get folder id by title
def get_folder_id_by_title(folder_title):
    try:
        folders = drive.ListFile({'q': f"title = '{folder_title}'"}).GetList()
        if folders and folders[0]['mimeType'] == 'application/vnd.google-apps.folder':
            return folders[0]['id']
        else:
            print(f"Folder '{folder_title}' not found or is not a folder.")
            return None
    except Exception as e:
        print(f"Error retrieving folder ID: {e}")
        return None
    
# Function to get subfolders in a folder
def get_subfolders_for_upload(folder_id='root'):
    if folder_id == 'root':
        files_and_folders = st.session_state.folder
    else:
        files_and_folders = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()

    subfolders = [{'id': f['id'], 'title': f['title']} for f in files_and_folders if f['mimeType'] == 'application/vnd.google-apps.folder']
    return subfolders

def upload(file_name, local_path=None, folder=None, mime_type=None):
    try:
        folder_id = folder if folder != 'root' else None

        if mime_type == 'application/vnd.google-apps.folder':
            # Buat folder baru
            file_metadata = {'title': file_name, 'mimeType': mime_type}
            if folder_id:
                file_metadata['parents'] = [{"id": folder_id}]
            new_folder = drive.CreateFile(file_metadata)
            new_folder.Upload()
            print(f"Folder '{file_name}' created.")
            return new_folder['id']
        else:
            # Upload file
            file_metadata = {'title': file_name}
            if folder_id:
                file_metadata['parents'] = [{"id": folder_id}]
            new_file = drive.CreateFile(file_metadata)
            if local_path:
                new_file.SetContentFile(local_path)
            new_file.Upload()
            print(f"File '{file_name}' uploaded.")
            return new_file['id']
    except Exception as e:
        print(f"Error during upload: {e}")
        return None

        
# Recursive function to display folder selection for upload
def display_folder_selector_for_upload():
    folder_id = 'root' if len(st.session_state.upload_selected_folders) == 0 else st.session_state.upload_selected_folders[-1]['id']
    subfolders = get_subfolders_for_upload(folder_id)

    if subfolders:
        folder_titles = [f['title'] for f in subfolders]
        unique_key = f"folder_selector_{folder_id}_{len(st.session_state.upload_selected_folders)}"
        selected_folder = st.selectbox(
            f"Select Folder {st.session_state.upload_selected_folders[-1]['title'] if st.session_state.upload_selected_folders else 'root'}",
            [''] + folder_titles,
            key=unique_key  # Menggunakan kunci yang unik
        )


        if selected_folder:
            # Get the folder ID of the selected folder and append to session_state for upload
            folder = next(f for f in subfolders if f['title'] == selected_folder)
            st.session_state.upload_selected_folders.append(folder)
            st.rerun()

    # Display current selected folder path for upload
    # if st.session_state.upload_selected_folders:
    #     st.write(f"Current Upload Folder: {' / '.join([folder['title'] for folder in st.session_state.upload_selected_folders])}")
    
    return st.session_state.upload_selected_folders[-1]['id'] if st.session_state.upload_selected_folders else 'root'

# Function to download file/files
def download_files_from_drive(folder_id, path):
    try:
        if not folder_id:
            st.error("Folder not found.")
            return None

        # List all files and folders within the current folder
        items_in_folder = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()

        for item in items_in_folder:
            # If the item is a folder, recursively download its contents
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                st.write(f"Entering folder: {item['title']}")
                new_path = os.path.join(path, item['title'])
                os.makedirs(new_path, exist_ok=True)
                download_files_from_drive(item['id'], new_path)
            else:
                # Download files in the current folder
                download_file(item, path)

        st.success(f"Zip Ready to Download")

    except Exception as e:
        st.error(f"Error during file operation: {e}")
        return None

# this function is used for above function
def download_file(file, path):
    try:
        print(f"Downloading {file['title']} from GDrive to {path}")
        file.GetContentFile(os.path.join(path, file['title']), remove_bom=True, mimetype=file['mimeType'])
    
    except Exception as e:
        print(f"Error downloading file {file['title']}: {e}")

def create_zip(folder_path):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zip_file.write(file_path, arcname)
    zip_buffer.seek(0)
    return zip_buffer

### SECONDARY FUNCTION ###
@st.cache_resource(ttl=1800) 
def get_list_of_all_folders_forusers():
    list_of_folders = drive.ListFile({'q': "mimeType = 'application/vnd.google-apps.folder'"}).GetList()
    return list_of_folders

# Function to get subfolders and files in a folder
def get_subfolders_and_files(folder_id='root'):
    # If we're at the root folder, include sharedWithMe folders
    if folder_id == 'root':
        files_and_folders = st.session_state.folder
    else:
        files_and_folders = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()

    subfolders = [{'id': f['id'], 'title': f['title']} for f in files_and_folders if f['mimeType'] == 'application/vnd.google-apps.folder']
    files = [{'ID': f['id'], 'Title': f['title'], 'File Type': f['mimeType']} for f in files_and_folders if f['mimeType'] != 'application/vnd.google-apps.folder']

    return subfolders, files

# Function to display the selected folder
def display_folder_selector():
    folder_id = 'root' if len(st.session_state.selected_folders) == 0 else st.session_state.selected_folders[-1]['id']
    
    subfolders, files = get_subfolders_and_files(folder_id)
    
    if subfolders:
        folder_titles = [f['title'] for f in subfolders]
        unique_key = f"folder_selector_{folder_id}_{len(st.session_state.upload_selected_folders)}"
        selected_folder = st.selectbox(
            f"Select Folder {st.session_state.upload_selected_folders[-1]['title'] if st.session_state.upload_selected_folders else 'root'}",
            [''] + folder_titles,
            key=unique_key  # Menggunakan kunci yang unik
        )


        if selected_folder:
            # Get the folder ID of the selected folder and append to session_state
            folder = next(f for f in subfolders if f['title'] == selected_folder)
            st.session_state.selected_folders.append(folder)
            st.rerun()
    
    return files

