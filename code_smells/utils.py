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
        if len(content) > 120:
            return content[:120]
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
        return input_str.strip().replace("\t", " ")


class MathHandler:
    def operate(self, first_value, second_value, action):
        if action == "sum":
            return first_value + second_value
        elif action == "difference":
            return first_value - second_value
        elif action == "product":
            return first_value * second_value
        elif action == "quotient":
            if second_value == 0:
                return 0
            return first_value / second_value
        return 0
