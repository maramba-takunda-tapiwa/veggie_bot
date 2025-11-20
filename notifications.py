"""
Admin notification system for FoodStream Veggies Bot
Sends SMS/WhatsApp notifications to admin about new orders
"""
import logging
from typing import Dict, Optional
from config import Config

logger = logging.getLogger(__name__)


class AdminNotifier:
    """Send notifications to admin about orders"""
    
    def __init__(self, enabled: bool = False):
        """
        Initialize admin notifier
        
        Args:
            enabled: Whether notifications are enabled
        """
        self.enabled = enabled
        self.admin_phone = Config.ADMIN_PHONE
        self.twilio_client = None
        self.from_number = Config.TWILIO_PHONE_NUMBER
        
        if self.enabled:
            self._initialize_twilio()
    
    def _initialize_twilio(self):
        """Initialize Twilio client for sending notifications"""
        try:
            from twilio.rest import Client
            
            account_sid = Config.TWILIO_ACCOUNT_SID
            auth_token = Config.TWILIO_AUTH_TOKEN
            
            if not account_sid or not auth_token:
                logger.warning("Twilio credentials not configured. Admin notifications disabled.")
                self.enabled = False
                return
            
            self.twilio_client = Client(account_sid, auth_token)
            logger.info("✅ Twilio client initialized for admin notifications")
        
        except ImportError:
            logger.error("Twilio package not installed. Run: pip install twilio")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            self.enabled = False
    
    def send_new_order_notification(self, order: Dict, customer_phone: str) -> bool:
        """
        Send notification about new order to admin
        
        Args:
            order: Order details dict
            customer_phone: Customer's phone number
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Admin notifications disabled, skipping")
            return False
        
        if not self.admin_phone:
            logger.warning("Admin phone not configured")
            return False
        
        try:
            message_body = self._format_order_notification(order, customer_phone)
            
            # Send via SMS or WhatsApp
            message = self.twilio_client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=self.admin_phone
            )
            
            logger.info(f"✅ Admin notification sent: {message.sid}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
            return False
    
    def _format_order_notification(self, order: Dict, customer_phone: str) -> str:
        """
        Format order notification message
        
        Args:
            order: Order details
            customer_phone: Customer's phone number
        
        Returns:
            Formatted notification message
        """
        lines = [
            "🔔 NEW VEGGIE ORDER!",
            "",
            f"Order ID: {order.get('order_id', 'N/A')}",
            f"Customer: {order.get('name', 'N/A')}",
            f"Phone: {customer_phone.replace('whatsapp:', '')}",
            f"Bundles: {order.get('bundles', 'N/A')}",
            f"Total: £{order.get('total_price', 'N/A')}",
            f"Address: {order.get('address', 'N/A')}, {order.get('postcode', 'N/A')}",
            f"Delivery: {order.get('delivery_slot', 'This weekend')}",
            "",
            "Check Google Sheets for full details."
        ]
        
        return "\n".join(lines)
    
    def send_order_cancellation(self, order_id: str, customer_name: str) -> bool:
        """
        Send notification about order cancellation
        
        Args:
            order_id: Cancelled order ID
            customer_name: Customer's name
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled or not self.admin_phone:
            return False
        
        try:
            message_body = (
                f"❌ ORDER CANCELLED\n\n"
                f"Order ID: {order_id}\n"
                f"Customer: {customer_name}\n\n"
                f"Please update Google Sheets."
            )
            
            message = self.twilio_client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=self.admin_phone
            )
            
            logger.info(f"✅ Cancellation notification sent: {message.sid}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send cancellation notification: {e}")
            return False


# Create singleton instance
admin_notifier = AdminNotifier(enabled=Config.ADMIN_NOTIFICATIONS_ENABLED)
