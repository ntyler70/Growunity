import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import re

# ------------------------------
# Google Sheets Connection
# ------------------------------
SHEET_NAME = "growunity_datalogs"
JSON_KEYFILE = "C:\\Users\\tyler\\OneDrive\\Documents\\Gardening_project\\credentials.json"

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
service_account_info = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(service_account_info)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# ------------------------------
# Streamlit Interface
# ------------------------------
st.set_page_config(page_title="GrowUnity", page_icon="🌱")
st.title("GrowUnity")
st.subheader("Collaborative Plant Data Logs")

st.markdown("""
GrowUnity brings together beginner and expert gardeners to share plant care data.  
Enter your plant’s growth and watering information below.  
If a field doesn’t apply, type **N/A**.
""")

# ------------------------------
# Helper: validate email
# ------------------------------
def is_valid_email(email):
    """Returns True if the string is a valid email format."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None

# ------------------------------
# Initialize session state
# ------------------------------
if "num_logs" not in st.session_state:
    st.session_state.num_logs = 1

if st.button("Add Log"):
    st.session_state.num_logs += 1

# ------------------------------
# Data Entry Form
# ------------------------------
with st.form("data_entry_form"):
    email = st.text_input("Your Email (used as your GrowUnity ID)")
    experience = st.selectbox("Your Experience Level", ["Beginner", "Intermediate", "Expert"])
    plant_name = st.text_input("Proper Botanical Name (ex: Ficus lyrata) ")
    description = st.text_area("General Description or Notes (fertilizer, sunlight, etc.)")

    data_entries = []
    for i in range(st.session_state.num_logs):
        st.write(f"### Log {i+1}")
        log_date = st.date_input(f"Date of log {i+1}", value=datetime.today(), key=f"date{i}")
        height = st.text_input(f"Height (cm) for log {i+1}", value="N/A", key=f"h{i}")
        watering = st.text_input(f"Watering frequency (liters) for log {i+1}", value="N/A", key=f"w{i}")
        notes = st.text_area(f"Additional notes for log {i+1}", value="N/A", key=f"n{i}")
        data_entries.append((log_date, height, watering, notes))

    submitted = st.form_submit_button("Submit Data")

# ------------------------------
# Data Upload
# ------------------------------
if submitted:
    if not is_valid_email(email):
        st.error("Please enter a valid email address.")
    elif plant_name.strip() == "":
        st.error("Please fill in your plant name.")
    else:
        rows_to_add = []
        for date, height, watering, notes in data_entries:
            rows_to_add.append([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                email,
                experience,
                plant_name,
                date.strftime("%Y-%m-%d"),
                height,
                watering,
                notes,
                description
            ])

        # Append to Google Sheet
        sheet.append_rows(rows_to_add)
        st.success("✅ Data successfully submitted to GrowUnity!")

        st.info(f"Use your email **{email}** on the visualization page to view your data.")
        st.dataframe(pd.DataFrame(rows_to_add, columns=[
            "Timestamp", "Email", "Experience", "Plant", "Date", "Height (cm)",
            "Watering", "Notes", "General Description"
        ]))
