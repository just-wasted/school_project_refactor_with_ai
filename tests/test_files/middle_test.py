import random

class Processor:
    def method_a(self):
        return self._helper_a()

    def _helper_a(self):
        return 42

    def long_method(self, x, y, z):
        result = x + y
        if z > 0:
            result = result * z
        if result < 0:
            return {"error": "Negative"}
        return {"result": result}

    def method_b(self):
        return self._helper_b()

    def _helper_b(self):
        return 99
