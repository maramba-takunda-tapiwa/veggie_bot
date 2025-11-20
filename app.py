"""
FoodStream Veggies Bot - Enhanced WhatsApp Ordering System
A production-ready bot for managing vegetable orders via WhatsApp

Features:
- Persistent state management with Redis
- Dynamic pricing with volume discounts
- Order modification and tracking
- Admin notifications
- Input validation and security
- Rate limiting
"""

# ---- Imports ----
import os
import json
import logging
from datetime import datetime
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
import gspread
from google.oauth2.service_account import Credentials

# Import our custom modules
from config import Config
from state_manager import create_state_manager
from validators import (
    validate_bundle_count, validate_postcode, validate_address,
    validate_name, validate_delivery_slot_choice, validate_order_id
)
from pricing import pricing_engine
from notifications import admin_notifier
from utils import (
    generate_order_id, sanitize_text, format_phone_number,
    format_timestamp, rate_limit, parse_yes_no, create_numbered_list,
    get_greeting_for_time
)

# ---- Logging Configuration ----
logging.basicConfig(
    level=logging.INFO if not Config.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---- Validate Configuration ----
try:
    Config.validate()
    Config.log_config()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    logger.warning("Some features may not work correctly")

# ---- Google Sheets Configuration ----
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from environment variable (production) or local file (development)
try:
    if Config.GOOGLE_CREDS_JSON:
        creds_json = json.loads(Config.GOOGLE_CREDS_JSON)
        creds = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file("veggiebot-key.json", scopes=SCOPES)
    
    client = gspread.authorize(creds)
    sheet = client.open(Config.GOOGLE_SHEET_NAME).sheet1
    logger.info(f"✅ Google Sheets connected: {Config.GOOGLE_SHEET_NAME}")
except Exception as e:
    logger.error(f"Failed to connect to Google Sheets: {e}")
    sheet = None

# ---- Initialize State Manager ----
state_manager = create_state_manager(
    redis_enabled=Config.REDIS_ENABLED,
    redis_url=Config.REDIS_URL,
    expiration_hours=Config.STATE_EXPIRATION_HOURS
)

# ---- Initialize Twilio Validator (for webhook security) ----
twilio_validator = None
if Config.TWILIO_AUTH_TOKEN:
    twilio_validator = RequestValidator(Config.TWILIO_AUTH_TOKEN)

# ---- Flask App ----
app = Flask(__name__)

# ---- Health Check Endpoint ----
@app.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": f"{Config.BOT_NAME} Bot",
        "version": "2.0",
        "features": {
            "redis_enabled": Config.REDIS_ENABLED,
            "admin_notifications": Config.ADMIN_NOTIFICATIONS_ENABLED,
            "order_modification": Config.ENABLE_ORDER_MODIFICATION,
            "order_tracking": Config.ENABLE_ORDER_TRACKING
        },
        "endpoints": {
            "whatsapp": "/whatsapp (POST)"
        }
    }, 200


# ---- Helper Functions ----
def validate_twilio_request(request_data) -> bool:
    """
    Validate that request actually came from Twilio
    
    Args:
        request_data: Flask request object
    
    Returns:
        True if valid, False otherwise
    """
    if not twilio_validator:
        logger.warning("Twilio validator not configured, skipping validation")
        return True
    
    if Config.DEBUG:
        # Skip validation in development mode
        return True
    
    try:
        url = request_data.url
        params = request_data.form
        signature = request_data.headers.get('X-Twilio-Signature', '')
        
        is_valid = twilio_validator.validate(url, params, signature)
        
        if not is_valid:
            logger.warning(f"Invalid Twilio signature from {request_data.remote_addr}")
        
        return is_valid
    except Exception as e:
        logger.error(f"Error validating Twilio request: {e}")
        return False


