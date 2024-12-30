import pandas as pd
import streamlit as st
import zipfile
import os
from io import BytesIO
from pydrive2.drive import GoogleDrive
from pydrive2.auth import GoogleAuth

# Autentikasi Google Drive menggunakan Streamlit Secrets
gauth = GoogleAuth(settings={
    "client_config_backend": "service",
    "service_config": {
        "client_json_dict": dict(st.secrets["GOOGLE_CREDENTIALS"])
    }
})
gauth.ServiceAuth()

# Koneksi ke Google Drive
drive = GoogleDrive(gauth)
print("Login successful with admin role")

### FUNCTION DEFINITIONS ###

# Function to get file ID by title
def get_file_id_by_title(file_title):
    try:
        files = drive.ListFile({'q': f"title = '{file_title}'"}).GetList()
        return files[0]['id'] if files else None
    except Exception as e:
        print(f"Error retrieving file ID: {e}")
        return None

# Function to get folder ID by title
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
    try:
        if folder_id == 'root':
            files_and_folders = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
        else:
            files_and_folders = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()

        subfolders = [{'id': f['id'], 'title': f['title']} for f in files_and_folders if f['mimeType'] == 'application/vnd.google-apps.folder']
        return subfolders
    except Exception as e:
        print(f"Error retrieving subfolders: {e}")
        return []

# Function to upload files or create folders
def upload(file_name, local_path=None, folder=None, mime_type=None):
    try:
        folder_id = folder if folder != 'root' else None

        if mime_type == 'application/vnd.google-apps.folder':
            file_metadata = {'title': file_name, 'mimeType': mime_type}
            if folder_id:
                file_metadata['parents'] = [{"id": folder_id}]
            new_folder = drive.CreateFile(file_metadata)
            new_folder.Upload()
            print(f"Folder '{file_name}' created.")
            return new_folder['id']
        else:
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

# Function to download files from Google Drive
def download_file(file, path):
    try:
        file.GetContentFile(os.path.join(path, file['title']))
        print(f"Downloaded {file['title']} to {path}")
    except Exception as e:
        print(f"Error downloading file {file['title']}: {e}")

# Function to download all files and folders from a folder
def download_files_from_drive(folder_id, path):
    try:
        items_in_folder = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()

        for item in items_in_folder:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                new_path = os.path.join(path, item['title'])
                os.makedirs(new_path, exist_ok=True)
                download_files_from_drive(item['id'], new_path)
            else:
                download_file(item, path)
    except Exception as e:
        print(f"Error during file operation: {e}")

# Function to delete files or folders
def delete_files(file_id):
    try:
        file = drive.CreateFile({'id': file_id})
        file.Delete()
        print(f"Deleted file or folder with ID {file_id}")
    except Exception as e:
        print(f"Error deleting file or folder: {e}")

# Function to create a ZIP archive from a folder
def create_zip(folder_path):
    try:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zip_file.write(file_path, arcname)
        zip_buffer.seek(0)
        return zip_buffer
    except Exception as e:
        print(f"Error creating ZIP archive: {e}")
        return None

# Cached function to retrieve all folders
@st.cache_resource(ttl=1800)
def get_list_of_all_folders():
    try:
        root_folders = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
        shared_folders = drive.ListFile({'q': "sharedWithMe=true and trashed=false"}).GetList()
        return root_folders + shared_folders
    except Exception as e:
        print(f"Error retrieving folders: {e}")
        return []

# Function to get subfolders and files in a folder
def get_subfolders_and_files(folder_id='root'):
    try:
        if folder_id == 'root':
            files_and_folders = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
        else:
            files_and_folders = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()

        subfolders = [{'id': f['id'], 'title': f['title']} for f in files_and_folders if f['mimeType'] == 'application/vnd.google-apps.folder']
        files = [{'ID': f['id'], 'Title': f['title'], 'File Type': f['mimeType']} for f in files_and_folders if f['mimeType'] != 'application/vnd.google-apps.folder']
        return subfolders, files
    except Exception as e:
        print(f"Error retrieving subfolders and files: {e}")
        return [], []

# Function to display a folder selector
def display_folder_selector():
    folder_id = 'root' if len(st.session_state.get("selected_folders", [])) == 0 else st.session_state.selected_folders[-1]['id']
    subfolders, files = get_subfolders_and_files(folder_id)

    if subfolders:
        folder_titles = [f['title'] for f in subfolders]
        selected_folder = st.selectbox(
            f"Select Folder: {st.session_state.selected_folders[-1]['title'] if st.session_state.selected_folders else 'root'}",
            [''] + folder_titles
        )
        if selected_folder:
            folder = next(f for f in subfolders if f['title'] == selected_folder)
            st.session_state.selected_folders.append(folder)
            st.rerun()
    return files
