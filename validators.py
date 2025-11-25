"""
Input validation for Iris Housing Bot
Validates age, country, phone, budget, and other user inputs
"""
import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


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


def validate_age(age_text: str) -> Tuple[bool, any]:
    """
    Validate user age (must be 18+)
    
    Args:
        age_text: User input for age
    
    Returns:
        Tuple of (is_valid: bool, result: int or error_message: str)
    """
    try:
        age = int(age_text)
        
        if age < 18:
            return False, "You must be at least 18 years old to inquire about housing. 🏠"
        
        if age > 120:
            return False, "Please enter a valid age."
        
        return True, age
    
    except ValueError:
        return False, "Please enter a valid age (e.g., 25, 30, etc.)"


def validate_country(country: str) -> Tuple[bool, str]:
    """
    Validate country input
    
    Args:
        country: User input for country
    
    Returns:
        Tuple of (is_valid: bool, result: country or error_message: str)
    """
    country = country.strip()
    
    # Check minimum length
    if len(country) < 2:
        return False, "Please provide a valid country name"
    
    # Check maximum length
    if len(country) > 50:
        return False, "Country name is too long. Please use a shorter format."
    
    # Check if it contains at least some letters
    has_letters = bool(re.search(r'[a-zA-Z]', country))
    
    if not has_letters:
        return False, "Please provide a valid country name"
    
    return True, country


def validate_phone_number(phone: str) -> Tuple[bool, str]:
    """
    Validate phone number format
    
    Args:
        phone: User input for phone number
    
    Returns:
        Tuple of (is_valid: bool, result: phone or error_message: str)
    """
    # Remove common separators and spaces
    phone_cleaned = re.sub(r'[\s\-\(\)]+', '', phone)
    
    # Check if it contains only digits and optional + at start
    if not re.match(r'^\+?\d{7,15}$', phone_cleaned):
        return False, "Please enter a valid phone number (e.g., +36301234567 or 06301234567)"
    
    return True, phone_cleaned


def validate_budget(budget_text: str) -> Tuple[bool, str]:
    """
    Validate budget in HUF
    
    Args:
        budget_text: User input for budget
    
    Returns:
        Tuple of (is_valid: bool, result: budget or error_message: str)
    """
    budget_text = budget_text.strip()
    
    # Remove common currency symbols and text
    budget_cleaned = re.sub(r'[HUF\s,]', '', budget_text, flags=re.IGNORECASE)
    
    try:
        budget_amount = float(budget_cleaned)
        
        if budget_amount <= 0:
            return False, "Please enter a positive budget amount 💰"
        
        # Format nicely with thousand separators
        budget_formatted = f"{int(budget_amount):,} HUF"
        
        return True, budget_formatted
    
    except ValueError:
        return False, "Please enter a valid budget amount (e.g., 150000, 200000)"


def validate_house_id(house_id: str) -> Tuple[bool, str]:
    """
    Validate house ID (optional field)
    
    Args:
        house_id: User input for house ID
    
    Returns:
        Tuple of (is_valid: bool, result: house_id or error_message: str)
    """
    house_id = house_id.strip().upper()
    
    # Check if user wants to skip
    if house_id.lower() in ["skip", "no", "none", "n/a", "na", "don't have", "dont have"]:
        return True, "N/A"
    
    # Validate length
    if len(house_id) < 2:
        return False, "Please provide a valid house ID or type 'skip' if you don't have one"
    
    if len(house_id) > 20:
        return False, "House ID is too long. Please provide a valid ID or type 'skip'"
    
    return True, house_id


def validate_location_preference(location: str) -> Tuple[bool, str]:
    """
    Validate location preference (free text)
    
    Args:
        location: User input for location preferences
    
    Returns:
        Tuple of (is_valid: bool, result: location or error_message: str)
    """
    location = location.strip()
    
    # Check minimum length
    if len(location) < 3:
        return False, "Please describe your location preferences (e.g., 'Near tram', 'Close to bus stop', 'City center')"
    
    # Check maximum length
    if len(location) > 200:
        return False, "Location preference is too long. Please be more concise."
    
    return True, location
