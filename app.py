"""
Iris Housing Bot - WhatsApp Housing Inquiry System
A production-ready bot for managing housing inquiries via WhatsApp

Features:
- Persistent state management with Redis
- Inquiry modification and tracking
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
    validate_name, validate_age, validate_country,
    validate_phone_number, validate_budget, validate_house_id,
    validate_location_preference
)
from notifications import admin_notifier
from utils import (
    generate_order_id, sanitize_text, format_phone_number,
    format_timestamp, rate_limit, parse_yes_no,
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
            "inquiry_modification": Config.ENABLE_INQUIRY_MODIFICATION,
            "inquiry_tracking": Config.ENABLE_INQUIRY_TRACKING
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


def save_inquiry_to_sheet(state, phone_number) -> tuple:
    """
    Save housing inquiry details to Google Sheet
    
    Args:
        state: User state containing inquiry details
        phone_number: Customer's phone number
    
    Returns:
        Tuple of (success: bool, inquiry_id: str or None)
    """
    if not sheet:
        logger.error("Google Sheets not initialized")
        return False, None
    
    try:
        timestamp = format_timestamp()
        inquiry_id = state.get('inquiry_id', generate_order_id())
        
        # Prepare row data for housing inquiry
        row_data = [
            inquiry_id,
            state["name"],
            state["age"],
            state["country"],
            state["phone"],
            state["budget"],
            state.get("house_id", "N/A"),
            state["location"],
            "Interested",  # Status set only on confirmation
            timestamp,
            timestamp,  # Updated At
        ]
        
        sheet.append_row(row_data)
        
        # Store last inquiry for this user
        inquiry_data = {
            'inquiry_id': inquiry_id,
            'name': state['name'],
            'age': state['age'],
            'country': state['country'],
            'phone': state['phone'],
            'budget': state['budget'],
            'house_id': state.get('house_id', 'N/A'),
            'location': state['location'],
            'status': 'Interested',
            'timestamp': timestamp
        }
        state_manager.set_last_order(phone_number, inquiry_data)
        
        logger.info(f"✅ Inquiry {inquiry_id} saved successfully")
        return True, inquiry_id
    
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
        f"We're here to help you find your perfect home.\n\n"
        f"Please tell me your *name* to start your inquiry."
    )
    
    return message


def handle_view_order(phone_number: str) -> str:
    """Handle view inquiry command"""
    inquiry = state_manager.get_last_order(phone_number)
    
    if not inquiry:
        return f"You don't have any recent inquiries. Type *HI* to start a new inquiry! {Config.BOT_EMOJI}"
    
    return (
        f"📋 *Your Last Inquiry*\n\n"
        f"🆔 Inquiry ID: {inquiry['inquiry_id']}\n"
        f"👤 Name: {inquiry['name']}\n"
        f"🎂 Age: {inquiry['age']}\n"
        f"🌍 Country: {inquiry['country']}\n"
        f"📱 Phone: {inquiry['phone']}\n"
        f"💰 Budget: {inquiry['budget']}\n"
        f"🏠 House ID: {inquiry.get('house_id', 'N/A')}\n"
        f"📍 Location: {inquiry['location']}\n"
        f"📊 Status: {inquiry.get('status', 'Interested')}\n\n"
        f"Reply *CANCEL* to cancel this inquiry\n"
        f"or *HI* to submit a new inquiry {Config.BOT_EMOJI}"
    )


def handle_cancel_order(phone_number: str) -> str:
    """Handle inquiry cancellation"""
    inquiry = state_manager.get_last_order(phone_number)
    
    if not inquiry:
        return "No recent inquiry found to cancel."
    
    inquiry_id = inquiry['inquiry_id']
    customer_name = inquiry['name']
    
    # Notify admin
    if Config.ADMIN_NOTIFICATIONS_ENABLED:
        admin_notifier.send_order_cancellation(inquiry_id, customer_name)
    
    # Remove from state
    state_manager.set_last_order(phone_number, {**inquiry, 'status': 'Cancelled'})
    
    return (
        f"❌ Inquiry {inquiry_id} has been cancelled.\n\n"
        f"Type *HI* to submit a new inquiry! 🏠"
    )


def handle_help_command() -> str:
    """Show help information"""
    return (
        f"ℹ️ *{Config.BOT_NAME} - Help*\n\n"
        f"*Available Commands:*\n"
        f"• *HI* - Start a new housing inquiry\n"
        f"• *VIEW* - See your last inquiry\n"
        f"• *CANCEL* - Cancel your inquiry\n"
        f"• *HELP* - Show this help message\n\n"
        f"Type *HI* to start your housing inquiry! {Config.BOT_EMOJI}"
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
    state["stage"] = "ask_age"
    
    return f"Nice to meet you, {state['name']}! 🏠\n\nHow old are you? (Please enter your age)"


def handle_ask_age(state: dict, incoming_msg: str) -> str:
    """Handle age collection stage"""
    is_valid, result = validate_age(incoming_msg)
    
    if not is_valid:
        return f"❌ {result}\nPlease enter your age:"
    
    state["age"] = result
    state["stage"] = "ask_country"
    
    return f"Got it! ✅\n\nWhich *country* are you from?"


def handle_ask_country(state: dict, incoming_msg: str) -> str:
    """Handle country collection stage"""
    is_valid, result = validate_country(incoming_msg)
    
    if not is_valid:
        return f"❌ {result}\nPlease provide your country:"
    
    state["country"] = result
    state["stage"] = "ask_phone"
    
    return f"Thank you! 🌍\n\nWhat is your *phone number*?\n(e.g., +36301234567 or 06301234567)"


def handle_ask_phone(state: dict, incoming_msg: str) -> str:
    """Handle phone number collection stage"""
    is_valid, result = validate_phone_number(incoming_msg)
    
    if not is_valid:
        return f"❌ {result}\nPlease provide your phone number:"
    
    state["phone"] = result
    state["stage"] = "ask_budget"
    
    return f"Perfect! 📱\n\nWhat is your *budget* in HUF?\n(e.g., 150000, 200000)"


def handle_ask_budget(state: dict, incoming_msg: str) -> str:
    """Handle budget collection stage"""
    is_valid, result = validate_budget(incoming_msg)
    
    if not is_valid:
        return f"❌ {result}\nPlease enter your budget:"
    
    state["budget"] = result
    state["stage"] = "ask_house_id"
    
    return (
        f"Excellent! 💰\n\n"
        f"Do you have a specific *house ID* you're interested in?\n"
        f"If yes, please provide it. If not, type *skip*."
    )


def handle_ask_house_id(state: dict, incoming_msg: str) -> str:
    """Handle house ID collection stage (optional)"""
    is_valid, result = validate_house_id(incoming_msg)
    
    if not is_valid:
        return f"❌ {result}\nPlease provide a house ID or type 'skip':"
    
    state["house_id"] = result
    state["stage"] = "ask_location"
    
    house_msg = f"House ID: {result}" if result != "N/A" else "No specific house ID"
    
    return (
        f"Noted! 🏠 {house_msg}\n\n"
        f"What are your *location preferences*?\n"
        f"(e.g., 'Near tram', 'Close to bus stop', 'City center', etc.)"
    )


def handle_ask_location(state: dict, incoming_msg: str) -> str:
    """Handle location preference collection stage"""
    is_valid, result = validate_location_preference(incoming_msg)
    
    if not is_valid:
        return f"❌ {result}\nPlease describe your location preferences:"
    
    state["location"] = result
    state["stage"] = "confirm_inquiry"
    
    return generate_confirmation_message(state)


def generate_confirmation_message(state: dict) -> str:
    """Generate inquiry confirmation message"""
    message = (
        f"✅ *Please Confirm Your Inquiry*\n\n"
        f"👤 Name: {state['name']}\n"
        f"🎂 Age: {state['age']}\n"
        f"🌍 Country: {state['country']}\n"
        f"📱 Phone: {state['phone']}\n"
        f"💰 Budget: {state['budget']}\n"
        f"🏠 House ID: {state.get('house_id', 'N/A')}\n"
        f"📍 Location Preference: {state['location']}\n\n"
    )
    
    if Config.ENABLE_INQUIRY_MODIFICATION:
        message += "Reply *YES* to confirm or *MODIFY* to make changes."
    else:
        message += "Reply *YES* to confirm or *CANCEL* to cancel."
    
    return message


def handle_confirm_inquiry(state: dict, incoming_msg: str, phone_number: str) -> str:
    """Handle inquiry confirmation stage"""
    response = parse_yes_no(incoming_msg)
    
    # Check for modification request
    if Config.ENABLE_INQUIRY_MODIFICATION and incoming_msg.lower() in ["modify", "change", "edit"]:
        state["stage"] = "modify_inquiry"
        return (
            "📝 What would you like to modify?\n\n"
            "Reply:\n"
            "• *1* - Change age\n"
            "• *2* - Change country\n"
            "• *3* - Change phone number\n"
            "• *4* - Change budget\n"
            "• *5* - Change house ID\n"
            "• *6* - Change location preference\n"
            "• *CANCEL* - Cancel modification"
        )
    
    if response is True:
        # Confirm and save inquiry
        inquiry_id = generate_order_id()
        state['inquiry_id'] = inquiry_id
        
        success, saved_inquiry_id = save_inquiry_to_sheet(state, phone_number)
        
        if not success:
            return (
                "⚠️ Sorry, there was an issue saving your inquiry.\n"
                "Please try again later or contact support.\n\n"
                f"Your inquiry details:\n"
                f"👤 {state['name']}\n"
                f"💰 {state['budget']}\n"
                f"📍 {state['location']}"
            )
        
        # Send admin notification
        if Config.ADMIN_NOTIFICATIONS_ENABLED:
            inquiry_data = state_manager.get_last_order(phone_number)
            admin_notifier.send_new_order_notification(inquiry_data, phone_number)
        
        # Reset state
        reset_user_state(phone_number)
        
        return (
            f"🎉 *Inquiry Submitted!*\n\n"
            f"🆔 Inquiry ID: *{saved_inquiry_id}*\n"
            f"👤 Name: {state['name']}\n"
            f"💰 Budget: {state['budget']}\n"
            f"📍 Location: {state['location']}\n\n"
            f"We'll review your inquiry and get back to you soon!\n\n"
            f"💡 *Commands:*\n"
            f"• Type *VIEW* to see your inquiry\n"
            f"• Type *CANCEL* to cancel\n"
            f"• Type *HI* for a new inquiry\n\n"
            f"Thank you for choosing {Config.BOT_NAME}! 💚"
        )
    
    elif response is False:
        reset_user_state(phone_number)
        return "Inquiry cancelled. Type *HI* to start a new inquiry! 🏠"
    
    else:
        return "Please reply *YES* to confirm or *NO* to cancel."


def handle_modify_inquiry(state: dict, incoming_msg: str) -> str:
    """Handle inquiry modification flow"""
    choice = incoming_msg.strip()
    
    if choice.lower() == "cancel":
        state["stage"] = "confirm_inquiry"
        return generate_confirmation_message(state)
    
    if choice == "1":
        state["stage"] = "ask_age"
        return "What is your age? 🎂"
    elif choice == "2":
        state["stage"] = "ask_country"
        return "Which country are you from? 🌍"
    elif choice == "3":
        state["stage"] = "ask_phone"
        return "What is your phone number? 📱"
    elif choice == "4":
        state["stage"] = "ask_budget"
        return "What is your budget? 💰"
    elif choice == "5":
        state["stage"] = "ask_house_id"
        return "What is the house ID? (or type 'skip') 🏠"
    elif choice == "6":
        state["stage"] = "ask_location"
        return "What are your location preferences? 📍"
    else:
        return (
            "Please choose:\n"
            "• *1* - Change age\n"
            "• *2* - Change country\n"
            "• *3* - Change phone number\n"
            "• *4* - Change budget\n"
            "• *5* - Change house ID\n"
            "• *6* - Change location preference\n"
            "• *CANCEL* - Keep current inquiry"
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
        # Check if in active conversation or cancelling inquiry
        state = state_manager.get_state(from_number)
        if state:
            reset_user_state(from_number)
            msg.body("Conversation cancelled. Type *HI* to start fresh! 🏠")
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
        
        elif stage == "ask_age":
            response_text = handle_ask_age(state, incoming_msg)
        
        elif stage == "ask_country":
            response_text = handle_ask_country(state, incoming_msg)
        
        elif stage == "ask_phone":
            response_text = handle_ask_phone(state, incoming_msg)
        
        elif stage == "ask_budget":
            response_text = handle_ask_budget(state, incoming_msg)
        
        elif stage == "ask_house_id":
            response_text = handle_ask_house_id(state, incoming_msg)
        
        elif stage == "ask_location":
            response_text = handle_ask_location(state, incoming_msg)
        
        elif stage == "confirm_inquiry":
            response_text = handle_confirm_inquiry(state, incoming_msg, from_number)
        
        elif stage == "modify_inquiry":
            response_text = handle_modify_inquiry(state, incoming_msg)
        
        else:
            response_text = "Something went wrong. Type *HI* to start fresh! 🏠"
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
