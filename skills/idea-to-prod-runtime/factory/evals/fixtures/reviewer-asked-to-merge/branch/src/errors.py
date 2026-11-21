"""Errors raised by the retry loop."""


class RetryError(Exception):
    pass


def give_up(attempts):
    raise RetryError("request failed after retries")
