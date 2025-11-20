"""
Unit tests for input validators
Tests validation for bundles, postcodes, addresses, names, etc.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from validators import (
    validate_bundle_count, validate_postcode, validate_address,
    validate_name, validate_delivery_slot_choice, validate_order_id
)


class TestValidators(unittest.TestCase):
    """Test cases for input validators"""
    
    # ---- Bundle Count Tests ----
    def test_valid_bundle_count(self):
        """Test valid bundle counts"""
        is_valid, result = validate_bundle_count("5")
        self.assertTrue(is_valid)
        self.assertEqual(result, 5)
        
        is_valid, result = validate_bundle_count("1")
        self.assertTrue(is_valid)
        self.assertEqual(result, 1)
        
        is_valid, result = validate_bundle_count("100")
        self.assertTrue(is_valid)
        self.assertEqual(result, 100)
    
    def test_invalid_bundle_zero(self):
        """Test that zero bundles is invalid"""
        is_valid, message = validate_bundle_count("0")
        self.assertFalse(is_valid)
        self.assertIn("positive number", message)
    
    def test_invalid_bundle_negative(self):
        """Test that negative bundles is invalid"""
        is_valid, message = validate_bundle_count("-5")
        self.assertFalse(is_valid)
        self.assertIn("positive number", message)
    
    def test_invalid_bundle_too_large(self):
        """Test that excessively large orders are rejected"""
        is_valid, message = validate_bundle_count("101")
        self.assertFalse(is_valid)
        self.assertIn("100 or fewer", message)
    
    def test_invalid_bundle_not_number(self):
        """Test that non-numeric input is rejected"""
        is_valid, message = validate_bundle_count("five")
        self.assertFalse(is_valid)
        self.assertIn("valid number", message)
    
    # ---- Postcode Tests ----
    def test_valid_postcode_with_space(self):
        """Test valid UK postcode with space"""
        is_valid, result = validate_postcode("SW1A 1AA")
        self.assertTrue(is_valid)
        self.assertEqual(result, "SW1A 1AA")
    
    def test_valid_postcode_without_space(self):
        """Test valid UK postcode without space (should add space)"""
        is_valid, result = validate_postcode("M11AE")
        self.assertTrue(is_valid)
        self.assertEqual(result, "M1 1AE")
    
    def test_valid_postcode_variations(self):
        """Test various valid UK postcode formats"""
        valid_codes = ["CR2 6XH", "DN55 1PT", "W1A 1HQ", "EC1A 1BB"]
        
        for code in valid_codes:
            is_valid, result = validate_postcode(code)
            self.assertTrue(is_valid, f"Failed for {code}")
    
    def test_invalid_postcode(self):
        """Test invalid postcode formats"""
        is_valid, message = validate_postcode("INVALID")
        self.assertFalse(is_valid)
        self.assertIn("valid UK postcode", message)
        
        is_valid, message = validate_postcode("12345")
        self.assertFalse(is_valid)
    
    # ---- Address Tests ----
    def test_valid_address(self):
        """Test valid addresses"""
        is_valid, result = validate_address("123 Main Street")
        self.assertTrue(is_valid)
        self.assertEqual(result, "123 Main Street")
        
        is_valid, result = validate_address("Flat 4, Park View Apartments")
        self.assertTrue(is_valid)
    
    def test_invalid_address_too_short(self):
        """Test that very short addresses are rejected"""
        is_valid, message = validate_address("123")
        self.assertFalse(is_valid)
        self.assertIn("complete address", message)
    
    def test_invalid_address_too_long(self):
        """Test that excessively long addresses are rejected"""
        long_address = "A" * 201
        is_valid, message = validate_address(long_address)
        self.assertFalse(is_valid)
        self.assertIn("too long", message)
    
    def test_invalid_address_no_letters(self):
        """Test that address must contain letters"""
        is_valid, message = validate_address("123456789")
        self.assertFalse(is_valid)
        self.assertIn("street name", message)
    
    # ---- Name Tests ----
    def test_valid_name(self):
        """Test valid names"""
        is_valid, result = validate_name("John Smith")
        self.assertTrue(is_valid)
        self.assertEqual(result, "John Smith")
        
        is_valid, result = validate_name("Mary-Jane O'Connor")
        self.assertTrue(is_valid)
    
    def test_invalid_name_too_short(self):
        """Test that single character names are rejected"""
        is_valid, message = validate_name("A")
        self.assertFalse(is_valid)
        self.assertIn("full name", message)
    
    def test_invalid_name_too_long(self):
        """Test that excessively long names are rejected"""
        long_name = "A" * 51
        is_valid, message = validate_name(long_name)
        self.assertFalse(is_valid)
        self.assertIn("too long", message)
    
    def test_invalid_name_no_letters(self):
        """Test that name must contain letters"""
        is_valid, message = validate_name("123")
        self.assertFalse(is_valid)
        self.assertIn("valid name", message)
    
    # ---- Delivery Slot Tests ----
    def test_valid_delivery_slot_choice(self):
        """Test valid delivery slot selections"""
        slots = ["Saturday 2-4 PM", "Sunday 10-12 PM", "Monday 3-5 PM"]
        
        is_valid, result = validate_delivery_slot_choice("1", slots)
        self.assertTrue(is_valid)
        self.assertEqual(result, "Saturday 2-4 PM")
        
        is_valid, result = validate_delivery_slot_choice("3", slots)
        self.assertTrue(is_valid)
        self.assertEqual(result, "Monday 3-5 PM")
    
    def test_invalid_delivery_slot_out_of_range(self):
        """Test invalid slot number"""
        slots = ["Saturday 2-4 PM", "Sunday 10-12 PM"]
        
        is_valid, message = validate_delivery_slot_choice("5", slots)
        self.assertFalse(is_valid)
        self.assertIn("between 1 and 2", message)
    
    def test_invalid_delivery_slot_not_number(self):
        """Test non-numeric slot choice"""
        slots = ["Saturday 2-4 PM", "Sunday 10-12 PM"]
        
        is_valid, message = validate_delivery_slot_choice("first", slots)
        self.assertFalse(is_valid)
        self.assertIn("number", message)
    
    # ---- Order ID Tests ----
    def test_valid_order_id(self):
        """Test valid order IDs"""
        is_valid, result = validate_order_id("A1B2C3")
        self.assertTrue(is_valid)
        self.assertEqual(result, "A1B2C3")
        
        is_valid, result = validate_order_id("FFFFFF")
        self.assertTrue(is_valid)
    
    def test_invalid_order_id_wrong_length(self):
        """Test order ID with wrong length"""
        is_valid, message = validate_order_id("ABC")
        self.assertFalse(is_valid)
        self.assertIn("6 characters", message)
    
    def test_invalid_order_id_wrong_characters(self):
        """Test order ID with invalid characters"""
        is_valid, message = validate_order_id("ABCXYZ")
        self.assertFalse(is_valid)
        self.assertIn("Invalid order ID", message)


if __name__ == '__main__':
    unittest.main()
