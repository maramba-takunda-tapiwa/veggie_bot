"""
Configuration management for Iris Housing Bot
Handles environment variables and feature flags
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
    GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Housing_Inquiries")
    
    # ---- Redis ----
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
    STATE_EXPIRATION_HOURS = int(os.getenv("STATE_EXPIRATION_HOURS", 24))
    
    # ---- Admin Settings ----
    ADMIN_PHONE = os.getenv("ADMIN_PHONE", "")
    ADMIN_NOTIFICATIONS_ENABLED = os.getenv("ADMIN_NOTIFICATIONS_ENABLED", "false").lower() == "true"
    
    # ---- Currency ----
    CURRENCY_SYMBOL = os.getenv("CURRENCY_SYMBOL", "HUF")
    CURRENCY_NAME = "Hungarian Forint"
    

    
    # ---- Rate Limiting ----
    RATE_LIMIT_MESSAGES = int(os.getenv("RATE_LIMIT_MESSAGES", 10))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", 60))
    
    # ---- Feature Flags ----
    ENABLE_INQUIRY_MODIFICATION = os.getenv("ENABLE_INQUIRY_MODIFICATION", "true").lower() == "true"
    ENABLE_INQUIRY_TRACKING = os.getenv("ENABLE_INQUIRY_TRACKING", "true").lower() == "true"
    ENABLE_CUSTOMER_HISTORY = os.getenv("ENABLE_CUSTOMER_HISTORY", "true").lower() == "true"
    
    # ---- Branding ----
    BOT_NAME = "Iris Housing"
    BOT_EMOJI = "🏠"
    
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
        

        
        if errors:
            error_msg = "Configuration validation failed:\n  - " + "\n  - ".join(errors)
            raise ValueError(error_msg)
        
        return True
    
    @classmethod
    def log_config(cls):
        """Log current configuration (excluding sensitive data)"""
        logger.info("=" * 50)
        logger.info(f"Iris Housing Bot Configuration")
        logger.info("=" * 50)
        logger.info(f"Environment: {cls.ENVIRONMENT}")
        logger.info(f"Debug Mode: {cls.DEBUG}")
        logger.info(f"Redis Enabled: {cls.REDIS_ENABLED}")
        logger.info(f"Currency: {cls.CURRENCY_SYMBOL}")
        logger.info(f"Admin Notifications: {'Enabled' if cls.ADMIN_NOTIFICATIONS_ENABLED else 'Disabled'}")
        logger.info(f"Inquiry Modification: {'Enabled' if cls.ENABLE_INQUIRY_MODIFICATION else 'Disabled'}")
        logger.info(f"Inquiry Tracking: {'Enabled' if cls.ENABLE_INQUIRY_TRACKING else 'Disabled'}")
        logger.info("=" * 50)
