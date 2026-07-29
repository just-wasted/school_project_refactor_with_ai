"""
utils.py - Hilfsfunktionen mit Code Smells

Enthält Hilfsfunktionen, die in verschiedenen Teilen der Anwendung verwendet werden.

PROBLEME:
- Duplikate (mehrere Funktionen mit fast identischer Logik)
- Unklare Namen (data, item, process())
- Magic Numbers
- Zu lange Methoden
- Vermischte Verantwortlichkeiten
"""

import datetime
import json


class DataHelper:
    """Hilfsklasse für Datenverarbeitung."""

    def process(self, data, flag=True):
        """
        PROBLEM: Unklarer Methodenname (process) und zu viele Verantwortlichkeiten
        """
        if flag:
            result = self._transform(data)
        else:
            result = self._clean(data)
        result = self._validate(result)
        result = self._format(result)
        return result

    def _transform(self, data):
        """Transformiert Daten."""
        # PROBLEM: Magic Number
        if len(data) > 100:
            return data[:100]
        return data

    def _clean(self, data):
        """Bereinigt Daten."""
        # PROBLEM: Magic Number
        if len(data) > 100:
            return data[:100]
        return data

    def _validate(self, data):
        """Validiert Daten."""
        if not data:
            return None
        return data

    def _format(self, data):
        """Formatiert Daten."""
        if isinstance(data, dict):
            return json.dumps(data, indent=2)
        return str(data)


# PROBLEM: Duplikat - gleiche Logik wie DataHelper._transform und _clean
class DataProcessor:
    """Alternative Datenverarbeitungs-Klasse."""

    def handle(self, input_data, mode="transform"):
        """
        PROBLEM: Unklarer Parameter (input_data), zu viele Verantwortlichkeiten
        """
        if mode == "transform":
            if len(input_data) > 100:  # PROBLEM: Magic Number
                return input_data[:100]
            return input_data
        elif mode == "clean":
            if len(input_data) > 100:  # PROBLEM: Magic Number Duplikat
                return input_data[:100]
            return input_data
        else:
            return input_data


# PROBLEM: Lange Funktion mit vermischten Verantwortlichkeiten
def handle_order_processing(order, user, payment, shipping, discount=None):
    """
    Verarbeitet eine Bestellung komplett - PROBLEM: > 40 Zeilen, viele Verantwortlichkeiten
    """
    # Validierung
    if not order:
        return None
    if not user:
        return None
    if not payment:
        return None

    # Berechnungen
    total = 0
    for item in order.get("items", []):
        # PROBLEM: Magic Number
        if item.get("quantity", 0) <= 0:
            continue
        price = item.get("price", 0)
        if price <= 0:  # PROBLEM: Magic Number
            continue
        total += price * item["quantity"]

    # Rabatt anwenden
    if discount:
        # PROBLEM: Magic Number
        if discount > 0.5:  # Maximal 50% Rabatt
            discount = 0.5
        total = total * (1 - discount)

    # Zahlung verarbeiten
    if payment.get("method") == "credit_card":
        if not payment.get("card_number"):
            return None
        # PROBLEM: Magic Number
        if len(payment["card_number"]) != 16:
            return None
    elif payment.get("method") == "paypal":
        if not payment.get("email"):
            return None

    # Versand prüfen
    if shipping:
        if not shipping.get("address"):
            return None
        # PROBLEM: Magic Number
        if len(shipping["address"]) < 10:  # Mindestlänge
            return None

    # Bestätigung generieren
    confirmation = {
        "order_id": order.get("id"),
        "user_id": user.get("id"),
        "total": total,
        "payment_method": payment.get("method"),
        "shipping_address": shipping.get("address") if shipping else None,
        "timestamp": datetime.datetime.now().isoformat()
    }

    return confirmation


# PROBLEM: Duplikate Funktionen
class StringUtils:
    """Hilfsklasse für String-Operationen."""

    @staticmethod
    def clean_string(s):
        """Bereinigt einen String."""
        if not s:
            return ""
        s = s.strip()
        s = s.replace("  ", " ")
        return s

    @staticmethod
    def sanitize_string(s):
        """Bereinigt einen String."""
        # PROBLEM: Duplikat von clean_string
        if not s:
            return ""
        s = s.strip()
        s = s.replace("  ", " ")
        return s

    @staticmethod
    def normalize_string(s):
        """Normalisiert einen String."""
        # PROBLEM: Duplikat von clean_string/sanitize_string
        if not s:
            return ""
        s = s.strip()
        s = s.replace("  ", " ")
        return s.lower()


# PROBLEM: Unklare Namen und Magic Numbers
class Calculator:
    """Einfacher Rechner mit unklaren Namen."""

    def calculate(self, a, b, op):
        """
        PROBLEM: Unklare Parameternamen (a, b, op)
        """
        if op == "add":
            return a + b
        elif op == "sub":
            return a - b
        elif op == "mul":
            return a * b
        elif op == "div":
            # PROBLEM: Magic Number
            if b == 0:
                return 0
            return a / b
        return 0

    def compute(self, x, y, z):
        """
        PROBLEM: Unklare Parameternamen (x, y, z)
        """
        # PROBLEM: Magic Numbers
        return (x * 10 + y * 5 - z * 2) / 3


# PROBLEM: Lange Methode mit vielen Verantwortlichkeiten
def process_user_registration(user_data, email, password, address, phone, newsletter=False):
    """
    Registriert einen neuen Benutzer - PROBLEM: > 30 Zeilen, viele Verantwortlichkeiten
    """
    # Validierung
    if not user_data:
        return {"success": False, "error": "No user data"}
    if not email:
        return {"success": False, "error": "No email"}
    if not password:
        return {"success": False, "error": "No password"}

    # E-Mail-Validierung
    if "@" not in email:
        return {"success": False, "error": "Invalid email"}

    # Passwort-Validierung
    # PROBLEM: Magic Number
    if len(password) < 8:
        return {"success": False, "error": "Password too short"}

    # Adressvalidierung
    if address:
        # PROBLEM: Magic Number
        if len(address) < 10:
            return {"success": False, "error": "Address too short"}

    # Telefonvalidierung
    if phone:
        # PROBLEM: Magic Number
        if len(phone) != 11:
            return {"success": False, "error": "Invalid phone"}

    # Benutzer erstellen
    user_id = generate_user_id()
    user = {
        "id": user_id,
        "email": email.lower(),
        "password_hash": hash_password(password),
        "address": address,
        "phone": phone,
        "newsletter": newsletter,
        "created_at": datetime.datetime.now().isoformat()
    }

    # Willkommens-E-Mail senden
    if newsletter:
        send_welcome_email(email)

    return {"success": True, "user_id": user_id}


# PROBLEM: Unklare Hilfsfunktionen
def generate_user_id():
    """Generiert eine Benutzer-ID."""
    import random
    return random.randint(10000, 99999)


def hash_password(pwd):
    """Hasht ein Passwort."""
    return pwd  # PROBLEM: Kein echtes Hashing!


def send_welcome_email(email):
    """Sendet Willkommens-E-Mail."""
    print(f"Sending welcome email to {email}")
