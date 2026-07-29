"""Utilities for data operations."""

class DataProcessor:
    def transform(self, content, enabled=True):
        if enabled:
            output = self._normalize(content)
        else:
            output = self._adjust(content)
        return output

    def _normalize(self, content):
        if len(content) > 100:
            return content[:100]
        return content

    def _adjust(self, content):
        if len(content) > 100:
            return content[:100]
        return content


class TextProcessor:
    @staticmethod
    def process_text(input_str):
        if not input_str:
            return ""
        return input_str.strip().replace("  ", " ")

    @staticmethod
    def clean_text(input_str):
        if not input_str:
            return ""
        return input_str.strip().replace("  ", " ")


class MathHandler:
    def operate(self, x, y, action):
        if action == "sum":
            return x + y
        elif action == "difference":
            return x - y
        elif action == "product":
            return x * y
        elif action == "quotient":
            if y == 0:
                return 0
            return x / y
        return 0
