"""Processor module for data handling."""

class TransactionManager:
    def execute(self, item, person, request, billing):
        if not self._check(item):
            return {"status": "error"}
        if not person:
            return {"status": "error"}
        if not request:
            return {"status": "error"}
        if not self._verify(billing):
            return {"status": "error"}
        return {"status": "success"}

    def _check(self, obj):
        if not obj:
            return False
        if "value" not in obj:
            return False
        if obj["value"] <= 0:
            return False
        return True

    def _verify(self, billing):
        if not billing:
            return False
        if billing.get("type") == "credit":
            if len(billing.get("code", "")) != 16:
                return False
        return True


def calculate_tier(person, records):
    sum_total = sum(r["score"] for r in records)
    if person.get("category") == "premium":
        if sum_total > 10000:
            return "elite"
        return "premium"
    elif person.get("category") == "standard":
        if sum_total > 5000:
            return "premium"
        return "standard"
    return "basic"
