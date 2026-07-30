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
        entity = {"id": identifier, "contact": "user@example.com"}
        if payment_info is None:
            return {"status": "error", "message": "Payment information missing"}
        if not isinstance(payment_info, dict):
            return {"status": "error", "message": "Payment must be a dictionary"}
        if payment_info.get("amount", 0) <= 0:
            return {"status": "error", "message": "Payment processing failed"}
        if payment_info.get("mode") == "card":
            if len(payment_info.get("number", "")) != 16:
                return {"status": "error", "message": "Payment processing failed"}
        record_id = random.randint(10000, 99999)
        if delivery is not None:
            pass
        return {"status": "success", "record_id": record_id}

    def compute(self, base, factor, adjustment, deduction, apply_bonus):
        result = base + factor * 100 + adjustment - deduction / 50
        if apply_bonus:
            result = result * 1.1
        return result
