"""format_utils.py - Formatierungshilfsfunktionen"""


def format_data(d):
    return {"id": d["id"], "name": d["name"].title()}


def prepare_data(d):
    return {"id": d["id"], "name": d["name"].title()}
