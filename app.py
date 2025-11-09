# ---- Imports ----
import os
import json
from datetime import datetime
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import gspread
from google.oauth2.service_account import Credentials

# ---- Google Sheets Configuration ----
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from environment variable (for production)
# or fallback to local file (for development)
try:
    creds_json = json.loads(os.getenv("GOOGLE_CREDS_JSON"))
    creds = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
except (TypeError, json.JSONDecodeError):
    # Fallback to local file for development
    creds = Credentials.from_service_account_file("veggiebot-key.json", scopes=SCOPES)

client = gspread.authorize(creds)
sheet = client.open("Veggie_Orders").sheet1

# ---- Flask App ----
app = Flask(__name__)

# ---- In-Memory User State Storage ----
user_states = {}

# ---- Helper Functions ----
def save_order_to_sheet(state, phone_number):
    """Save order details to Google Sheet"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_delivery = f"{state['delivery_day']} {state['delivery_time']}"
    sheet.append_row([
        state["name"],
        state["bundles"],
        full_delivery,
        phone_number.replace("whatsapp:", ""),
        timestamp
    ])

def reset_user_state(phone_number):
    """Remove user state after order completion"""
    if phone_number in user_states:
        del user_states[phone_number]

# ---- WhatsApp Webhook Endpoint ----
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    """Handle incoming WhatsApp messages"""
    from_number = request.values.get("From", "")
    incoming_msg = request.values.get("Body", "").strip()
    resp = MessagingResponse()
    msg = resp.message()

    # Initialize new user
    if from_number not in user_states:
        user_states[from_number] = {"stage": "ask_name"}
        msg.body("👋 Welcome to Marr's Veggie Orders 🥬!\nPlease tell me your *name* to start your order.")
        return str(resp)

    state = user_states[from_number]

    # ---- Stage 1: Get Customer Name ----
    if state["stage"] == "ask_name":
        state["name"] = incoming_msg
        state["stage"] = "ask_bundles"
        msg.body(f"Nice to meet you, {state['name']}! 🧺\nHow many *bundles* would you like to order?")
        return str(resp)

    # ---- Stage 2: Get Bundle Count ----
    elif state["stage"] == "ask_bundles":
        state["bundles"] = incoming_msg
        state["stage"] = "ask_delivery_day"
        msg.body(
            "Got it ✅\nPlease choose a *delivery day*:\n"
            "1️⃣ Saturday\n"
            "2️⃣ Sunday"
        )
        return str(resp)

    # ---- Stage 3: Get Delivery Day ----
    elif state["stage"] == "ask_delivery_day":
        choice = incoming_msg.strip().lower()
        if choice in ["1", "saturday"]:
            state["delivery_day"] = "Saturday"
        elif choice in ["2", "sunday"]:
            state["delivery_day"] = "Sunday"
        else:
            msg.body("❌ Invalid option. Please reply with *1 for Saturday* or *2 for Sunday*.")
            return str(resp)

        state["stage"] = "ask_delivery_time"
        msg.body(f"Cool 😎\nWhat *time* on {state['delivery_day']} would you like your veggies delivered? (e.g. 2 PM)")
        return str(resp)

    # ---- Stage 4: Get Delivery Time and Confirm Order ----
    elif state["stage"] == "ask_delivery_time":
        state["delivery_time"] = incoming_msg
        full_delivery = f"{state['delivery_day']} {state['delivery_time']}"

        # Save to Google Sheet
        save_order_to_sheet(state, from_number)

        # Send confirmation message
        msg.body(
            f"✅ Order confirmed!\n\n"
            f"👤 Name: {state['name']}\n"
            f"🥬 Bundles: {state['bundles']}\n"
            f"🕒 Delivery: {full_delivery}\n\n"
            "We'll deliver this weekend 🚚\nThank you for supporting Marr's Veggie Orders! 💚"
        )

        # Reset user state
        reset_user_state(from_number)
        return str(resp)

    # ---- Fallback: Unknown Stage ----
    else:
        msg.body("Type 'hi' to start a new order 🥦")
        reset_user_state(from_number)
        return str(resp)

# ---- Run Flask App ----
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
