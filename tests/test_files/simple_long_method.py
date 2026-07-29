class Processor:
    def process(self, data):
        if data is None:
            return {"error": "No data"}
        if "items" not in data:
            return {"error": "No items"}
        for item in data["items"]:
            if item.get("qty", 0) <= 0:
                return {"error": "Invalid qty"}
        result = self.calculate(data)
        self.save(result)
        self.notify(data)
        return {"success": True}

    def calculate(self, data):
        return sum(item.get("price", 0) for item in data.get("items", []))

    def save(self, result):
        pass

    def notify(self, data):
        pass
