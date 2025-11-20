"""
Pricing engine for FoodStream Veggies Bot
Calculates order totals with volume discounts and delivery fees
"""
import logging
from typing import Dict, Tuple
from config import Config

logger = logging.getLogger(__name__)


class PricingEngine:
    """Calculate order pricing with discounts"""
    
    def __init__(self):
        self.price_per_bundle = Config.PRICE_PER_BUNDLE
        self.currency_symbol = Config.CURRENCY_SYMBOL
        self.delivery_fee = Config.DELIVERY_FEE
        self.volume_discounts = Config.get_volume_discounts()
    
    def calculate_discount(self, bundles: int) -> float:
        """
        Calculate discount percentage based on volume
        
        Args:
            bundles: Number of bundles ordered
        
        Returns:
            Discount percentage (0-100)
        """
        if not self.volume_discounts:
            return 0.0
        
        # Find highest applicable discount
        applicable_discount = 0.0
        for threshold, discount in sorted(self.volume_discounts.items()):
            if bundles >= threshold:
                applicable_discount = discount
        
        return applicable_discount
    
    def calculate_order(self, bundles: int) -> Dict:
        """
        Calculate complete order pricing
        
        Args:
            bundles: Number of bundles ordered
        
        Returns:
            Dictionary with pricing breakdown:
            {
                'bundles': 10,
                'unit_price': 5.00,
                'subtotal': 50.00,
                'discount_percent': 10.0,
                'discount_amount': 5.00,
                'subtotal_after_discount': 45.00,
                'delivery_fee': 0.00,
                'total': 45.00
            }
        """
        # Calculate subtotal
        subtotal = bundles * self.price_per_bundle
        
        # Calculate discount
        discount_percent = self.calculate_discount(bundles)
        discount_amount = subtotal * (discount_percent / 100)
        subtotal_after_discount = subtotal - discount_amount
        
        # Add delivery fee
        total = subtotal_after_discount + self.delivery_fee
        
        return {
            'bundles': bundles,
            'unit_price': self.price_per_bundle,
            'subtotal': subtotal,
            'discount_percent': discount_percent,
            'discount_amount': discount_amount,
            'subtotal_after_discount': subtotal_after_discount,
            'delivery_fee': self.delivery_fee,
            'total': total
        }
    
    def format_price(self, amount: float) -> str:
        """Format price with currency symbol"""
        return f"{self.currency_symbol}{amount:.2f}"
    
    def get_order_summary(self, bundles: int) -> str:
        """
        Generate human-readable pricing summary
        
        Args:
            bundles: Number of bundles ordered
        
        Returns:
            Formatted pricing summary string
        """
        pricing = self.calculate_order(bundles)
        
        lines = [
            f"💰 *Pricing Breakdown*",
            f"• {pricing['bundles']} bundles × {self.format_price(pricing['unit_price'])} = {self.format_price(pricing['subtotal'])}"
        ]
        
        # Add discount line if applicable
        if pricing['discount_percent'] > 0:
            lines.append(
                f"• Volume discount ({pricing['discount_percent']:.0f}% off): -{self.format_price(pricing['discount_amount'])}"
            )
            lines.append(f"• Subtotal: {self.format_price(pricing['subtotal_after_discount'])}")
        
        # Add delivery fee if applicable
        if pricing['delivery_fee'] > 0:
            lines.append(f"• Delivery fee: {self.format_price(pricing['delivery_fee'])}")
        
        # Total
        lines.append(f"• *TOTAL: {self.format_price(pricing['total'])}*")
        
        return "\n".join(lines)
    
    def get_discount_info(self) -> str:
        """
        Get information about available volume discounts
        
        Returns:
            Formatted string explaining discounts, or empty if none
        """
        if not self.volume_discounts:
            return ""
        
        lines = ["💡 *Volume Discounts Available:*"]
        for threshold, discount in sorted(self.volume_discounts.items()):
            lines.append(f"• {threshold}+ bundles: {discount:.0f}% off!")
        
        return "\n".join(lines)


# Create singleton instance
pricing_engine = PricingEngine()
