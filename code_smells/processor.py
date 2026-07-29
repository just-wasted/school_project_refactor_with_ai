"""
processor.py - Datenverarbeitungs-Klasse mit Code Smells

Enthält eine Klasse zur Verarbeitung von Bestellungen und Transaktionen.

PROBLEME:
- Lange Methoden
- Duplikate Code-Blöcke
- Unklare Variablennamen (d, temp, result)
- Magic Numbers
- Vermischte Verantwortlichkeiten
- Zu viele Parameter
- Unnötige Kommentare
"""

import datetime
import random


class OrderProcessor:
    """
    Verarbeitet Bestellungen und Transaktionen.
    
    PROBLEM: Klasse hat zu viele Verantwortlichkeiten
    """

    def __init__(self, database, logger, config):
        """Initialisierung."""
        self.db = database
        self.log = logger
        self.cfg = config
        # PROBLEM: Unnötige Kommentare
        # Dies ist die Datenbankverbindung
        # Dies ist der Logger
        # Dies ist die Konfiguration

    def process_transaction(self, transaction, user, order, payment, shipping):
        """
        Verarbeitet eine komplette Transaktion.
        
        PROBLEM: Lange Methode (> 60 Zeilen) mit zu vielen Parametern (> 4)
        und vermischten Verantwortlichkeiten
        """
        # PROBLEM: Unnötiger Kommentar
        # Schritt 1: Validierung
        if not self._validate_transaction(transaction):
            return {"status": "error", "message": "Invalid transaction"}

        # PROBLEM: Unnötiger Kommentar
        # Schritt 2: Benutzer prüfen
        if not self._check_user(user):
            return {"status": "error", "message": "Invalid user"}

        # PROBLEM: Unnötiger Kommentar
        # Schritt 3: Bestellung prüfen
        if not self._validate_order(order):
            return {"status": "error", "message": "Invalid order"}

        # PROBLEM: Unnötiger Kommentar
        # Schritt 4: Zahlung verarbeiten
        payment_result = self._handle_payment(payment, order["total"])
        if not payment_result["success"]:
            return {"status": "error", "message": "Payment failed"}

        # PROBLEM: Unnötiger Kommentar
        # Schritt 5: Lagerbestand prüfen
        for item in order["items"]:
            if not self._check_inventory(item):
                return {"status": "error", "message": "Insufficient inventory"}

        # PROBLEM: Unnötiger Kommentar
        # Schritt 6: Transaktion speichern
        transaction_id = self._save_transaction(transaction, user, order, payment)

        # PROBLEM: Unnötiger Kommentar
        # Schritt 7: Bestätigung senden
        self._send_confirmation(user, order, transaction_id)

        return {"status": "success", "transaction_id": transaction_id}

    def _validate_transaction(self, transaction):
        """Validiert eine Transaktion."""
        if not transaction:
            return False
        if "id" not in transaction:
            return False
        if "amount" not in transaction:
            return False
        # PROBLEM: Magic Number
        if transaction["amount"] <= 0:
            return False
        return True

    def _check_user(self, user):
        """Prüft einen Benutzer."""
        if not user:
            return False
        if "id" not in user:
            return False
        if "email" not in user:
            return False
        return True

    def _validate_order(self, order):
        """Validiert eine Bestellung."""
        if not order:
            return False
        if "id" not in order:
            return False
        if "items" not in order:
            return False
        # PROBLEM: Magic Number
        if len(order["items"]) == 0:
            return False
        return True

    def _handle_payment(self, payment, amount):
        """Verarbeitet eine Zahlung."""
        # PROBLEM: Duplikat-Logik (ähnlich wie in service.py)
        if amount <= 0:
            return {"success": False, "message": "Invalid amount"}
        if not payment:
            return {"success": False, "message": "No payment info"}
        if "method" not in payment:
            return {"success": False, "message": "No payment method"}
        
        # PROBLEM: Magic Numbers
        if payment["method"] == "credit_card":
            if len(payment.get("card_number", "")) != 16:
                return {"success": False, "message": "Invalid card number"}
        elif payment["method"] == "paypal":
            if "@" not in payment.get("email", ""):
                return {"success": False, "message": "Invalid email"}
        
        return {"success": True, "transaction_id": f"tx_{random.randint(1000, 9999)}"}

    def _check_inventory(self, item):
        """Prüft Lagerbestand."""
        # PROBLEM: Magic Number
        if item.get("quantity", 0) <= 0:
            return False
        return True

    def _save_transaction(self, transaction, user, order, payment):
        """Speichert eine Transaktion."""
        # PROBLEM: Zu viele Parameter (> 4)
        # Simuliertes Speichern
        return random.randint(100000, 999999)

    def _send_confirmation(self, user, order, transaction_id):
        """Sendet Bestätigung."""
        # PROBLEM: Unnötiger Kommentar
        # Hier wird die Bestätigung an den Benutzer gesendet
        pass