def save_order_to_sheet(state, phone_number) -> tuple:
    """
    Save order details to Google Sheet
    
    Args:
        state: User state containing order details
        phone_number: Customer's phone number
    
    Returns:
        Tuple of (success: bool, order_id: str or None)
    """
    if not sheet:
        logger.error("Google Sheets not initialized")
        return False, None
    
    try:
        timestamp = format_timestamp()
        order_id = state.get('order_id', generate_order_id())
        
        # Get pricing details
        pricing = pricing_engine.calculate_order(state['bundles'])
        
        # Prepare row data
        row_data = [
            order_id,
            state["name"],
            state["bundles"],
            pricing['unit_price'],
            pricing['total'],
            pricing['discount_percent'],
            state["address"],
            state["postcode"],
            state.get("delivery_slot", "This weekend"),
            format_phone_number(phone_number),
            "Confirmed",
            timestamp,
            timestamp,  # Updated At
            state.get("notes", "")
        ]
        
        sheet.append_row(row_data)
        
        # Store last order for this user
        order_data = {
            'order_id': order_id,
            'name': state['name'],
            'bundles': state['bundles'],
            'address': state['address'],
            'postcode': state['postcode'],
            'delivery_slot': state.get('delivery_slot', 'This weekend'),
            'total_price': pricing['total'],
            'timestamp': timestamp,
            'status': 'Confirmed'
        }
        state_manager.set_last_order(phone_number, order_data)
        
        logger.info(f"✅ Order {order_id} saved successfully")
        return True, order_id
    
    except Exception as e:
        logger.error(f"Error saving to sheet: {e}")
        return False, None


def reset_user_state(phone_number: str):
    """Remove user state after order completion"""
    state_manager.delete_state(phone_number)


def handle_start_command(phone_number: str) -> str:
    """Handle start/restart commands"""
    # Clear any existing state
    reset_user_state(phone_number)
    
    # Initialize fresh state
    state = {"stage": "ask_name"}
    state_manager.set_state(phone_number, state)
    
    greeting = get_greeting_for_time()
    
    message = (
        f"{greeting}! 👋 Welcome to {Config.BOT_NAME} {Config.BOT_EMOJI}!\n\n"
        f"Please tell me your *name* to start your order."
    )
    
    # Show volume discounts if configured (REMOVED - no discounts)
    # discount_info = pricing_engine.get_discount_info()
    # if discount_info:
    #     message += f"\n\n{discount_info}"
    
    return message


def handle_view_order(phone_number: str) -> str:
    """Handle view order command"""
    order = state_manager.get_last_order(phone_number)
    
    if not order:
        return f"You don't have any recent orders. Type *HI* to place a new order! {Config.BOT_EMOJI}"
    
    return (
        f"📦 *Your Last Order*\n\n"
        f"🆔 Order ID: {order['order_id']}\n"
        f"👤 Name: {order['name']}\n"
        f"🥬 Bundles: {order['bundles']}\n"
        f"💰 Total: £{order.get('total_price', 'N/A')}\n"
        f"📍 Address: {order['address']}, {order['postcode']}\n"
        f"🚚 Delivery: {order.get('delivery_slot', 'This weekend')}\n"
        f"📊 Status: {order.get('status', 'Confirmed')}\n\n"
        f"Reply *CANCEL* to cancel this order\n"
        f"or *HI* to place a new order {Config.BOT_EMOJI}"
    )


def handle_cancel_order(phone_number: str) -> str:
    """Handle order cancellation"""
    order = state_manager.get_last_order(phone_number)
    
    if not order:
        return "No recent order found to cancel."
    
    order_id = order['order_id']
    customer_name = order['name']
    
    # Notify admin
    if Config.ADMIN_NOTIFICATIONS_ENABLED:
        admin_notifier.send_order_cancellation(order_id, customer_name)
    
    # Remove from state
    state_manager.set_last_order(phone_number, {**order, 'status': 'Cancelled'})
    
    return (
        f"❌ Order {order_id} has been cancelled.\n\n"
        f"Note: If you need to cancel within 24 hours of delivery, "
        f"please contact us directly.\n\n"
        f"Type *HI* to place a new order! 🥦"
    )


