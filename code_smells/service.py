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
        entity = self._build_entity(identifier, data.get("user_name", "unknown"))
        total_amount = self._calculate_entries_total(data["entries"])
        if payment_info is None:
            return {"status": "error", "message": "Payment information missing"}
        if not isinstance(payment_info, dict):
            return {"status": "error", "message": "Payment must be a dictionary"}
        if payment_info.get("amount", 0) <= 0:
            return {"status": "error", "message": "Payment processing failed"}
        if payment_info.get("mode") == "card":
            if len(payment_info.get("number", "")) != 16:
                return {"status": "error", "message": "Payment processing failed"}
        processed_entity = self._enrich_entity(entity, data.get("metadata", {}))
        record_id = self._generate_record_id()
        if delivery is not None:
            delivery_status = self._process_delivery(delivery, processed_entity)
        else:
            delivery_status = "none"
        return {"status": "success", "record_id": record_id, "entity": processed_entity,
                "total": total_amount, "delivery": delivery_status}

    def _build_entity(self, identifier, user_name):
        return {"id": identifier, "name": user_name, "contact": "user@example.com", "created_at": "2024-01-01"}

    def _calculate_entries_total(self, entries):
        return sum(entry.get("count", 0) * entry.get("price", 0) for entry in entries)

    def _enrich_entity(self, entity, metadata):
        enriched = entity.copy()
        enriched.update(metadata)
        enriched["processed"] = True
        return enriched

    def _process_delivery(self, delivery, entity):
        return f"{delivery['method']}_{entity['id']}"

    def _generate_record_id(self):
        return random.randint(10000, 99999)

    def compute(self, base, factor, adjustment, deduction, apply_bonus):
        result = base + factor * 100 + adjustment - deduction / 50
        if apply_bonus:
            result = result * 1.1
        return result
