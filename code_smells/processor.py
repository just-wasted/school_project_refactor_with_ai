"""processor.py - Datenverarbeitung"""

class OrderProcessor:
    def process_transaction(self, transaction, user, order, payment):
        if not self._validate(transaction):
            return {"status": "error"}
        if not user:
            return {"status": "error"}
        if not order:
            return {"status": "error"}
        if not self._handle_payment(payment):
            return {"status": "error"}
        return {"status": "success"}

    def _validate(self, txn):
        if not txn:
            return False
        if "amount" not in txn:
            return False
        if txn["amount"] <= 0:
            return False
        return True

    def _handle_payment(self, pay):
        if not pay:
            return False
        if pay.get("method") == "card":
            if len(pay.get("num", "")) != 16:
                return False
        return True


def determine_level(user, history):
    total = sum(o["amount"] for o in history)
    if user.get("type") == "gold":
        if total > 10000:
            return "platinum"
        return "gold"
    elif user.get("type") == "silver":
        if total > 5000:
            return "gold"
        return "silver"
    return "bronze"
