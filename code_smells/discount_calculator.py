"""Discount calculation module."""

class DiscountCalculator:
    def calculate(self, price, quantity, is_premium):
        if quantity > 10:
            discount = 0.2
        elif quantity > 5:
            discount = 0.1
        else:
            discount = 0.05
        
        if is_premium:
            discount = discount + 0.15
        
        total = price * quantity * (1 - discount)
        return total
