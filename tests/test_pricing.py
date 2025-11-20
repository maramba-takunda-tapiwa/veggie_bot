"""
Unit tests for pricing engine
Tests basic pricing, volume discounts, and edge cases
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from pricing import PricingEngine


class TestPricingEngine(unittest.TestCase):
    """Test cases for PricingEngine"""
    
    def setUp(self):
        """Set up test pricing engine with known values"""
        self.engine = PricingEngine()
        # Override with test values
        self.engine.price_per_bundle = 5.00
        self.engine.delivery_fee = 0.00
        self.engine.volume_discounts = {10: 10, 20: 15}
    
    def test_basic_pricing_no_discount(self):
        """Test basic pricing without discounts"""
        result = self.engine.calculate_order(5)
        
        self.assertEqual(result['bundles'], 5)
        self.assertEqual(result['unit_price'], 5.00)
        self.assertEqual(result['subtotal'], 25.00)
        self.assertEqual(result['discount_percent'], 0.0)
        self.assertEqual(result['discount_amount'], 0.0)
        self.assertEqual(result['total'], 25.00)
    
    def test_volume_discount_10_bundles(self):
        """Test 10% discount for 10 bundles"""
        result = self.engine.calculate_order(10)
        
        self.assertEqual(result['bundles'], 10)
        self.assertEqual(result['subtotal'], 50.00)
        self.assertEqual(result['discount_percent'], 10.0)
        self.assertEqual(result['discount_amount'], 5.00)
        self.assertEqual(result['total'], 45.00)
    
    def test_volume_discount_20_bundles(self):
        """Test 15% discount for 20 bundles"""
        result = self.engine.calculate_order(20)
        
        self.assertEqual(result['bundles'], 20)
        self.assertEqual(result['subtotal'], 100.00)
        self.assertEqual(result['discount_percent'], 15.0)
        self.assertEqual(result['discount_amount'], 15.00)
        self.assertEqual(result['total'], 85.00)
    
    def test_volume_discount_15_bundles(self):
        """Test that 15 bundles gets 10% discount (not 15%)"""
        result = self.engine.calculate_order(15)
        
        self.assertEqual(result['bundles'], 15)
        self.assertEqual(result['subtotal'], 75.00)
        self.assertEqual(result['discount_percent'], 10.0)  # Gets 10% tier
        self.assertEqual(result['discount_amount'], 7.50)
        self.assertEqual(result['total'], 67.50)
    
    def test_with_delivery_fee(self):
        """Test pricing with delivery fee"""
        self.engine.delivery_fee = 3.50
        result = self.engine.calculate_order(5)
        
        self.assertEqual(result['subtotal'], 25.00)
        self.assertEqual(result['delivery_fee'], 3.50)
        self.assertEqual(result['total'], 28.50)
    
    def test_edge_case_one_bundle(self):
        """Test with minimum order of 1 bundle"""
        result = self.engine.calculate_order(1)
        
        self.assertEqual(result['bundles'], 1)
        self.assertEqual(result['total'], 5.00)
    
    def test_edge_case_large_order(self):
        """Test with large order of 100 bundles"""
        result = self.engine.calculate_order(100)
        
        self.assertEqual(result['bundles'], 100)
        self.assertEqual(result['subtotal'], 500.00)
        self.assertEqual(result['discount_percent'], 15.0)  # Gets highest tier
        self.assertEqual(result['discount_amount'], 75.00)
        self.assertEqual(result['total'], 425.00)
    
    def test_format_price(self):
        """Test price formatting"""
        formatted = self.engine.format_price(25.50)
        self.assertEqual(formatted, "£25.50")
    
    def test_get_order_summary(self):
        """Test order summary generation"""
        summary = self.engine.get_order_summary(10)
        
        self.assertIn("10 bundles", summary)
        self.assertIn("£50.00", summary)  # Subtotal
        self.assertIn("£45.00", summary)  # Total after discount
        self.assertIn("10% off", summary)  # Discount info
    
    def test_no_discounts_configured(self):
        """Test with no volume discounts"""
        self.engine.volume_discounts = {}
        result = self.engine.calculate_order(50)
        
        self.assertEqual(result['discount_percent'], 0.0)
        self.assertEqual(result['discount_amount'], 0.0)
        self.assertEqual(result['total'], 250.00)


if __name__ == '__main__':
    unittest.main()
