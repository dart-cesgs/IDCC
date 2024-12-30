import streamlit as st
import pandas as pd
from Admin.Admin_Operation import display_folder_selector, delete_files
from main import show_reset_cache_button
import os

st.header("Delete File from Google Drive")

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

# Show selectbox and retrieve files
files_in_current_folder = display_folder_selector()

# Add reset cache button
show_reset_cache_button()

if files_in_current_folder:
    files_df = pd.DataFrame(files_in_current_folder)

    # Add a "Select" column to let users choose which files to delete
    files_df['Select Files to Delete'] = False

    # Display the table with the checkboxes using st.data_editor
    edited_df = st.data_editor(files_df, column_order=('Title', 'File Type', 'Select Files to Delete'))

    # Add a "Select All" checkbox
    if st.checkbox("Select All Files"):
        files_df['Select Files to Delete'] = True
        edited_df = files_df  # Update the edited dataframe

    # Extract the selected rows for deletion
    selected_files = edited_df[edited_df['Select Files to Delete'] == True]
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
                        # DELETE PERMANENT
                        delete_files(file_id=file_id)
                        st.success(f"File '{row['Title']}' deleted successfully.")
                        if 'activity' not in st.session_state:
                            st.session_state.activity = []
                        st.session_state.activity.append(f"{st.session_state.name} delete {row['Title']}")  # update logs
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
    # If no files, conditionally show the Reset Cache button
    if 'reset_cache_key' not in st.session_state:
        st.session_state.reset_cache_key = "reset_cache_" + os.urandom(8).hex()
    st.button("Reset Cache", key=st.session_state.reset_cache_key)
