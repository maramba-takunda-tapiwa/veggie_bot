"""
Input validation for FoodStream Veggies Bot
Validates bundles, postcodes, addresses, and other user inputs
"""
import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def validate_bundle_count(text: str) -> Tuple[bool, any]:
    """
    Validate that bundle count is a positive number within acceptable range
    
    Args:
        text: User input for bundle count
    
    Returns:
        Tuple of (is_valid: bool, result: int or error_message: str)
        If valid: (True, bundle_count)
        If invalid: (False, error_message)
    """
    try:
        count = int(text)
        
        if count <= 0:
            return False, "Please enter a positive number of bundles! 😊"
        
        if count > 100:
            return False, "That's a lot of veggies! 😅 Please order 100 or fewer bundles, or contact us directly for bulk orders."
        
        return True, count
    
    except ValueError:
        return False, "Please enter a valid number (e.g., 1, 2, 3, etc.)"


def validate_postcode(postcode: str) -> Tuple[bool, str]:
    """
    Validate UK postcode format
    
    Args:
        postcode: User input for postcode
    
    Returns:
        Tuple of (is_valid: bool, result: formatted_postcode or error_message: str)
    """
    # Remove whitespace and convert to uppercase
    postcode = postcode.strip().upper()
    
    # Basic UK postcode regex pattern
    # Matches formats like: SW1A 1AA, M1 1AE, CR2 6XH, etc.
    uk_postcode_pattern = re.compile(
        r'^[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}$'
    )
    
    if not uk_postcode_pattern.match(postcode):
        return False, "Please enter a valid UK postcode (e.g., SW1A 1AA, M1 1AE)"
    
    # Format with space if missing
    if ' ' not in postcode:
        # Insert space before last 3 characters
        postcode = postcode[:-3] + ' ' + postcode[-3:]
    
    return True, postcode


def validate_address(address: str) -> Tuple[bool, str]:
    """
    Validate delivery address
    
    Args:
        address: User input for address
    
    Returns:
        Tuple of (is_valid: bool, result: address or error_message: str)
    """
    address = address.strip()
    
    # Check minimum length
    if len(address) < 5:
        return False, "Please provide a complete address (street, house number, etc.)"
    
    # Check maximum length
    if len(address) > 200:
        return False, "Address is too long. Please use a shorter format."
    
    # Check if it contains at least some letters and numbers
    has_letters = bool(re.search(r'[a-zA-Z]', address))
    
    if not has_letters:
        return False, "Please provide a valid address with street name"
    
    return True, address


def validate_name(name: str) -> Tuple[bool, str]:
    """
    Validate customer name
    
    Args:
        name: User input for name
    
    Returns:
        Tuple of (is_valid: bool, result: name or error_message: str)
    """
    name = name.strip()
    
    # Check minimum length
    if len(name) < 2:
        return False, "Please provide your full name"
    
    # Check maximum length
    if len(name) > 50:
        return False, "Name is too long. Please use a shorter format."
    
    # Check if it contains at least some letters
    has_letters = bool(re.search(r'[a-zA-Z]', name))
    
    if not has_letters:
        return False, "Please provide a valid name"
    
    return True, name


def validate_delivery_slot_choice(choice: str, available_slots: list) -> Tuple[bool, any]:
    """
    Validate delivery slot selection
    
    Args:
        choice: User input (should be a number)
        available_slots: List of available delivery slots
    
    Returns:
        Tuple of (is_valid: bool, result: selected_slot or error_message: str)
    """
    try:
        index = int(choice) - 1  # Convert to 0-indexed
        
        if index < 0 or index >= len(available_slots):
            return False, f"Please choose a number between 1 and {len(available_slots)}"
        
        return True, available_slots[index]
    
    except ValueError:
        return False, "Please enter the number of your preferred delivery slot"


def validate_order_id(order_id: str) -> Tuple[bool, str]:
    """
    Validate order ID format
    
    Args:
        order_id: User input for order ID
    
    Returns:
        Tuple of (is_valid: bool, result: order_id or error_message: str)
    """
    order_id = order_id.strip().upper()
    
    # Order IDs are 6-character hexadecimal
    if len(order_id) != 6:
        return False, "Order ID should be 6 characters"
    
    if not re.match(r'^[A-F0-9]{6}$', order_id):
        return False, "Invalid order ID format. Order IDs contain only letters A-F and numbers 0-9"
    
    return True, order_id
