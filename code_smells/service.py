import random


class ServiceHandler:

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def handle_request(self, d, e, f, g):
        if d is None:
            return {"status": "error", "message": "Invalid input data"}
        if "entries" not in d:
            return {"status": "error", "message": "Data validation failed"}
        for entry in d["entries"]:
            if entry.get("count", 0) <= 0:
                return {"status": "error", "message": "Data validation failed"}
        v1 = sum(entry.get("count", 0) * entry.get("price", 0) for entry in d["entries"])
        v2 = d.get("customer_tier", "standard").lower()
        v3 = {"standard": 0.0, "silver": 0.05, "gold": 0.10, "platinum": 0.15}
        v4 = v3.get(v2, 0.0)
        v5 = v1 * (1 - v4)
        v6 = d.get("tax_exempt", False)
        v7 = 0.0 if v6 else v5 * 0.19
        v8 = v5 + v7
        obj = {
            "id": e,
            "name": d.get("user_name", "unknown"),
            "contact": "user@example.com",
            "created_at": "2024-01-01",
            "status": "processed"
        }
        if f is not None and f.get("amount", 0) < v8:
            return {"status": "error", "message": "Payment verification failed"}
        obj2 = {"entity_id": obj["id"], "total": v8, "tax_rate": 0.19, "discount_applied": v4 > 0}
        rid = random.randint(10000, 99999)
        return {"status": "success", "record_id": rid, "entity": obj,
                "total": v8, "tax": v7, "discount": v4, "audit": obj2}

    def compute(self, p1, p2, p3, p4, p5):
        res = p1 + p2 * 100 + p3 - p4 / 50
        if p5:
            res = res * 1.1
        return res
