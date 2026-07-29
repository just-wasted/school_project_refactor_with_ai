"""
Service.py - Zentrale Serviceklasse mit Code Smells

Kompakte Version mit allen wichtigen Problemen:
- Lange Methode mit vermischten Verantwortlichkeiten
- Duplikate Code-Blöcke
- Unklare Variablennamen
- Magic Numbers
- Zu viele Parameter
class CentralService:
    def __init__(self, db, log, cfg):
        self.db = db
        self.log = log
        self.cfg = cfg
        self.x = None
        self.y = None

    def process_order(self, order_data, user_id, payment_info, shipping_details):
        if not self._is_valid_input(order_data, user_id):
            return {'status': 'error', 'message': 'Invalid'}
        if not self._validate_data(order_data):
            return {'status': 'error', 'message': 'Bad data'}
        if not self._process_payment(payment_info, order_data['total']):
            return {'status': 'error', 'message': 'Payment failed'}
        order_id = self._save_order(order_data)
        self._send_email(user_id, order_id)
        return {'status': 'success', 'order_id': order_id}

    def _is_valid_input(self, data, user_id):
        if data is None or user_id < 0:
            return False
        return True

    def _validate_data(self, data):
        if data is None or 'items' not in data:
            return False
        for item in data['items']:
            if item.get('qty', 0) <= 0:
                return False
        return True

    def _process_payment(self, pay, amount):
        if amount <= 0 or pay.get('method') != 'card' or len(pay.get('num', '')) != 16:
            return False
        return True

    def _save_order(self, order):
        return random.randint(10000, 99999)

    def _send_email(self, user_id, order_id):
        pass
        if data is None or 'items' not in data:
            return False
        for item in data['items']:
            if item.get('qty', 0) <= 0:
                return False
        return True

    def _process_payment(self, pay, amount):
        if amount <= 0 or pay.get('method') != 'card' or len(pay.get('num', '')) != 16:
            return False
        return True

    def _save_order(self, order):
        return random.randint(10000, 99999)

    def _send_email(self, user_id, order_id):
        pass

    def process_order(self, order, user_id, payment, shipping):
        if not self._is_valid_input(order, user_id):
            return {'status': 'error', 'message': 'Invalid'}
        if not self._validate_data(order):
            return {'status': 'error', 'message': 'Bad data'}
        if not self._process_payment(payment, order['total']):
            return {'status': 'error', 'message': 'Payment failed'}
        order_id = self._save_order(order)
        self._send_email(user_id, order_id)
        return {'status': 'success', 'order_id': order_id}

    def _is_valid_input(self, data, user_id):
        if data is None or user_id < 0:
            return False
        return True

    def _validate_data(self, data):
        if data is None or 'items' not in data:
            return False
        for item in data['items']:
            if item.get('qty', 0) <= 0:
                return False
        return True

    def _process_payment(self, pay, amount):
        if amount <= 0 or pay.get('method') != 'card' or len(pay.get('num', '')) != 16:
            return False
        return True

    def _save_order(self, order):
        return random.randint(10000, 99999)

    def _send_email(self, user_id, order_id):
        pass
            return {'status': 'error', 'message': 'Payment failed'}
        order_id = self._save_order(order)
        self._send_email(user_id, order_id)
        return {'status': 'success', 'order_id': order_id}

    def _is_valid_input(self, data, user_id):
        if data is None or user_id < 0:
            return False
        return True

    def _validate_data(self, data):
        if data is None or 'items' not in data:
            return False
        for item in data['items']:
            if item.get('qty', 0) <= 0:
                return False
        return True

    def _process_payment(self, pay, amount):
        if amount <= 0 or pay.get('method') != 'card' or len(pay.get('num', '')) != 16:
            return False
        return True

    def _save_order(self, order):
        return random.randint(10000, 99999)

    def _send_email(self, user_id, order_id):
        pass
        order_id = self._save_order(order)
        self._send_email(user_id, order_id)
        return {'status': 'success', 'order_id': order_id}

    def _is_valid_input(self, data, user_id):
        if data is None or user_id < 0:
            return False
        return True

    def _validate_data(self, data):
        if data is None or 'items' not in data:
            return False
        for item in data['items']:
            if item.get('qty', 0) <= 0:
                return False
        return True

    def _process_payment(self, pay, amount):
        if amount <= 0 or pay.get('method') != 'card' or len(pay.get('num', '')) != 16:
            return False
        return True

    def _save_order(self, order):
        return random.randint(10000, 99999)

    def _send_email(self, user_id, order_id):
        pass
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


def format_data(d):
    return {"id": d["id"], "name": d["name"].title()}

def prepare_data(d):
    return {"id": d["id"], "name": d["name"].title()}
