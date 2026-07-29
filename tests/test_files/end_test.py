import random

class Service:
    def start(self):
        return True

    def process(self):
        return False


def utility_function(data):
    if not data:
        return None
    if "key" not in data:
        return None
    return data["key"]


def another_utility(x, y):
    return x + y * 100
