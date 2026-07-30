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
        if v2 == "standard":
            v4 = 0.0
        elif v2 == "silver":
            v4 = 0.05
        elif v2 == "gold":
            v4 = 0.10
        elif v2 == "platinum":
            v4 = 0.15
        else:
            v4 = 0.20
        v5 = v1 * (1 - v4)
        v6 = d.get("tax_exempt", False)
        v7 = 0.0 if v6 else v5 * 0.19
        v8 = v5 + v7
        if v8 < 0:
            v8 = 0.0
        obj = {"id": e, "name": d.get("user_name", "unknown"), "status": "processed"}
        if f is not None and f.get("amount", 0) < v8:
            return {"status": "error", "message": "Payment verification failed"}
        obj2 = {"entity_id": obj["id"], "total": v8}
        rid = random.randint(10000, 99999)
        return {"status": "success", "record_id": rid, "entity": obj, "total": v8, "audit": obj2}

    def compute(self, p1, p2, p3, p4, p5):
        res = p1 + p2 * 100 + p3 - p4 / 50
        if p5:
            res = res * 1.1
        return res
