"""Reference correction for the teaching fixture, not shipped product code."""


def retry_delay(attempt: int) -> int:
    return min(2 ** attempt, 30)
