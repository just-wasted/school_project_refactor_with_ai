"""
Service.py - Zentrale Serviceklasse für Bestellungen
"""

import random


class CentralService:
    """Zentrale Service-Klasse für Bestellungen."""

    def __init__(self, db, log, cfg):
        self.db = db
        self.log = log
        self.cfg = cfg
        self.x = None
        self.y = None

    def process_order(self, order, user_id, payment, shipping):
        if order is None or user_id < 0:
            return {"status": "error", "message": "Invalid"}
        user = self._get_user(user_id)
        if not self.validate_input(order):
            return {"status": "error", "message": "Bad order"}
        if not self.check_data(order):
            return {"status": "error", "message": "Bad data"}
        if not self._process_payment(payment, order["total"]):
            return {"status": "error", "message": "Payment failed"}
        order_id = self._save(order)
        self._send_email(user, order_id)
        return {"status": "success", "order_id": order_id}

    def validate_input(self, data):
        if data is None:
            return False
        if "items" not in data:
            return False
        for item in data["items"]:
            if item.get("qty", 0) <= 0:
                return False
        return True

    def check_data(self, data):
        if data is None:
            return False
        if "items" not in data:
            return False
        for x in data["items"]:
            if x.get("qty", 0) < 1:
                return False
        return True

    def _get_user(self, uid):
        return {"id": uid, "email": "test@example.com"}

    def _process_payment(self, pay, amount):
        if amount <= 0:
            return False
        if pay.get("method") == "card":
            if len(pay.get("num", "")) != 16:
                return False
        return True

    def _save(self, order):
        return random.randint(10000, 99999)

    def _send_email(self, user, oid):
        pass

    def doStuff(self, a, b, c, d, e):
        result = a + b * 100 + c - d / 50
        if e:
            result = result * 1.1
        return result
