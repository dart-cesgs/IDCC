import streamlit as st
import pandas as pd
import os
from io import BytesIO
from tempfile import TemporaryDirectory
from Admin.Admin_Operation import get_subfolders_and_files, display_folder_selector, download_files_from_drive, create_zip
from main import show_reset_cache_button
from pydrive2.drive import GoogleDrive
from pydrive2.auth import GoogleAuth

# Initialize Google Drive authentication
gauth = GoogleAuth()
gauth.LoadCredentialsFile("credentials.json")
if gauth.access_token_expired:
    gauth.Refresh()
else:
    gauth.Authorize()
drive = GoogleDrive(gauth)

st.header("Read and Download Files from Google Drive")

if 'selected_folders' not in st.session_state:
    st.session_state.selected_folders = []

# Show the folder navigation structure
if st.session_state.selected_folders:
    with st.container():
        col1, col2 = st.columns([2, 1])
        for folder in st.session_state.selected_folders:
            col1.write(f" - {folder['title']}")
    # Button to go back to parent folder
    if st.session_state.selected_folders and col2.button("Back to Previous Folder ⬅️"):
        st.session_state.selected_folders.pop()
        st.rerun()

# Show selectbox and retrieve files
files_in_current_folder = display_folder_selector()

# Add reset cache button
if files_in_current_folder:
    show_reset_cache_button()

if files_in_current_folder:
    files_df = pd.DataFrame(files_in_current_folder)

    # Add a "Select" column to let users choose which files to download
    files_df['Select Files to Download'] = False

    # Display the table with the checkboxes using st.data_editor
    edited_df = st.data_editor(files_df, column_order=('Title', 'File Type', 'Select Files to Download'))

    # Add a "Select All" checkbox
    if st.checkbox("Select All Files"):
        files_df['Select Files to Download'] = True
        edited_df = files_df  # Update the edited dataframe

    # Extract the selected rows for download
    selected_files = edited_df[edited_df['Select Files to Download'] == True]
    st.divider()

    if not selected_files.empty:
        st.write(f"Selected {len(selected_files)} files for download:")

        # Display selected files in a scrollable table
        st.dataframe(selected_files[['Title', 'File Type']], height=200)

        # Button to trigger ZIP creation and download
        if st.button("Download Selected Files", use_container_width=True):
            with TemporaryDirectory() as tmp_dir:
                folder_id = st.session_state.selected_folders[-1]['id'] if st.session_state.selected_folders else 'root'
                folder_name = st.session_state.selected_folders[-1]['title'] if st.session_state.selected_folders else 'root'
                st.session_state.zip_file_name = f"{folder_name}.zip"  # Save in session state
                # Download each selected file
                for index, row in selected_files.iterrows():
                    file_title = row['Title']
                    file_id = row['ID']
                    file_path = os.path.join(tmp_dir, file_title)
                    try:
                        file = drive.CreateFile({'id': file_id})
                        if row['File Type'] == 'application/vnd.google-apps.spreadsheet':
                            file.GetContentFile(file_path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                        elif row['File Type'] == 'application/vnd.google-apps.document':
                            file.GetContentFile(file_path, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                        elif row['File Type'] == 'application/vnd.google.colaboratory':
                            file.GetContentFile(file_path, mimetype='text/plain')
                        else:
                            file.GetContentFile(file_path)
                    except Exception as e:
                        st.error(f"Error downloading file '{file_title}': {e}")

                # Create a ZIP file from the downloaded files
                zip_buffer = create_zip(tmp_dir)
                # Store the ZIP buffer in session state
                st.session_state.zip_buffer = zip_buffer
                st.success("ZIP file created. Click the button below to download.")

        # Button to download the ZIP file
        if 'zip_buffer' in st.session_state and 'zip_file_name' in st.session_state:
            st.divider()
            st.download_button(
                label="Download Selected Files as ZIP 📂",
                data=st.session_state.zip_buffer,
                file_name=st.session_state.zip_file_name,  # Use the variable from session state
                mime="application/zip",
                use_container_width=True
            )
            # Optionally, clear the session state after download
            # del st.session_state.zip_buffer
    else:
        st.warning("No files selected for download.")
else:
    st.write("No files in this folder.")
    # If no files, conditionally show the Reset Cache button
    if 'reset_cache_key' not in st.session_state:
        st.session_state.reset_cache_key = "reset_cache_" + os.urandom(8).hex()
    st.button("Reset Cache", key=st.session_state.reset_cache_key)
