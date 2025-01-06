import json
import base64
import streamlit as st 

import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials

# Read secrets
spreadsheet_id = st.secrets["connections"]["gsheets"]["spreadsheet"]
service_account_info = st.secrets["service_account"]

# Set up credentials and client
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
client = gspread.authorize(credentials)

# Access the spreadsheet and worksheet
spreadsheet = client.open_by_key(spreadsheet_id)
worksheet = spreadsheet.worksheet('Users')
data = get_as_dataframe(worksheet)
print(st.secrets["service_account"])