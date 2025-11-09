from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ---- Google Sheets Setup ----
SERVICE_ACCOUNT_FILE = "veggiebot-key.json"  # ← your JSON filename
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open("Veggie_Orders").sheet1  # must match your sheet name

# ---- Flask App ----
app = Flask(__name__)

# Store chat states (in memory for now)
user_states = {}

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    from_number = request.values.get("From", "")
    incoming_msg = request.values.get("Body", "").strip()
    resp = MessagingResponse()
    msg = resp.message()

    # Initialize new user
    if from_number not in user_states:
        user_states[from_number] = {"stage": "ask_name"}
        msg.body("👋 Welcome to Marr’s Veggie Orders 🥬!\nPlease tell me your *name* to start your order.")
        return str(resp)

    state = user_states[from_number]

    # ---- Stage 1: Get name ----
    if state["stage"] == "ask_name":
        state["name"] = incoming_msg
        state["stage"] = "ask_bundles"
        msg.body(f"Nice to meet you, {state['name']}! 🧺\nHow many *bundles* would you like to order?")
        return str(resp)

    # ---- Stage 2: Get bundle count ----
    elif state["stage"] == "ask_bundles":
        state["bundles"] = incoming_msg
        state["stage"] = "ask_delivery"
        msg.body("Got it ✅\nWhen should we *deliver* your veggies? (e.g. Saturday 3PM)")
        return str(resp)

    # ---- Stage 3: Get delivery time and save ----
    elif state["stage"] == "ask_delivery":
        state["delivery_time"] = incoming_msg

        # Save to Google Sheet
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([
            state["name"],
            state["bundles"],
            state["delivery_time"],
            from_number.replace("whatsapp:", ""),
            timestamp
        ])

        msg.body(
            f"✅ Order confirmed!\n\n"
            f"👤 Name: {state['name']}\n"
            f"🥬 Bundles: {state['bundles']}\n"
            f"🕒 Delivery: {state['delivery_time']}\n\n"
            "We’ll deliver this weekend 🚚\nThank you for supporting Marr’s Veggie Orders! 💚"
        )

        # Reset their state
        del user_states[from_number]
        return str(resp)

    else:
        msg.body("Type 'hi' to start a new order 🥦")
        del user_states[from_number]
        return str(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
