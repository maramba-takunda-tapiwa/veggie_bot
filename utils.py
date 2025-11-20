"""
Utility functions for FoodStream Veggies Bot
Includes order ID generation, text sanitization, rate limiting, and helpers
"""
import secrets
import re
import time
import logging
from functools import wraps
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Rate limiting storage: {phone_number: [timestamp1, timestamp2, ...]}
rate_limit_store: Dict[str, list] = {}


def generate_order_id() -> str:
    """
    Generate a unique 6-character order ID
    Returns: Uppercase hexadecimal string (e.g., '3FA8B2')
    """
    return secrets.token_hex(3).upper()


def sanitize_text(text: str, max_length: int = 500) -> str:
    """
    Sanitize user input to prevent injection attacks and excessive length
    
    Args:
        text: Raw user input
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text with dangerous characters removed
    """
    if not text:
        return ""
    
    # Remove any null bytes
    text = text.replace('\0', '')
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    return text


def format_phone_number(phone: str) -> str:
    """
    Format phone number for display
    
    Args:
        phone: Phone number (may include 'whatsapp:' prefix)
    
    Returns:
        Cleaned phone number without prefix
    """
    return phone.replace("whatsapp:", "").strip()


def format_currency(amount: float, currency_symbol: str = "£") -> str:
    """
    Format amount as currency
    
    Args:
        amount: Numeric amount
        currency_symbol: Currency symbol to use
    
    Returns:
        Formatted currency string (e.g., '£25.00')
    """
    return f"{currency_symbol}{amount:.2f}"


def format_timestamp(dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime as string
    
    Args:
        dt: Datetime object (defaults to now)
        format_str: strftime format string
    
    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)


def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """
    Decorator to rate limit function calls per user
    
    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
    
    Usage:
        @rate_limit(max_requests=10, window_seconds=60)
        def my_function(phone_number, ...):
            pass
    
    Returns:
        Decorator function that returns (is_allowed: bool, retry_after: int)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(phone_number: str, *args, **kwargs):
            current_time = time.time()
            
            # Initialize or get user's request history
            if phone_number not in rate_limit_store:
                rate_limit_store[phone_number] = []
            
            # Remove timestamps outside the current window
            rate_limit_store[phone_number] = [
                ts for ts in rate_limit_store[phone_number]
                if current_time - ts < window_seconds
            ]
            
            # Check if limit exceeded
            if len(rate_limit_store[phone_number]) >= max_requests:
                oldest_timestamp = rate_limit_store[phone_number][0]
                retry_after = int(window_seconds - (current_time - oldest_timestamp))
                logger.warning(f"Rate limit exceeded for {phone_number}. Retry after {retry_after}s")
                return False, retry_after
            
            # Add current request
            rate_limit_store[phone_number].append(current_time)
            
            # Call the original function
            return True, func(phone_number, *args, **kwargs)
        
        return wrapper
    return decorator


def parse_yes_no(text: str) -> Optional[bool]:
    """
    Parse user input as yes/no response
    
    Args:
        text: User input
    
    Returns:
        True for yes, False for no, None for unclear
    """
    text = text.lower().strip()
    
    yes_words = {'yes', 'y', 'yeah', 'yep', 'sure', 'ok', 'okay', 'confirm', 'correct'}
    no_words = {'no', 'n', 'nope', 'nah', 'cancel', 'wrong'}
    
    if text in yes_words:
        return True
    elif text in no_words:
        return False
    else:
        return None


def create_numbered_list(items: list, emoji: str = "•") -> str:
    """
    Create a numbered list with emojis
    
    Args:
        items: List of strings
        emoji: Emoji to use as bullet point
    
    Returns:
        Formatted string with numbered items
    """
    if not items:
        return ""
    
    return "\n".join([f"{emoji} {i+1}. {item}" for i, item in enumerate(items)])


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def get_greeting_for_time() -> str:
    """
    Get appropriate greeting based on time of day
    
    Returns:
        Greeting string (e.g., 'Good morning', 'Good afternoon')
    """
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 17:
        return "Good afternoon"
    elif 17 <= hour < 22:
        return "Good evening"
    else:
        return "Hello"