def handle_help_command() -> str:
    """Show help information"""
    return (
        f"ℹ️ *{Config.BOT_NAME} - Help*\n\n"
        f"*Available Commands:*\n"
        f"• *HI* - Start a new order\n"
        f"• *VIEW* - See your last order\n"
        f"• *CANCEL* - Cancel your order\n"
        f"• *HELP* - Show this help message\n\n"
        f"*Pricing:*\n"
        f"£{Config.PRICE_PER_BUNDLE} per bundle\n"
        f"{pricing_engine.get_discount_info()}\n\n"
        f"Type *HI* to start ordering! {Config.BOT_EMOJI}"
    )


def handle_debug_command(phone_number: str) -> str:
    """Show debug information about current state"""
    state = state_manager.get_state(phone_number)
    
    if not state:
        return "🔧 Debug Info:\nNo active conversation.\n\nType *HI* to start ordering!"
    
    current_stage = state.get("stage", "unknown")
    return (
        f"🔧 *Debug Info*\n\n"
        f"Current stage: {current_stage}\n"
        f"State data: {json.dumps(state, indent=2)}\n\n"
        f"Type *RESET* to start fresh."
    )


# ---- Conversation Stage Handlers ----
def handle_ask_name(state: dict, incoming_msg: str) -> str:
    """Handle name collection stage"""
    is_valid, result = validate_name(incoming_msg)
    
    if not is_valid:
        return f"❌ {result}\nPlease tell me your name:"
    
    state["name"] = result
    state["stage"] = "ask_bundles"
    
    return f"Nice to meet you, {state['name']}! 🧺\n\nHow many *bundles* would you like to order?"


def handle_ask_bundles(state: dict, incoming_msg: str) -> str:
    """Handle bundle count collection stage"""
    is_valid, result = validate_bundle_count(incoming_msg)
    
    if not is_valid:
        return f"❌ {result}\nPlease enter how many bundles you'd like:"
    
    state["bundles"] = result
    state["stage"] = "ask_address"
    
    # Show pricing preview
    pricing_summary = pricing_engine.get_order_summary(result)
    
    return (
        f"Got it ✅\n\n"
        f"{pricing_summary}\n\n"
        f"Please provide your *delivery address*:"
    )


def handle_ask_address(state: dict, incoming_msg: str) -> str:
    """Handle address collection stage"""
    is_valid, result = validate_address(incoming_msg)
    
    if not is_valid:
        return f"❌ {result}\nPlease provide your delivery address:"
    
    state["address"] = result
    state["stage"] = "ask_postcode"
    
    return "Thank you! 📍\n\nNow please provide your *postcode*:"


def handle_ask_postcode(state: dict, incoming_msg: str) -> str:
    """Handle postcode collection stage"""
    is_valid, result = validate_postcode(incoming_msg)
    
    if not is_valid:
        return f"❌ {result}\nPlease provide your postcode:"
    
    state["postcode"] = result
    
    # Get delivery slots
    delivery_slots = Config.get_delivery_slots()
    
    if len(delivery_slots) > 1:
        state["stage"] = "ask_delivery_slot"
        slot_list = create_numbered_list(delivery_slots, "🕒")
        
        return (
            f"Perfect! 🎯\n\n"
            f"*Choose your delivery slot:*\n{slot_list}\n\n"
            f"Reply with the number of your preferred slot."
        )
    else:
        # Skip to confirmation if only one slot
        state["delivery_slot"] = delivery_slots[0] if delivery_slots else "This weekend"
        state["stage"] = "confirm_order"
        return generate_confirmation_message(state)


def handle_ask_delivery_slot(state: dict, incoming_msg: str) -> str:
    """Handle delivery slot selection stage"""
    delivery_slots = Config.get_delivery_slots()
    is_valid, result = validate_delivery_slot_choice(incoming_msg, delivery_slots)
    
    if not is_valid:
        slot_list = create_numbered_list(delivery_slots, "🕒")
        return f"❌ {result}\n\n{slot_list}\n\nPlease choose a number:"
    
    state["delivery_slot"] = result
    state["stage"] = "confirm_order"
    
    return generate_confirmation_message(state)


