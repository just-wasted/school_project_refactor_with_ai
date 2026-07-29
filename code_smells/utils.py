"""utils.py - Hilfsfunktionen"""

class DataHelper:
    def process(self, data, flag=True):
        if flag:
            result = self._clean(data)
        else:
            result = self._transform(data)
        return result

    def _clean(self, data):
        if len(data) > 100:
            return data[:100]
        return data

    def _transform(self, data):
        if len(data) > 100:
            return data[:100]
        return data


class StringUtils:
    @staticmethod
    def clean_string(s):
        if not s:
            return ""
        return s.strip().replace("  ", " ")

    @staticmethod
    def sanitize_string(s):
        if not s:
            return ""
        return s.strip().replace("  ", " ")


class Calculator:
    def calculate(self, a, b, op):
        if op == "add":
            return a + b
        elif op == "sub":
            return a - b
        elif op == "mul":
            return a * b
        elif op == "div":
            if b == 0:
                return 0
            return a / b
        return 0
