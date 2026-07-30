"""Formatting utilities."""


def prepare_output(data):
    return {"id": data["id"], "title": data["title"].title()}


def format_output(data):
    return {"id": data["id"], "title": data["title"].upper()}
