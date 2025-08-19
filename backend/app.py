from flask import Flask, request, jsonify, abort
import csv
import os
from flask_cors import CORS
from twilio.rest import Client
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
CORS(app)

ITEMS_FILE = "data/items.csv"
USERS_FILE = "users.csv"

# ---------------- CONFIG ----------------
# Twilio Config
TWILIO_SID = "your_twilio_sid"
TWILIO_AUTH = "your_twilio_auth"
TWILIO_PHONE = "+1234567890"   # Twilio phone number

# Email Config
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = "adityapatel8698@gmail.com"
EMAIL_PASS = "qokb fiwy dzlz ljcx"

# ---------------- Helper Functions ----------------
def read_items():
    items = []
    if os.path.exists(ITEMS_FILE):
        with open(ITEMS_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                item = {
                    "id": row.get("id", ""),
                    "title": row.get("title", "Untitled Item"),
                    "description": row.get("description", ""),
                    "category": row.get("category", ""),
                    "location": row.get("location", ""),
                    "status": row.get("status", "open"),
                    "type": row.get("type", ""),
                    "lost_date": row.get("lost_date", ""),
                    "found_date": row.get("found_date", ""),
                    "image_url": row.get("image_url", ""),
                    "contact_name": row.get("contact_name", ""),
                    "contact_email": row.get("contact_email", ""),
                    "contact_phone": row.get("contact_phone", "")
                }
                items.append(item)
    return items


def write_items(items):
    fieldnames = [
        "id", "title", "description", "category", "location",
        "status", "type", "lost_date", "found_date", "image_url",
        "contact_name", "contact_email", "contact_phone"
    ]
    with open(ITEMS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)


def read_users():
    users = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                users.append(row)
    return users


def write_users(users):
    fieldnames = ["id", "name", "email", "password", "role"]
    with open(USERS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)

# ---------------- Notifications ----------------
def send_sms(to, message):
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH)
        client.messages.create(to=to, from_=TWILIO_PHONE, body=message)
        print(f"SMS sent to {to}")
    except Exception as e:
        print(f"SMS failed: {e}")

def send_email(to, subject, body):
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = to

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)  # Use App Password here
            server.sendmail(EMAIL_USER, [to], msg.as_string())
        
        print(f"✅ Email sent to {to}")
    except Exception as e:
        print(f"❌ Email failed: {e}")


# ----------- Matching Logic -------------
def check_and_match_items():
    items = read_items()
    changed = False

    lost_items = [i for i in items if i["type"].lower() == "lost" and i["status"] == "lost"]
    found_items = [i for i in items if i["type"].lower() == "found" and i["status"] == "found"]

    for lost in lost_items:
        for found in found_items:
            if (
                lost["title"].strip().lower() == found["title"].strip().lower() and
                lost["description"].strip().lower() == found["description"].strip().lower() and
                lost["category"].strip().lower() == found["category"].strip().lower() 
                
            ):
                lost["status"] = "matched"
                found["status"] = "matched"
                changed = True

                # Send notifications to lost item owner
                msg = f"Good news {lost['contact_name']}! Your lost item '{lost['title']}' has been found by {found['contact_name']}.\nContact: {found['contact_phone']} / {found['contact_email']}"

                if lost["contact_phone"]:
                    send_sms(lost["contact_phone"], msg)
                if lost["contact_email"]:
                    send_email(lost["contact_email"], "Lost & Found Match Found!", msg)

    if changed:
        write_items(items)

# ----------------- API Routes -----------------
@app.route("/api/items", methods=["GET"])
def get_items():
    return jsonify(read_items())

@app.route("/api/items", methods=["POST"])
def create_item():
    data = request.get_json()
    items = read_items()
    new_id = str(len(items) + 1)
    data["id"] = new_id
    data.setdefault("status", data.get("type", "open"))
    items.append(data)
    write_items(items)

    # Check matches after saving
    check_and_match_items()

    return jsonify({"message": "Item saved successfully", "id": new_id}), 201

@app.route("/api/stats", methods=["GET"])
def get_stats():
    items = read_items()
    total_items = len(items)
    lost_items = sum(1 for i in items if i["type"].lower() == "lost")
    found_items = sum(1 for i in items if i["type"].lower() == "found")
    matched_items = sum(1 for i in items if i["status"] == "matched")
    return jsonify({
        "total_items": total_items,
        "lost_items": lost_items,
        "found_items": found_items,
        "matched_items": matched_items
    })

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    users = read_users()
    new_id = str(len(users) + 1)
    data["id"] = new_id
    data.setdefault("role", "student")
    users.append(data)
    write_users(users)
    return jsonify({"message": "User registered successfully", "id": new_id}), 201

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    users = read_users()
    for u in users:
        if u["email"] == email and u["password"] == password:
            return jsonify({
                "message": "Login successful",
                "role": u.get("role", "student"),
                "name": u.get("name", ""),
                "id": u.get("id", "")
            })
    abort(401, "Invalid credentials")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
