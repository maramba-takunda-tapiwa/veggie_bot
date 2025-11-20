"""
Configuration management for FoodStream Veggies Bot
Handles environment variables, pricing settings, and feature flags
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Config:
    """Centralized configuration management"""
    
    # ---- Environment ----
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = ENVIRONMENT == "development"
    
    # ---- Flask ----
    PORT = int(os.getenv("PORT", 5000))
    HOST = os.getenv("HOST", "0.0.0.0")
    
    # ---- Twilio ----
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    # ---- Google Sheets ----
    GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")
    GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Veggie_Orders")
    
    # ---- Redis ----
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
    STATE_EXPIRATION_HOURS = int(os.getenv("STATE_EXPIRATION_HOURS", 24))
    
    # ---- Admin Settings ----
    ADMIN_PHONE = os.getenv("ADMIN_PHONE", "")
    ADMIN_NOTIFICATIONS_ENABLED = os.getenv("ADMIN_NOTIFICATIONS_ENABLED", "false").lower() == "true"
    
    # ---- Pricing ----
    PRICE_PER_BUNDLE = float(os.getenv("PRICE_PER_BUNDLE", "5.00"))
    CURRENCY_SYMBOL = os.getenv("CURRENCY_SYMBOL", "£")
    DELIVERY_FEE = float(os.getenv("DELIVERY_FEE", "0.00"))
    
    # Volume discounts: "10:10,20:15,50:20" means 10+ bundles = 10% off, 20+ = 15% off, etc.
    VOLUME_DISCOUNTS_RAW = os.getenv("VOLUME_DISCOUNTS", "10:10,20:15")
    
    @classmethod
    def get_volume_discounts(cls) -> dict:
        """
        Parse volume discounts from environment variable
        Returns: {quantity_threshold: discount_percentage}
        Example: {10: 10, 20: 15} means 10+ bundles get 10% off, 20+ get 15% off
        """
        if not cls.VOLUME_DISCOUNTS_RAW:
            return {}
        
        try:
            discounts = {}
            for pair in cls.VOLUME_DISCOUNTS_RAW.split(","):
                qty, discount = pair.strip().split(":")
                discounts[int(qty)] = float(discount)
            return discounts
        except Exception as e:
            logger.warning(f"Failed to parse VOLUME_DISCOUNTS: {e}. Using no discounts.")
            return {}
    
    # ---- Delivery Settings ----
    # Delivery slots: "Saturday 2-4 PM,Saturday 4-6 PM,Sunday 10-12 PM,Sunday 2-4 PM"
    DELIVERY_SLOTS_RAW = os.getenv(
        "DELIVERY_SLOTS",
        "Saturday 2-4 PM,Saturday 4-6 PM,Sunday 10-12 PM,Sunday 2-4 PM"
    )
    
    @classmethod
    def get_delivery_slots(cls) -> list:
        """Parse delivery slots from environment variable"""
        if not cls.DELIVERY_SLOTS_RAW:
            return ["This weekend"]
        return [slot.strip() for slot in cls.DELIVERY_SLOTS_RAW.split(",")]
    
    # ---- Rate Limiting ----
    RATE_LIMIT_MESSAGES = int(os.getenv("RATE_LIMIT_MESSAGES", 10))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", 60))
    
    # ---- Feature Flags ----
    ENABLE_ORDER_MODIFICATION = os.getenv("ENABLE_ORDER_MODIFICATION", "true").lower() == "true"
    ENABLE_ORDER_TRACKING = os.getenv("ENABLE_ORDER_TRACKING", "true").lower() == "true"
    ENABLE_CUSTOMER_HISTORY = os.getenv("ENABLE_CUSTOMER_HISTORY", "true").lower() == "true"
    
    # ---- Branding ----
    BOT_NAME = "FoodStream Veggies"
    BOT_EMOJI = "🥬"
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate required configuration settings
        Returns True if valid, raises ValueError if invalid
        """
        errors = []
        
        # Only validate Twilio if admin notifications are enabled
        if cls.ADMIN_NOTIFICATIONS_ENABLED:
            if not cls.TWILIO_ACCOUNT_SID:
                errors.append("TWILIO_ACCOUNT_SID is required for admin notifications")
            if not cls.TWILIO_AUTH_TOKEN:
                errors.append("TWILIO_AUTH_TOKEN is required for admin notifications")
            if not cls.ADMIN_PHONE:
                errors.append("ADMIN_PHONE is required for admin notifications")
        
        # Google Sheets is always required
        if not cls.GOOGLE_CREDS_JSON and not os.path.exists("veggiebot-key.json"):
            errors.append("GOOGLE_CREDS_JSON environment variable or veggiebot-key.json file required")
        
        # Pricing validation
        if cls.PRICE_PER_BUNDLE <= 0:
            errors.append("PRICE_PER_BUNDLE must be greater than 0")
        
        if errors:
            error_msg = "Configuration validation failed:\n  - " + "\n  - ".join(errors)
            raise ValueError(error_msg)
        
        return True
    
    @classmethod
    def log_config(cls):
        """Log current configuration (excluding sensitive data)"""
        logger.info("=" * 50)
        logger.info(f"FoodStream Veggies Bot Configuration")
        logger.info("=" * 50)
        logger.info(f"Environment: {cls.ENVIRONMENT}")
        logger.info(f"Debug Mode: {cls.DEBUG}")
        logger.info(f"Redis Enabled: {cls.REDIS_ENABLED}")
        logger.info(f"Price per Bundle: {cls.CURRENCY_SYMBOL}{cls.PRICE_PER_BUNDLE}")
        logger.info(f"Delivery Fee: {cls.CURRENCY_SYMBOL}{cls.DELIVERY_FEE}")
        logger.info(f"Volume Discounts: {cls.get_volume_discounts()}")
        logger.info(f"Delivery Slots: {len(cls.get_delivery_slots())} available")
        logger.info(f"Admin Notifications: {'Enabled' if cls.ADMIN_NOTIFICATIONS_ENABLED else 'Disabled'}")
        logger.info(f"Order Modification: {'Enabled' if cls.ENABLE_ORDER_MODIFICATION else 'Disabled'}")
        logger.info(f"Order Tracking: {'Enabled' if cls.ENABLE_ORDER_TRACKING else 'Disabled'}")
        logger.info("=" * 50)
