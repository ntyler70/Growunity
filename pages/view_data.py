# view_data.py
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
from datetime import datetime

# ------------------------------
# Google Sheets Connection
# ------------------------------
SHEET_NAME = "growunity_datalogs"  # Must match your Google Sheet title
JSON_KEYFILE = "C:\\Users\\tyler\\OneDrive\\Documents\\Gardening_project\\credentials.json"

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
service_account_info = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(service_account_info,scopes=scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# ------------------------------
# Load Data
# ------------------------------
data = sheet.get_all_records()
df = pd.DataFrame(data)

if df.empty:
    st.warning("No data available yet!")
    st.stop()

# ------------------------------
# User Input
# ------------------------------
st.title("GrowUnity — View Your Data")
user_email = st.text_input("Enter your GrowUnity email")

if user_email:
    if "Email" not in df.columns:
        st.error("Google Sheet does not have an 'Email' column, Check your headers.")
        st.stop()

    user_df = df[df["Email"].str.lower() == user_email.strip().lower()].copy()

    if user_df.empty:
        st.info("No data found for that email. Please check your spelling or submission email, but sometimes you may need to refresh.")
        st.stop()

    # Convert Date to datetime
    user_df["Date"] = pd.to_datetime(user_df["Date"], errors='coerce')
    user_df = user_df.sort_values("Date")

    # ------------------------------
    # Plant Selection
    # ------------------------------
    plants = user_df["Plant"].unique()
    selected_plant = st.selectbox("Select a plant to view growth", plants)

    plant_df = user_df[user_df["Plant"] == selected_plant].copy()

    # ------------------------------
    # Clean numeric height
    # ------------------------------
    plant_df["Height_num"] = pd.to_numeric(
        plant_df["Height (cm)"].replace("N/A", ""), errors="coerce"
    )

    # ------------------------------
    # Plot Growth Over Time
    # ------------------------------
    if plant_df["Height_num"].notna().any():
        st.subheader(f"Growth of {selected_plant} Over Time")
        plt.figure(figsize=(8, 4))
        plt.plot(plant_df["Date"], plant_df["Height_num"], marker='o', linestyle='-')
        plt.title(f"{selected_plant} Growth Over Time")
        plt.xlabel("Date")
        plt.ylabel("Height (cm)")
        plt.xticks(rotation=45)
        st.pyplot(plt)
    else:
        st.info("No numeric height data available for this plant.")

    # ------------------------------
    # Optional Additional Data
    # ------------------------------
    if st.checkbox("Show additional logs (watering, notes)"):
        st.subheader(f"Additional Data for {selected_plant}")
        display_df = plant_df[["Date", "Watering", "Notes"]].replace("N/A", "")
        st.dataframe(display_df)

    # ------------------------------
    # 🌿 Smart Insights Section
    # ------------------------------
    def generate_insights(df):
        """Generate simple context-aware insights from user plant data."""
        insights = []

        df["Height_num"] = pd.to_numeric(df["Height (cm)"].replace("N/A", None), errors="coerce")

        # Growth analysis
        if df["Height_num"].notna().sum() >= 2:
            growth_change = df["Height_num"].iloc[-1] - df["Height_num"].iloc[0]
            if growth_change > 0:
                insights.append(f"Your plant grew by **{growth_change:.1f} cm** since the first log, which is steady progress!")
            elif growth_change < 0:
                insights.append(f"Your plant's height decreased by **{abs(growth_change):.1f} cm** — consider checking sunlight, soil, or watering levels. ☀️💧")
            else:
                insights.append("No significant change in height yet, but consistent monitoring helps spot trends early.")
        else:
            insights.append("Not enough numeric height data to analyze growth trends.")

        # Watering pattern insight
        if "Watering" in df.columns:
            watering_values = [w for w in df["Watering"] if isinstance(w, str) and w.strip().lower() != "n/a"]
            if watering_values:
                avg_len = sum(len(w) for w in watering_values) / len(watering_values)
                if avg_len > 8:
                    insights.append("Detailed watering notes detected, great for consistency")
                else:
                    insights.append("Try logging more details about watering frequency and amount.")
            else:
                insights.append("No watering data logged yet — water tracking helps improve growth results.")

        # Notes quality insight
        if "Notes" in df.columns and df["Notes"].notna().any():
            non_empty_notes = df["Notes"].replace("N/A", "").astype(str).str.strip()
            if non_empty_notes.str.len().mean() > 20:
                insights.append("Thanks for documenting notes and changes!")
            else:
                insights.append("Consider adding more detailed notes to better track environmental conditions.")

        return insights

    # ------------------------------
    # Display Smart Insights
    # ------------------------------
    st.subheader("Smart Insights")
    insights = generate_insights(plant_df)
    for i in insights:
        st.write("- " + i)
