#!/bin/bash
# Seed a module with one unreferenced helper (legacy_total) and a factory
# hierarchy that only ever builds one formatter, plus its one caller.
set -euo pipefail
cat > report.py <<'PY'
"""Order report helpers."""
from abc import ABC, abstractmethod


class Formatter(ABC):
    @abstractmethod
    def format(self, value):
        ...


class CurrencyFormatter(Formatter):
    def format(self, value):
        return f"${value:,.2f}"


class FormatterFactory:
    _registry = {"currency": CurrencyFormatter}

    @classmethod
    def create(cls, kind):
        return cls._registry[kind]()


def legacy_total(orders):
    total = 0
    for order in orders:
        total = total + order["amount"]
    return total


def order_total(orders):
    return FormatterFactory.create("currency").format(
        sum(order["amount"] for order in orders))
PY
cat > main.py <<'PY'
from report import order_total

print(order_total([{"amount": 12.5}, {"amount": 7.25}]))
PY
