import streamlit as st
import time
import pandas as pd
from main import show_reset_cache_button

# Flag to track if we are in edit mode
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# Function to toggle edit mode
def toggle_edit_mode():
    st.session_state.edit_mode = not st.session_state.edit_mode

# Function to save edited data
def save_data(updated_df):
    st.session_state.database = updated_df
    st.session_state.edit_mode = False

# Display buttons and handle interactions
if st.session_state.edit_mode:
    st.write("You are in edit mode. Make your changes and click save.")
    # Display the editable data editor
    edited_data = st.data_editor(st.session_state.database, num_rows="dynamic")
    if st.button("Save"):
        save_data(edited_data)
        st.session_state.connection.update(data=edited_data, worksheet='Users')  # Update spreadsheets
        st.success('Data Updated!')
        time.sleep(1)
        st.rerun()
else:
    # Display the table in read-only mode
    st.header('Table of User and Roles')
    st.table(st.session_state.database.sort_values(by='Role'))
    # Edit button to enable editing
    if st.button("Edit"):
        st.session_state.edit_mode = True
        st.rerun()
    # Add Reset Cache button right below the Edit button
    show_reset_cache_button()

# Print latest activity
recent_activities = pd.DataFrame({'Activity': st.session_state.logs[-10:] + st.session_state.activity})
st.header('Table of User Activity')
st.table(recent_activities)
