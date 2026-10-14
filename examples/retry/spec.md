# Retry delay specification

## Approved scope

For integer retry attempts from 0 through 10, return the delay in seconds.

- R1: attempt 0 returns 1 second.
- R2: the delay doubles for each subsequent attempt until it reaches the 30-second cap in R3.
- R3: the delay never exceeds 30 seconds; attempt 6 returns 30 seconds.

There is one delivery phase and one implementation task. There are no dependencies, services, persistence, external calls or production deployment. Input validation outside the stated integer range is outside this fixture's scope.
