import streamlit as st
import requests
import datetime
import csv
import os
import pandas as pd  # for creating DataFrame

# ===== CONFIG =====
API_BASE = "http://127.0.0.1:5000"  # Change if running on LAN
USERS_FILE = "users.csv"

st.set_page_config(page_title="College Lost & Found Tracker", layout="wide")

# ===== CSV UTILITIES =====
def save_user_login(role, email):
    file_exists = os.path.exists(USERS_FILE)
    with open(USERS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["role", "email", "login_time"])
        writer.writerow([role, email, datetime.datetime.now().isoformat()])

# ===== API UTILITIES =====
def fetch_items():
    try:
        r = requests.get(f"{API_BASE}/api/items")
        if r.status_code == 200:
            return r.json()
        return []
    except Exception as e:
        st.error(f"Error fetching items: {e}")
        return []

def fetch_stats():
    try:
        r = requests.get(f"{API_BASE}/api/stats")
        if r.status_code == 200:
            return r.json()
        return {}
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
        return {}

def submit_report(data):
    try:
        r = requests.post(f"{API_BASE}/api/items", json=data)
        if r.status_code in (200, 201):
            return True
        st.error(f"Failed to submit: {r.text}")
        return False
    except Exception as e:
        st.error(f"Error submitting: {e}")
        return False

# ===== SESSION STATE =====
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.email = ""
    st.session_state.show_report_form = False

# ===== LOGIN =====
if not st.session_state.logged_in:
    st.title("🔐 Student Login")
    email = st.text_input("Student Email", key="student_email")
    password = st.text_input("Password", type="password", key="student_password")
    if st.button("Login"):
        if email and password:
            st.session_state.logged_in = True
            st.session_state.email = email
            save_user_login("student", email)
            st.rerun()
        else:
            st.warning("Enter both email and password")

# ===== MAIN APP =====
else:
    st.sidebar.write(f"Logged in as: **{st.session_state.email}** (Student)")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.show_report_form = False
        st.rerun()

    st.title("📊 Lost & Found Dashboard")

    # Show stats
    stats = fetch_stats()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Items", stats.get("total_items", 0))
    col2.metric("Lost Items", stats.get("lost_items", 0))
    col3.metric("Found Items", stats.get("found_items", 0))
    col4.metric("Matches", stats.get("matched_items", 0))

        # Show items list in a standard table with images + description
    st.subheader("📋 All Reported Items")
    items = fetch_items()
    if items:
        # Convert items into DataFrame
        df = pd.DataFrame(items)

        # Ensure all expected columns exist
        expected_cols = [
            "id", "title", "description", "type", "category", "location", "status",
            "lost_date", "found_date", "contact_name", "contact_email",
            "contact_phone", "image_url"
        ]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""

        # Reorder columns explicitly
        df = df[expected_cols]

        # Show images as thumbnails
        def image_formatter(url):
            if url:
                return f'<img src="{url}" width="80">'
            return "❌"

        # Row highlighting (green for matched)
        def highlight_row(row):
            if row["status"] == "matched":
                return ['background-color: lightgreen'] * len(row)
            elif row["status"] == "lost":
                return ['background-color: #ffcccc'] * len(row)  # light red
            elif row["status"] == "found":
                return ['background-color: #cce5ff'] * len(row)  # light blue
            return [''] * len(row)

        st.write(
            df.style.apply(highlight_row, axis=1)
                   .format({"image_url": image_formatter})
                   .hide(axis="index")
                   .to_html(escape=False),
            unsafe_allow_html=True
        )


    else:
        st.info("No items found.")

    # Button to toggle report form
    if st.button("➕ Report Lost/Found Item"):
        st.session_state.show_report_form = not st.session_state.show_report_form

    # Report form (shows only if toggled)
    if st.session_state.show_report_form:
        st.subheader("📝 Report Lost or Found Item")
        with st.form("report_form"):
            title = st.text_input("Item Title")
            description = st.text_area("Description")
            item_type = st.selectbox("Type", ["lost", "found","matched"])
            category = st.selectbox("Category", ["books", "electronics", "id_cards", "clothing", "accessories", "other"])
            location = st.text_input("Location")
            image_url = st.text_input("Image URL (optional)", value="https://placehold.co/150x100?text=No+Image")

            # Contact info fields
            contact_name = st.text_input("Your Name")
            contact_email = st.text_input("Your Email")
            contact_phone = st.text_input("Your Phone")

            # Conditional date pickers
            lost_date, found_date = "", ""
            if item_type == "lost":
                lost_date = st.date_input("Lost Date", datetime.date.today())
            elif item_type == "found":
                found_date = st.date_input("Found Date", datetime.date.today())

            submitted = st.form_submit_button("Submit Report", type="primary")
            if submitted:
                data = {
                    "title": title,
                    "description": description,
                    "type": item_type,
                    "category": category,
                    "location": location,
                    "image_url": image_url,
                    "contact_name": contact_name,
                    "contact_email": contact_email,
                    "contact_phone": contact_phone,
                    "status": item_type,  # save as lost/found
                    "lost_date": str(lost_date) if lost_date else "",
                    "found_date": str(found_date) if found_date else ""
                }
                if submit_report(data):
                    st.success("Report submitted successfully!")
                    st.session_state.show_report_form = False
                    st.rerun()