def generate_confirmation_message(state: dict) -> str:
    """Generate order confirmation message"""
    pricing = pricing_engine.calculate_order(state['bundles'])
    pricing_summary = pricing_engine.get_order_summary(state['bundles'])
    
    message = (
        f"✅ *Please Confirm Your Order*\n\n"
        f"👤 Name: {state['name']}\n"
        f"🥬 Bundles: {state['bundles']}\n"
        f"📍 Address: {state['address']}, {state['postcode']}\n"
        f"🚚 Delivery: {state.get('delivery_slot', 'This weekend')}\n\n"
        f"{pricing_summary}\n\n"
    )
    
    if Config.ENABLE_ORDER_MODIFICATION:
        message += "Reply *YES* to confirm or *MODIFY* to make changes."
    else:
        message += "Reply *YES* to confirm or *CANCEL* to cancel."
    
    return message


def handle_confirm_order(state: dict, incoming_msg: str, phone_number: str) -> str:
    """Handle order confirmation stage"""
    response = parse_yes_no(incoming_msg)
    
    # Check for modification request
    if Config.ENABLE_ORDER_MODIFICATION and incoming_msg.lower() in ["modify", "change", "edit"]:
        state["stage"] = "modify_order"
        return (
            "📝 What would you like to modify?\n\n"
            "Reply:\n"
            "• *1* - Change quantity\n"
            "• *2* - Change address\n"
            "• *3* - Change postcode\n"
            "• *4* - Change delivery slot\n"
            "• *CANCEL* - Cancel modification"
        )
    
    if response is True:
        # Confirm and save order
        order_id = generate_order_id()
        state['order_id'] = order_id
        
        success, saved_order_id = save_order_to_sheet(state, phone_number)
        
        if not success:
            return (
                "⚠️ Sorry, there was an issue saving your order.\n"
                "Please try again later or contact support.\n\n"
                f"Your order details:\n"
                f"👤 {state['name']}\n"
                f"🥬 {state['bundles']} bundles\n"
                f"📍 {state['address']}, {state['postcode']}"
            )
        
        # Send admin notification
        if Config.ADMIN_NOTIFICATIONS_ENABLED:
            order_data = state_manager.get_last_order(phone_number)
            admin_notifier.send_new_order_notification(order_data, phone_number)
        
        # Reset state
        reset_user_state(phone_number)
        
        return (
            f"🎉 *Order Confirmed!*\n\n"
            f"🆔 Order ID: *{saved_order_id}*\n"
            f"👤 Name: {state['name']}\n"
            f"🥬 Bundles: {state['bundles']}\n"
            f"📍 Address: {state['address']}, {state['postcode']}\n"
            f"🚚 Delivery: {state.get('delivery_slot', 'This weekend')}\n\n"
            f"💡 *Commands:*\n"
            f"• Type *VIEW* to see your order\n"
            f"• Type *CANCEL* to cancel\n"
            f"• Type *HI* for a new order\n\n"
            f"Thank you for supporting {Config.BOT_NAME}! 💚"
        )
    
    elif response is False:
        reset_user_state(phone_number)
        return "Order cancelled. Type *HI* to start a new order! 🥦"
    
    else:
        return "Please reply *YES* to confirm or *NO* to cancel."


def handle_modify_order(state: dict, incoming_msg: str) -> str:
    """Handle order modification flow"""
    choice = incoming_msg.strip()
    
    if choice.lower() == "cancel":
        state["stage"] = "confirm_order"
        return generate_confirmation_message(state)
    
    if choice == "1":
        state["stage"] = "ask_bundles"
        return "How many bundles would you like? 🧺"
    elif choice == "2":
        state["stage"] = "ask_address"
        return "What's your delivery address? 📍"
    elif choice == "3":
        state["stage"] = "ask_postcode"
        return "What's your postcode? 📮"
    elif choice == "4":
        state["stage"] = "ask_delivery_slot"
        delivery_slots = Config.get_delivery_slots()
        slot_list = create_numbered_list(delivery_slots, "🕒")
        return f"Choose your delivery slot:\n{slot_list}"
    else:
        return (
            "Please choose:\n"
            "• *1* - Change quantity\n"
            "• *2* - Change address\n"
            "• *3* - Change postcode\n"
            "• *4* - Change delivery slot\n"
            "• *CANCEL* - Keep current order"
        )


