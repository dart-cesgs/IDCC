import streamlit as st
import os
from User.User_Operation import upload, display_folder_selector_for_upload
from main import show_reset_cache_button

st.header("Upload File or Folder to Google Drive")

# Initialize session state for upload process if not present
if 'upload_selected_folders' not in st.session_state:
    st.session_state.upload_selected_folders = []

# Show the folder navigation structure
if st.session_state.upload_selected_folders:
    with st.container():
        col1, col2 = st.columns([2, 1])
        for folder in st.session_state.upload_selected_folders:
            col1.write(f" - {folder['title']}")
    # Button to go back to parent folder
    if st.session_state.upload_selected_folders and col2.button("Back to Previous Folder ⬅️"):
        st.session_state.upload_selected_folders.pop()
        st.rerun()

# Display folder selector for upload
upload_folder_option = display_folder_selector_for_upload()

# Add the Reset Cache button below the folder selector
show_reset_cache_button()

st.divider()

# Upload type selector
upload_type = st.radio("Choose upload type:", ["File", "Folder"])

if upload_type == "File":
    # File uploader component
    files = st.file_uploader("Choose files", accept_multiple_files=True)
else:
    # Folder upload simulation
    folder_name = st.text_input("Enter folder name:")
    files = st.file_uploader("Choose files for the folder", accept_multiple_files=True)

# Upload/Update button
if st.button("Upload/Update"):
    if upload_type == "File" and files:
        for file in files:
            with open(file.name, "wb") as f:
                f.write(file.getbuffer())
            upload(file.name, file.name, upload_folder_option)
            # Update logs
            if 'activity' not in st.session_state:
                st.session_state.activity = []
            st.session_state.activity.append(
                f"{st.session_state.name} uploaded file {file.name} to {'/'.join([folder['title'] for folder in st.session_state.upload_selected_folders])}"
            )
            # Print progress
            st.success(
                f"File '{file.name}' uploaded successfully to '{'/'.join([folder['title'] for folder in st.session_state.upload_selected_folders]) or 'root'}'."
            )

    elif upload_type == "Folder" and folder_name and files:
        # Create a new folder in Google Drive
        new_folder_id = upload(
            folder_name, local_path=None, folder=upload_folder_option, mime_type='application/vnd.google-apps.folder'
        )

        # Upload files to the new folder
        for file in files:
            with open(file.name, "wb") as f:
                f.write(file.getbuffer())
            upload(file.name, file.name, new_folder_id)

        # Update logs
        if 'activity' not in st.session_state:
            st.session_state.activity = []
        st.session_state.activity.append(
            f"{st.session_state.name} uploaded folder {folder_name} with {len(files)} files to {'/'.join([folder['title'] for folder in st.session_state.upload_selected_folders])}"
        )

        # Print progress
        st.success(
            f"Folder '{folder_name}' with {len(files)} files uploaded successfully to '{'/'.join([folder['title'] for folder in st.session_state.upload_selected_folders]) or 'root'}'."
        )
    else:
        st.warning("Please select files to upload.")

# Add some vertical space
st.write("")