# ---- Imports ----
import os
import json
import re
import secrets
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
# Store last order for each user (for modifications)
last_orders = {}

# ---- Configuration ----
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "")  # Set in Render env variables

# ---- Helper Functions ----
def generate_order_id():
    """Generate a unique 6-character order ID"""
    return secrets.token_hex(3).upper()

def validate_bundle_count(text):
    """Validate that bundle count is a positive number"""
    try:
        count = int(text)
        if count <= 0:
            return False, "Please enter a positive number of bundles!"
        if count > 50:
            return False, "That's a lot of veggies! 😅 Please order 50 or fewer bundles."
        return True, count
    except ValueError:
        return False, "Please enter a valid number (e.g., 1, 2, 3, etc.)"

def save_order_to_sheet(state, phone_number):
    """Save order details to Google Sheet with error handling"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_delivery = f"{state['delivery_day']} {state['delivery_time']}"
        order_id = state.get('order_id', generate_order_id())
        
        sheet.append_row([
            order_id,
            state["name"],
            state["bundles"],
            full_delivery,
            phone_number.replace("whatsapp:", ""),
            timestamp,
            "Confirmed"
        ])
        
        # Store last order for this user
        last_orders[phone_number] = {
            'order_id': order_id,
            'name': state['name'],
            'bundles': state['bundles'],
            'delivery': full_delivery,
            'timestamp': timestamp
        }
        
        return True, order_id
    except Exception as e:
        print(f"Error saving to sheet: {e}")
        return False, None

def send_admin_notification(state, phone_number, order_id):
    """Send notification to admin about new order (optional)"""
    # This would require Twilio client setup, keeping it simple for now
    pass

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

    # Check for restart command
    if incoming_msg.lower() in ["hi", "hello", "start", "restart"]:
        user_states[from_number] = {"stage": "ask_name"}
        msg.body("👋 Welcome to Marr's Veggie Orders 🥬!\nPlease tell me your *name* to start your order.")
        return str(resp)
    
    # Check for view order command
    if incoming_msg.lower() in ["view", "my order", "order status"]:
        if from_number in last_orders:
            order = last_orders[from_number]
            msg.body(
                f"📦 Your Last Order:\n\n"
                f"🆔 Order ID: {order['order_id']}\n"
                f"👤 Name: {order['name']}\n"
                f"🥬 Bundles: {order['bundles']}\n"
                f"🕒 Delivery: {order['delivery']}\n\n"
                "Reply *CANCEL* to cancel this order\n"
                "or *HI* to place a new order 🥦"
            )
        else:
            msg.body("You don't have any recent orders. Type *HI* to place a new order! 🥬")
        return str(resp)
    
    # Check for cancel order command
    if incoming_msg.lower() == "cancel" and from_number in last_orders:
        order = last_orders[from_number]
        msg.body(
            f"❌ Order {order['order_id']} has been cancelled.\n\n"
            "Note: If you need to cancel within 24 hours of delivery, "
            "please contact us directly.\n\n"
            "Type *HI* to place a new order! 🥦"
        )
        del last_orders[from_number]
        return str(resp)

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
        # Validate bundle count
        is_valid, result = validate_bundle_count(incoming_msg)
        if not is_valid:
            msg.body(f"❌ {result}\nPlease enter how many bundles you'd like:")
            return str(resp)
        
        state["bundles"] = result
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

        # Save to Google Sheet with error handling
        success, order_id = save_order_to_sheet(state, from_number)
        
        if not success:
            msg.body(
                "⚠️ Sorry, there was an issue saving your order.\n"
                "Please try again later or contact support.\n\n"
                "Your order details:\n"
                f"👤 {state['name']}\n"
                f"🥬 {state['bundles']} bundles\n"
                f"🕒 {full_delivery}"
            )
            reset_user_state(from_number)
            return str(resp)
        
        # Store order ID in state for reference
        state['order_id'] = order_id

        # Send confirmation message with order ID
        msg.body(
            f"✅ Order Confirmed!\n\n"
            f"🆔 Order ID: *{order_id}*\n"
            f"👤 Name: {state['name']}\n"
            f"🥬 Bundles: {state['bundles']}\n"
            f"🕒 Delivery: {full_delivery}\n\n"
            "We'll deliver this weekend 🚚\n\n"
            "💡 *Commands:*\n"
            "• Type *VIEW* to see your order\n"
            "• Type *CANCEL* to cancel\n"
            "• Type *HI* for a new order\n\n"
            "Thank you for supporting Marr's Veggie Orders! 💚"
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