# ---- WhatsApp Webhook Endpoint ----
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    """Handle incoming WhatsApp messages"""
    
    # Validate request is from Twilio
    if not validate_twilio_request(request):
        logger.warning("Rejected invalid request")
        return "Forbidden", 403
    
    from_number = request.values.get("From", "")
    incoming_msg = sanitize_text(request.values.get("Body", "").strip())
    
    resp = MessagingResponse()
    msg = resp.message()
    
    # Apply rate limiting
    is_allowed, result = rate_limit(
        max_requests=Config.RATE_LIMIT_MESSAGES,
        window_seconds=Config.RATE_LIMIT_WINDOW_SECONDS
    )(lambda phone: True)(from_number)
    
    if not is_allowed:
        retry_after = result
        msg.body(
            f"⚠️ Too many messages! Please wait {retry_after} seconds before trying again."
        )
        return str(resp)
    
    # Log incoming message
    logger.info(f"Message from {format_phone_number(from_number)}: {incoming_msg[:50]}")
    
    # Handle commands
    msg_lower = incoming_msg.lower()
    
    if msg_lower in ["hi", "hello", "start", "restart", "reset", "new"]:
        msg.body(handle_start_command(from_number))
        return str(resp)
    
    if msg_lower in ["view", "my order", "order status", "status"]:
        msg.body(handle_view_order(from_number))
        return str(resp)
    
    if msg_lower == "cancel":
        # Check if in active conversation or cancelling order
        state = state_manager.get_state(from_number)
        if state:
            reset_user_state(from_number)
            msg.body("Conversation cancelled. Type *HI* to start fresh! 🥦")
        else:
            msg.body(handle_cancel_order(from_number))
        return str(resp)
    
    if msg_lower == "help":
        msg.body(handle_help_command())
        return str(resp)
    
    if msg_lower == "debug" and Config.DEBUG:
        msg.body(handle_debug_command(from_number))
        return str(resp)
    
    # Get or initialize user state
    state = state_manager.get_state(from_number)
    
    if not state:
        # Initialize new conversation
        msg.body(handle_start_command(from_number))
        return str(resp)
    
    # Route to appropriate stage handler
    stage = state.get("stage", "ask_name")
    response_text = ""
    
    try:
        if stage == "ask_name":
            response_text = handle_ask_name(state, incoming_msg)
        
        elif stage == "ask_bundles":
            response_text = handle_ask_bundles(state, incoming_msg)
        
        elif stage == "ask_address":
            response_text = handle_ask_address(state, incoming_msg)
        
        elif stage == "ask_postcode":
            response_text = handle_ask_postcode(state, incoming_msg)
        
        elif stage == "ask_delivery_slot":
            response_text = handle_ask_delivery_slot(state, incoming_msg)
        
        elif stage == "confirm_order":
            response_text = handle_confirm_order(state, incoming_msg, from_number)
        
        elif stage == "modify_order":
            response_text = handle_modify_order(state, incoming_msg)
        
        else:
            response_text = "Something went wrong. Type *HI* to start fresh! 🥦"
            reset_user_state(from_number)
        
        # Save updated state
        state_manager.set_state(from_number, state)
        
        msg.body(response_text)
    
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        msg.body(
            "⚠️ Sorry, something went wrong. Please try again or type *HI* to start fresh."
        )
    
    return str(resp)


# ---- Run Flask App ----
if __name__ == "__main__":
    logger.info(f"Starting {Config.BOT_NAME} Bot...")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
