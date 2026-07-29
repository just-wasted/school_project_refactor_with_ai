"""
Service.py - Zentrale Serviceklasse mit multiplen Code Smells

Dieses Modul enthält eine zentrale Service-Klasse, die für die Verarbeitung
von Benutzerdaten, Bestellungen und Zahlungen zuständig ist.

PROBLEME:
- Lange Methode (process_order() hat > 50 Zeilen)
- Duplikate (validate_input() und check_data() machen fast das Gleiche)
- Unklare Namen (x, y, temp, doStuff())
- Vermischte Verantwortlichkeiten (Bestellung, Zahlung, Benutzer in einer Methode)
- Magic Numbers (0.1, 100, 50)
- Zu viele Parameter (> 4 in mehreren Methoden)
"""

import datetime
import json
import random
import re


class CentralService:
    """
    Zentrale Service-Klasse für alle Geschäftsvorgänge.
    
    Verantwortlich für:
    - Benutzerverwaltung
    - Bestellabwicklung
    - Zahlungsabwicklung
    - Datenvalidierung
    - Logging
    """

    def __init__(self, db_connection, logger, config, cache, email_service):
        """
        Initialisiert den Service mit allen Abhängigkeiten.
        
        PROBLEM: Zu viele Parameter (> 4) und unklare Namen (x, y)
        """
        self.db = db_connection
        self.log = logger
        self.cfg = config
        self.cache = cache
        self.email = email_service
        self.x = None  # PROBLEM: Unklarer Name
        self.y = None  # PROBLEM: Unklarer Name

    def process_order(self, order_data, user_id, payment_info, shipping_address, discount_code=None):
        """
        Verarbeitet eine Bestellung von Anfang bis Ende.
        
        PROBLEM: Lange Methode (> 50 Zeilen) mit vermischten Verantwortlichkeiten
        """
        # PROBLEM: Magic Number
        if order_data is None or user_id < 0:
            return {"status": "error", "message": "Invalid input"}

        # Schritt 1: Benutzerdaten abrufen
        user = self._get_user_by_id(user_id)
        if user is None:
            self.log.error(f"User {user_id} not found")
            return {"status": "error", "message": "User not found"}

        # Schritt 2: Bestelldaten validieren
        if not self.validate_input(order_data):
            self.log.error("Invalid order data")
            return {"status": "error", "message": "Invalid order data"}

        # Schritt 3: Zahlung verarbeiten
        payment_result = self._process_payment(payment_info, order_data["total"])
        if not payment_result["success"]:
            self.log.error(f"Payment failed: {payment_result['message']}")
            return {"status": "error", "message": "Payment failed"}

        # Schritt 4: Lagerbestand prüfen
        for item in order_data["items"]:
            if not self._check_stock(item["product_id"], item["quantity"]):
                self.log.error(f"Insufficient stock for {item['product_id']}")
                return {"status": "error", "message": "Insufficient stock"}

        # Schritt 5: Bestellung in DB speichern
        order_id = self._save_order(order_data, user_id, payment_info, shipping_address)
        if not order_id:
            self.log.error("Failed to save order")
            return {"status": "error", "message": "Failed to save order"}

        # Schritt 6: Bestätigungs-E-Mail senden
        self.email.send(
            to=user["email"],
            subject="Bestellbestätigung",
            body=f"Ihre Bestellung #{order_id} wurde bestätigt."
        )

        # PROBLEM: Magic Number
        if discount_code and random.random() < 0.1:  # 10% Chance für Rabatt
            discount = order_data["total"] * 0.1
            self._apply_discount(order_id, discount)

        # Schritt 7: Cache aktualisieren
        self.cache.set(f"order_{order_id}", order_data)

        return {"status": "success", "order_id": order_id}

    def validate_input(self, data):
        """
        Validiert Eingabedaten.
        
        PROBLEM: Duplikat von check_data() - fast identische Logik
        """
        if data is None:
            return False
        if not isinstance(data, dict):
            return False
        if "items" not in data:
            return False
        if not data["items"]:
            return False
        for item in data["items"]:
            if "product_id" not in item or "quantity" not in item:
                return False
            if item["quantity"] <= 0:  # PROBLEM: Magic Number
                return False
        return True

    def check_data(self, input_data):
        """
        Überprüft Eingabedaten.
        
        PROBLEM: Duplikat von validate_input() - fast identische Logik
        """
        if input_data is None:
            return False
        if not isinstance(input_data, dict):
            return False
        if "items" not in input_data:
            return False
        if not input_data["items"]:
            return False
        for x in input_data["items"]:  # PROBLEM: Unklarer Name (x)
            if "product_id" not in x or "quantity" not in x:
                return False
            if x["quantity"] < 1:  # PROBLEM: Magic Number, anders als in validate_input
                return False
        return True

    def _get_user_by_id(self, user_id):
        """Holt Benutzer aus der Datenbank."""
        # Simulierte DB-Abfrage
        return {"id": user_id, "name": "Test User", "email": "test@example.com"}

    def _process_payment(self, payment_info, amount):
        """
        Verarbeitet Zahlung.
        
        PROBLEM: Vermischte Verantwortlichkeiten (Validierung + Verarbeitung)
        """
        # PROBLEM: Magic Numbers
        if amount <= 0:
            return {"success": False, "message": "Invalid amount"}
        if amount > 10000:  # PROBLEM: Magic Number
            return {"success": False, "message": "Amount too high"}
        if not self._validate_payment_info(payment_info):
            return {"success": False, "message": "Invalid payment info"}
        return {"success": True, "transaction_id": f"txn_{random.randint(1000, 9999)}"}

    def _validate_payment_info(self, info):
        """Validiert Zahlungsinformationen."""
        if not info:
            return False
        required = ["card_number", "expiry", "cvv"]
        for field in required:
            if field not in info:
                return False
        return True

    def _check_stock(self, product_id, quantity):
        """Prüft Lagerbestand."""
        # Simulierte Lagerprüfung
        return True

    def _save_order(self, order_data, user_id, payment_info, shipping_address):
        """Speichert Bestellung in der Datenbank."""
        # Simuliertes Speichern
        return random.randint(10000, 99999)

    def _apply_discount(self, order_id, amount):
        """Wendet Rabatt an."""
        # Simuliertes Rabatt-Anwenden
        pass

    def doStuff(self, a, b, c, d, e):
        """
        PROBLEM: Unklarer Methodenname und zu viele Parameter (> 4)
        """
        # PROBLEM: Magic Numbers
        result = a + b * 100 + c - d / 50
        if e:
            result = result * 1.1
        return result

    def temp(self, data):
        """
        PROBLEM: Unklarer Methodenname
        """
        # PROBLEM: Vermischte Verantwortlichkeiten + Magic Number
        if len(data) > 50:
            return data[:50]
        return data


# PROBLEM: Duplikat-Code (gleiche Logik in zwei Funktionen)
def format_user_data(user):
    """Formatiert Benutzerdaten."""
    return {
        "id": user["id"],
        "name": user["name"].title(),
        "email": user["email"].lower()
    }


def prepare_user_data(user):
    """Bereitet Benutzerdaten vor."""
    # PROBLEM: Duplikat von format_user_data
    return {
        "id": user["id"],
        "name": user["name"].title(),
        "email": user["email"].lower()
    }
