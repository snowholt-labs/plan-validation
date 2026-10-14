"""Deliberately incomplete fixture: the plan omitted the maximum delay."""


def retry_delay(attempt: int) -> int:
    return 2 ** attempt
