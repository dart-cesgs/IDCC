import streamlit as st
import pandas as pd
from Admin.Admin_Operation import display_folder_selector, delete_files, drive
from main import show_reset_cache_button
import os

st.header("Delete File or Folder from Google Drive")

# Initialize session state variables if not present
if 'selected_folders' not in st.session_state:
    st.session_state.selected_folders = []

if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = False

# Show the folder navigation structure
if st.session_state.selected_folders:
    with st.container():
        col1, col2 = st.columns([2, 1])
        for folder in st.session_state.selected_folders:
            col1.write(f" - {folder['title']}")
    # Button to go back to parent folder
    if st.session_state.selected_folders and col2.button("Back to Previous Folder ⬅️"):
        st.session_state.selected_folders.pop()
        st.rerun()  # Use st.rerun() instead of st.experimental_rerun()

# Display folder selector
selected_folder = display_folder_selector()  # Folder selection functionality here

# Add Reset Cache button here, below the folder selector
show_reset_cache_button()

st.divider()

# Select whether to delete Files or Folders
delete_type = st.radio("What would you like to delete?", ["File", "Folder"])

# Handle deletion based on selected type
if delete_type == "File":
    # Show selectbox and retrieve files
    files_in_current_folder = selected_folder  # Use the selected folder for file operations

    if files_in_current_folder:
        files_df = pd.DataFrame(files_in_current_folder)

        # Add a "Select" column to let users choose which files to delete
        files_df['Select'] = False

        # Display the table with the checkboxes using st.data_editor
        edited_df = st.data_editor(files_df, column_order=('Title', 'File Type', 'Select'))

        # Add a "Select All" checkbox
        if st.checkbox("Select All Files"):
            files_df['Select'] = True
            edited_df = files_df  # Update the edited dataframe

        # Extract the selected rows for deletion
        selected_files = edited_df[edited_df['Select'] == True]
        st.divider()

        if not selected_files.empty:
            st.write(f"Selected {len(selected_files)} files for deletion:")

            # Display selected files in a scrollable table
            st.dataframe(selected_files[['Title', 'File Type']], height=200)

            def delete_selected_files():
                st.session_state.confirm_delete = True

            # Add a delete button
            if st.button("Delete Selected Files", on_click=delete_selected_files, use_container_width=True):
                pass

            if st.session_state.confirm_delete:
                confirm_delete = st.button("Are you sure you want to delete these files?")
                if confirm_delete:
                    for index, row in selected_files.iterrows():
                        file_id = row['ID']
                        try:
                            # DELETE PERMANENTLY
                            delete_files(file_id=file_id)
                            st.success(f"File '{row['Title']}' deleted successfully.")
                            if 'activity' not in st.session_state:
                                st.session_state.activity = []
                            st.session_state.activity.append(f"{st.session_state.name} deleted file '{row['Title']}'")
                        except Exception as e:
                            st.error(f"Failed to delete file '{row['Title']}': {e}")
                    st.session_state.confirm_delete = False
                    st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
                elif st.button("Cancel"):
                    st.session_state.confirm_delete = False
                    st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
        else:
            st.warning("No files selected for deletion.")
    else:
        st.write("No files in this folder.")

elif delete_type == "Folder":
    # Fetch subfolders in the current directory
    folder_id = 'root' if len(st.session_state.selected_folders) == 0 else st.session_state.selected_folders[-1]['id']
    try:
        subfolders = drive.ListFile({'q': f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
    except Exception as e:
        st.error(f"Error fetching folders: {e}")
        subfolders = []

    if subfolders:
        # Prepare DataFrame for folders
        folders_df = pd.DataFrame(subfolders)
        folders_df = folders_df.rename(columns={'title': 'Title', 'id': 'ID', 'mimeType': 'File Type'})
        # Ensure 'ID' column is retained for deletion
        folders_df = folders_df[['Title', 'File Type', 'ID']]
        folders_df['Select'] = False

        # Display the table with the checkboxes using st.data_editor
        edited_folders_df = st.data_editor(folders_df, column_order=('Title', 'File Type', 'Select'))

        # Add a "Select All" checkbox
        if st.checkbox("Select All Folders"):
            folders_df['Select'] = True
            edited_folders_df = folders_df  # Update the edited dataframe

        # Extract the selected rows for deletion
        selected_folders = edited_folders_df[edited_folders_df['Select'] == True]
        st.divider()

        if not selected_folders.empty:
            st.write(f"Selected {len(selected_folders)} folders for deletion:")

            # Display selected folders in a scrollable table
            st.dataframe(selected_folders[['Title', 'File Type']], height=200)

            def delete_selected_folders():
                st.session_state.confirm_delete = True

            # Add a delete button
            if st.button("Delete Selected Folders", on_click=delete_selected_folders, use_container_width=True):
                pass

            if st.session_state.confirm_delete:
                confirm_delete = st.button("Yes, delete.")
                if confirm_delete:
                    for index, row in selected_folders.iterrows():
                        folder_id_to_delete = row['ID']
                        try:
                            # DELETE PERMANENTLY
                            delete_files(file_id=folder_id_to_delete)
                            st.success(f"Folder '{row['Title']}' deleted successfully.")
                            if 'activity' not in st.session_state:
                                st.session_state.activity = []
                            st.session_state.activity.append(f"{st.session_state.name} deleted folder '{row['Title']}'")
                        except Exception as e:
                            st.error(f"Failed to delete folder '{row['Title']}': {e}")
                    st.session_state.confirm_delete = False
                    st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
                elif st.button("No, cancel."):
                    st.session_state.confirm_delete = False
                    st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
        else:
            st.warning("No folders selected for deletion.")
    else:
        st.write("No folders in this folder.")
