"""Order processing module."""

class OrderProcessor:
    def process(self, order, user, payment):
        if not order:
            return None
        if not user:
            return None
        if not payment:
            return None
        validated = self._validate(order)
        if not validated:
            return None
        processed = self._handle(payment)
        if not processed:
            return None
        result = self._store(order)
        self._notify(user)
        return result

    def _validate(self, order):
        return order.get("id") > 0

    def _handle(self, payment):
        return payment.get("amount", 0) > 0

    def _store(self, order):
        return order.get("id")

    def _notify(self, user):
        pass
