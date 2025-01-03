import streamlit as st
import requests
from google.oauth2 import service_account
import pandas as pd
import base64
import json
import datetime
import time

# Streamlit App
st.title("Google Drive File Manager")

# Read secrets
spreadsheet_id = st.secrets["connections"]["gsheets"]["spreadsheet"]
service_account_base64 = st.secrets["BASE64_ENCODED_SERVICE_ACCOUNT"]["BASE64_ENCODED_SERVICE_ACCOUNT"]

# Decode the base64-encoded service account credentials
decoded_bytes = base64.b64decode(service_account_base64)
service_account_info = json.loads(decoded_bytes.decode('utf-8'))

# Define the scope
scope = ['https://www.googleapis.com/auth/spreadsheets']

# Authenticate with the service account
credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes=scope)
access_token = credentials.token

# Make a request to the Sheets API for Users sheet
headers = {
    'Authorization': f'Bearer {access_token}'
}
users_url = f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/Users!A1:Z1000'
response = requests.get(users_url, headers=headers)
users_data = response.json()

# Check if 'values' key exists in the response
if 'values' in users_data:
    headers = users_data['values'][0]
    rows = users_data['values'][1:]
    df = pd.DataFrame(rows, columns=headers)
    st.session_state.database = df
else:
    st.error("No data retrieved from Users sheet.")

# Make a request to the Sheets API for Logs sheet
logs_url = f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/Logs!A1:Z1000'
logs_response = requests.get(logs_url, headers=headers)
logs_data = logs_response.json()

# Check if 'values' key exists in the logs response
if 'values' in logs_data:
    logs_headers = logs_data['values'][0]
    logs_rows = logs_data['values'][1:]
    logs_df = pd.DataFrame(logs_rows, columns=logs_headers)
    st.session_state.logs = logs_df['Activity'].values.tolist()
else:
    st.error("No data retrieved from Logs sheet.")

# Define session state variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if 'role' not in st.session_state:
    st.session_state.role = None

if 'name' not in st.session_state:
    st.session_state.name = None

if 'folder' not in st.session_state:
    st.session_state.folder = []

if 'activity' not in st.session_state:
    st.session_state.activity = []

# Function to reset cache
def reset_cache():
    st.cache_data.clear()
    st.session_state.cache_reset = True
    if 'selected_folders' in st.session_state:
        st.session_state.selected_folders = []
    if 'upload_selected_folders' in st.session_state:
        st.session_state.upload_selected_folders = []
    st.rerun()

# Function to show reset cache button
def show_reset_cache_button():
    if st.button("Reset Cache", key="reset_cache"):
        reset_cache()
    if 'cache_reset' in st.session_state and st.session_state.cache_reset:
        st.toast('Cache telah di-reset!', icon='🔄')
        st.session_state.cache_reset = False

# Function to log activity
def log_activity(activity):
    st.session_state.activity.append(
        f"{st.session_state.name} {activity} at {datetime.datetime.now().strftime('%d %B %Y %H:%M')}"
    )
    # Update Logs worksheet
    if st.session_state.logged_in:
        conn.set_service_account_info(service_account_info)
        conn.write(data=pd.DataFrame(st.session_state.activity), spreadsheet=spreadsheet_key, worksheet='Logs')

# Login function
def login():
    st.write('Please login')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    if st.button("Log in"):
        # Check if the username and password match any entry in the DataFrame
        user_row = st.session_state.database[
            (st.session_state.database['Username'] == username) & (st.session_state.database['Password'] == password)
        ]
        if not user_row.empty:
            st.session_state.logged_in = True
            st.session_state.role = user_row.iloc[0]['Role']
            st.session_state.name = user_row.iloc[0]['Name']
            log_activity("logged in")
            st.success(f"Welcome, {st.session_state.role}!")
            time.sleep(0.3)
            st.rerun()
        else:
            st.error('Username/password is incorrect')
    show_reset_cache_button()

# Logout function
def logout():
    st.table(pd.DataFrame({'Your Activity': st.session_state.activity}))
    if st.button("Log out"):
        log_activity("logged out")
        st.session_state.logs.extend(st.session_state.activity)
        new_logs_df = pd.DataFrame({'Activity': st.session_state.logs})
        # Update Logs sheet with new activity data
        # (Code to update the sheet would be added here)
        st.session_state.activity = []
        st.session_state.selected_folders = []
        st.session_state.name = None
        st.session_state.role = None
        st.session_state.logged_in = False
        st.rerun()

# Define login and logout pages
login_page = st.Page(login, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

# Define admin and user pages
# Admin pages
create_update_page = st.Page("Admin/Create_Update.py", title="Create", icon=":material/add_circle:", default=True)
read_page = st.Page("Admin/Read.py", title="Read", icon=":material/table:")
delete_page = st.Page("Admin/Delete.py", title="Delete", icon=":material/delete_forever:")
maintenance_page = st.Page("Admin/Maintenance.py", title="Maintenance", icon=":material/engineering:")

# User pages
create_update_user_page = st.Page("User/Create_Update.py", title="Create", icon=":material/add_circle:", default=True)
read_user_page = st.Page("User/Read.py", title="Read", icon=":material/table:")

# Pagination logic
if st.session_state.logged_in and st.session_state.role == 'ADMIN':
    # Admin pages navigation
    pg = st.navigation(
        {
            "Operations": [create_update_page, read_page, delete_page, maintenance_page],
            "Account": [logout_page]
        }
    )
elif st.session_state.logged_in and st.session_state.role == 'USER':
    # User pages navigation
    pg = st.navigation(
        {
            "Operations": [create_update_user_page, read_user_page],
            "Account": [logout_page]
        }
    )
else:
    pg = st.navigation([login_page])

pg.run()

# Logging folder access
if 'selected_folders' in st.session_state:
    log_activity(f"accessed folder {st.session_state.selected_folders[-1]['title'] if st.session_state.selected_folders else 'root'}")