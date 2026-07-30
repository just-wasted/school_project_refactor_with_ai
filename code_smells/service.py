"""Service module for order handling."""

import random


class ServiceHandler:
    """Main class for processing requests."""

    def __init__(self, db, log, cfg):
        self.db = db
        self.log = log
        self.cfg = cfg

    def handle_request(self, data, identifier, payment_info, delivery):
        if data is None or identifier < 0:
            return {"status": "error", "message": "Invalid"}
        entity = self._fetch_entity(identifier)
        if not self.check_validity(data):
            return {"status": "error", "message": "Bad data"}
        if not self.ensure_quality(data):
            return {"status": "error", "message": "Bad input"}
        if not self._handle_payment(payment_info, data["amount"]):
            return {"status": "error", "message": "Payment failed"}
        record_id = self._store(data)
        self._notify(entity, record_id)
        return {"status": "success", "record_id": record_id}

    def check_validity(self, content):
        if content is None:
            return False
        if "entries" not in content:
            return False
        for entry in content["entries"]:
            if entry.get("count", 0) <= 0:
                return False
        return True

    def ensure_quality(self, content):
        if content is None:
            return False
        if "entries" not in content:
            return False
        for entry in content["entries"]:
            if entry.get("count", 0) < 1:
                return False
        return True

    def _fetch_entity(self, id):
        return {"id": id, "contact": "user@example.com"}

    def _handle_payment(self, pay, total):
        if total <= 0:
            return False
        if pay.get("mode") == "card":
            if len(pay.get("number", "")) != 16:
                return False
        return True

    def _store(self, content):
        return random.randint(10000, 99999)

    def _notify(self, entity, id):
        pass

    def compute(self, base, factor, adjustment, deduction, apply_bonus):
        result = base + factor * 100 + adjustment - deduction / 50
        if apply_bonus:
            result = result * 1.1
        return result
