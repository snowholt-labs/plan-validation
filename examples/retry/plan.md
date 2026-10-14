# Retry delay implementation plan

**Spec:** [spec.md](spec.md)

## Scope

One phase, one implementation task, no new dependency or service. This is a deliberately incomplete teaching fixture.

## Task 1

Implement `retry_delay(attempt: int) -> int` for integer attempts from 0 through 10. Return `2 ** attempt`. Verify attempts 0 and 3 return 1 and 8.

## Verification

Run the bundled acceptance checks against the implementation. The plan omits a required boundary from SPEC; the demonstration preserves the defect for reproduction.
