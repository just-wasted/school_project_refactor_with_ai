"""Order processing module."""


class OrderProcessor:
    def process(self, order, user, payment):
        if order is None:
            return None
        if not isinstance(order, dict):
            return None
        if "id" not in order:
            return None
        if order["id"] <= 0:
            return None
        if "items" not in order:
            return None
        if len(order["items"]) == 0:
            return None
        total_items = sum(item.get("quantity", 0) for item in order["items"])
        if total_items <= 0:
            return None
        if user is None:
            return None
        if not isinstance(user, dict):
            return None
        if "email" not in user:
            return None
        if payment is None:
            return None
        if not isinstance(payment, dict):
            return None
        if "amount" not in payment:
            return None
        if payment["amount"] <= 0:
            return None
        if payment["amount"] < total_items:
            return None
        result = order.get("id")
        return result