# PROBLEM: Duplikat-Klasse mit ähnlicher Funktionalität
class TransactionHandler:
    """Alternative Transaktions-Klasse."""

    def handle(self, txn):
        """
        Verarbeitet eine Transaktion.
        
        PROBLEM: Unklarer Parameter (txn), ähnliche Logik wie OrderProcessor
        """
        if not txn:
            return None
        if "amount" not in txn:
            return None
        # PROBLEM: Magic Number
        if txn["amount"] < 0:
            return None
        return self._process(txn)

    def _process(self, data):
        """Verarbeitet Daten."""
        # PROBLEM: Unklarer Name (data) und Magic Number
        if data["amount"] > 10000:
            return None
        return {"id": random.randint(1, 1000), "amount": data["amount"]}


# PROBLEM: Lange Funktion mit vielen if/else Verschachtelungen
def determine_discount_level(user, order_history, current_order):
    """
    Bestimmt den Rabatt-Level eines Benutzers.
    
    PROBLEM: Hohe zyklomatische Komplexität, lange Methode
    """
    # PROBLEM: Magic Numbers
    total_spent = sum(order["amount"] for order in order_history)
    current_amount = current_order.get("amount", 0)
    
    # PROBLEM: Tiefe Verschachtelung
    if user.get("membership") == "gold":
        if total_spent > 10000:
            if current_amount > 5000:
                return "platinum_plus"
            elif current_amount > 2000:
                return "platinum"
            else:
                return "gold_plus"
        else:
            if total_spent > 5000:
                return "gold"
            else:
                return "silver"
    elif user.get("membership") == "silver":
        if total_spent > 5000:
            return "gold"
        elif total_spent > 2000:
            return "silver_plus"
        else:
            return "silver"
    elif user.get("membership") == "bronze":
        if total_spent > 2000:
            return "silver"
        else:
            return "bronze"
    else:
        if total_spent > 1000:
            return "bronze"
        else:
            return "none"


# PROBLEM: Unklare Variablennamen und Magic Numbers
class DataProcessor:
    """Datenprozessor mit unklaren Namen."""

    def process(self, d):
        """
        Verarbeitet Daten.
        
        PROBLEM: Unklarer Parameter (d)
        """
        # PROBLEM: Unklare Variable (temp), Magic Number
        temp = d * 100
        if temp > 5000:
            temp = 5000
        return temp / 100

    def transform(self, x, y):
        """
        Transformiert Daten.
        
        PROBLEM: Unklare Parameternamen (x, y)
        """
        # PROBLEM: Magic Numbers
        result = (x + y) * 10 - 5
        if result < 0:
            result = 0
        return result


# PROBLEM: Duplikat-Funktionen
class ValidationUtils:
    """Validierungs-Hilfsfunktionen."""

    @staticmethod
    def is_valid_email(email):
        """Prüft, ob eine E-Mail gültig ist."""
        if not email:
            return False
        if "@" not in email:
            return False
        return True

    @staticmethod
    def check_email(email):
        """Prüft, ob eine E-Mail gültig ist."""
        # PROBLEM: Duplikat von is_valid_email
        if not email:
            return False
        if "@" not in email:
            return False
        return True

    @staticmethod
    def validate_email(email):
        """Validiert eine E-Mail."""
        # PROBLEM: Duplikat von is_valid_email
        if not email:
            return False
        if "@" not in email:
            return False
        return True
