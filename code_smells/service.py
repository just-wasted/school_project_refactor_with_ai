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
        if v5 < 0:
            v5 = 0.0
        if v5 > 10000:
            v5 = 10000.0
        obj = {"id": e, "name": d.get("user_name", "unknown")}
        if f is not None and f.get("amount", 0) < v5:
            return {"status": "error", "message": "Payment verification failed"}
        return {"status": "success", "record_id": random.randint(10000, 99999), "entity": obj, "total": v5}

    def compute(self, p1, p2, p3, p4, p5):
        res = p1 + p2 * 100 + p3 - p4 / 50
        if p5:
            res = res * 1.1
        return res
