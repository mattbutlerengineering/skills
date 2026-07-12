"""Fixture module for the charter regression suite (not shipped code)."""


class RetryError(Exception):
    pass


def give_up(attempts):
    raise RetryError("request faled after retries")
