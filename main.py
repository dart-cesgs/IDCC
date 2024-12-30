import streamlit as st
from io import BytesIO
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import time
import datetime
from Admin.Admin_Operation import get_list_of_all_folders
from User.User_Operation import get_list_of_all_folders_forusers

# Streamlit App
st.title("Google Drive File Manager")

# Koneksi ke Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(worksheet='Users', ttl=1800)
logs_data = conn.read(worksheet='Logs', ttl=1800)
data['Password'] = data['Password'].astype(int).astype(str)

# Define session state jika belum ada
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if 'role' not in st.session_state:
    st.session_state.role = None

if 'name' not in st.session_state:
    st.session_state.name = None

if 'connection' not in st.session_state:
    st.session_state.connection = None

if 'database' not in st.session_state:
    st.session_state.database = data

if 'logs' not in st.session_state:
    st.session_state.logs = logs_data['Activity'].values.tolist()

if 'activity' not in st.session_state:
    st.session_state.activity = []

if 'folder' not in st.session_state:
    st.session_state.folder = []

if 'cache_reset' not in st.session_state:
    st.session_state.cache_reset = False

# Fungsi untuk reset cache
def reset_cache():
    st.cache_data.clear()
    st.session_state.cache_reset = True
    if 'selected_folders' in st.session_state:
        st.session_state.selected_folders = []
    if 'upload_selected_folders' in st.session_state:
        st.session_state.upload_selected_folders = []
    st.rerun()

# Fungsi untuk menampilkan tombol Reset Cache
def show_reset_cache_button():
    if st.button("Reset Cache", key="reset_cache"):
        reset_cache()
    
    if st.session_state.cache_reset:
        st.toast('Cache telah di-reset!', icon='🔄')
        st.session_state.cache_reset = False

# Fungsi untuk mencatat aktivitas
def log_activity(activity):
    st.session_state.activity.append(
        f"{st.session_state.name} {activity} at {datetime.datetime.now().strftime('%d %B %Y %H:%M')}"
    )

# Fungsi Login
def login():
    st.write('Please login')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    if st.button("Log in"):
        # Check if the username and password match any entry in the DataFrame
        user_row = data[(data['Username'] == username) & (data['Password'] == password)]
        
        if not user_row.empty:
            # Tetapkan role (ADMIN/USER) berdasarkan Google Sheets
            st.session_state.logged_in = True
            st.session_state.connection = conn
            st.session_state.role = user_row.iloc[0]['Role']
            st.session_state.name = user_row.iloc[0]['Name']
            log_activity("logged in")
            st.success(f"Welcome, {st.session_state.role}!")
            time.sleep(0.3)
            st.rerun()
        else:
            # Jika tidak cocok, tampilkan error
            st.error('Username/password is incorrect')
    show_reset_cache_button()  # Tampilkan tombol reset cache


# Fungsi Logout
def logout():
    st.table(pd.DataFrame({'Your Activity': st.session_state.activity}))
    if st.button("Log out"):
        log_activity("logged out")
        st.session_state.logs.extend(st.session_state.activity)
        new_data = pd.DataFrame({'Activity': st.session_state.logs})
        st.session_state.connection.update(data=new_data, worksheet='Logs')
        st.session_state.activity = []
        st.session_state.selected_folders = []
        st.session_state.name = None
        st.session_state.role = None
        st.session_state.logged_in = False
        st.rerun()

# DEFINE LOGIN - LOGOUT PAGES
login_page = st.Page(login, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

# DEFINE ADMIN PAGES
create_update_page = st.Page("Admin/Create_Update.py", title="Create", icon=":material/add_circle:", default=True)
read_page = st.Page("Admin/Read.py", title="Read", icon=":material/table:")
delete_page = st.Page("Admin/Delete.py", title="Delete", icon=":material/delete_forever:")
maintenance_page = st.Page("Admin/Maintenance.py", title="Maintenance", icon=":material/engineering:")

# DEFINE USER PAGES
create_update_user_page = st.Page("User/Create_Update.py", title="Create", icon=":material/add_circle:", default=True)
read_user_page = st.Page("User/Read.py", title="Read", icon=":material/table:")

# PAGINATION
if st.session_state.logged_in and st.session_state.role == 'ADMIN':
    st.session_state.folder = get_list_of_all_folders()
    pg = st.navigation(
        {
            "Operations": [create_update_page, read_page, delete_page, maintenance_page],
            "Account": [logout_page]
        }
    )

elif st.session_state.logged_in and st.session_state.role == 'USER':
    st.session_state.folder = get_list_of_all_folders_forusers()
    pg = st.navigation(
        {
            "Operations": [create_update_user_page, read_user_page],
            "Account": [logout_page]
        }
    )
else:
    pg = st.navigation([login_page])

pg.run()

# Tambahkan logging saat file atau folder diakses
if 'selected_folders' in st.session_state:
    log_activity(f"accessed folder {st.session_state.selected_folders[-1]['title'] if st.session_state.selected_folders else 'root'}")
