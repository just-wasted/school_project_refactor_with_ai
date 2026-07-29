"""Formatting utilities."""


def prepare_output(data):
    return {"id": data["id"], "title": data["title"].title()}


def make_output(data):
    return {"id": data["id"], "title": data["title"].title()}
