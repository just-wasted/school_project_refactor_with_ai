"""Service module for order handling."""

import random


class ServiceHandler:
    """Main class for processing requests."""

    def __init__(self, db, log, cfg):
        self.db = db
        self.log = log
        self.cfg = cfg

    def handle_request(self, data, identifier, payment_info, delivery):
        if data is None:
            return {"status": "error", "message": "Invalid input data"}
        if not isinstance(data, dict):
            return {"status": "error", "message": "Data must be a dictionary"}
        if "entries" not in data:
            return {"status": "error", "message": "Data validation failed"}
        for entry in data["entries"]:
            if entry.get("count", 0) <= 0:
                return {"status": "error", "message": "Data validation failed"}
        if identifier is None:
            return {"status": "error", "message": "Invalid identifier"}
        if not isinstance(identifier, int):
            return {"status": "error", "message": "Identifier must be an integer"}
        if identifier < 0:
            return {"status": "error", "message": "Invalid identifier"}
        if payment_info is None:
            return {"status": "error", "message": "Payment information missing"}
        if not isinstance(payment_info, dict):
            return {"status": "error", "message": "Payment must be a dictionary"}
        if payment_info.get("amount", 0) <= 0:
            return {"status": "error", "message": "Payment processing failed"}
        if payment_info.get("mode") == "card":
            if len(payment_info.get("number", "")) != 16:
                return {"status": "error", "message": "Payment processing failed"}
        raw_total = sum(entry.get("count", 0) * entry.get("price", 0) for entry in data["entries"])
        customer_tier = data.get("customer_tier", "standard").lower()
        tier_rates = {"standard": 0.0, "silver": 0.05, "gold": 0.10, "platinum": 0.15}
        discount_rate = tier_rates.get(customer_tier, 0.0)
        discounted_total = raw_total * (1 - discount_rate)
        tax_exempt = data.get("tax_exempt", False)
        tax_amount = 0.0 if tax_exempt else discounted_total * 0.19
        final_total = discounted_total + tax_amount
        from datetime import datetime
        try:
            date_str = data.get("timestamp", "2024-01-01")
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            created_at = dt.strftime("%d.%m.%Y %H:%M:%S")
        except:
            created_at = "01.01.2024 00:00:00"
        entity = {
            "id": identifier,
            "name": data.get("user_name", "unknown"),
            "contact": "user@example.com",
            "created_at": created_at,
            "status": "processed",
            "version": "1.0"
        }
        base_days = {"standard": 5, "express": 2, "overnight": 1}
        delivery_eta = base_days.get(delivery.get("method", "standard"), 5) if delivery is not None else None
        if delivery is not None:
            delivery_method = delivery.get("method", "unknown")
            delivery_status = f"{delivery_method.upper()}_{entity['id']}"
        else:
            delivery_status = "none"
        if payment_info.get("amount", 0) < final_total:
            return {"status": "error", "message": "Payment verification failed"}
        if payment_info.get("mode") == "card":
            card_number = payment_info.get("number", "")
            if len(card_number) != 16:
                return {"status": "error", "message": "Payment verification failed"}
        audit_data = {
            "entity_id": entity["id"],
            "total": final_total,
            "tax_rate": 0.19,
            "discount_applied": discount_rate > 0,
            "timestamp": created_at
        }
        record_id = random.randint(10000, 99999)
        return {"status": "success", "record_id": record_id, "entity": entity,
                "total": final_total, "tax": tax_amount, "discount": discount_rate,
                "delivery": delivery_status, "delivery_eta": delivery_eta, "audit": audit_data}

    def compute(self, base, factor, adjustment, deduction, apply_bonus):
        result = base + factor * 100 + adjustment - deduction / 50
        if apply_bonus:
            result = result * 1.1
        return result
