"""
Sentinel — Typed Exceptions

Defines explicit exception types that guarantee fail-closed behavior.
If any of these exceptions bubble up to the API layer, the policy MUST
evaluate to ESCALATE or DENY, never ALLOW.
"""


class SentinelSecurityException(Exception):
    """Base exception for all Sentinel security boundaries."""

    pass


class FailClosedException(SentinelSecurityException):
    """
    Thrown when an unexpected system state occurs that cannot be safely resolved.
    Mandates immediate escalation/denial of the transaction.
    """

    pass


class IdempotencyConflictException(SentinelSecurityException):
    """
    Thrown when a client submits a duplicate idempotency key with mutating parameters.
    Must be blocked to prevent replay attacks or double-spend.
    """

    pass


class BehavioralDuplicateException(SentinelSecurityException):
    """
    Thrown when the intent matches a recently executed intent so closely
    (same agent, amount, recipient) within a very short window that it
    is classified as a likely accidental double-submission or script glitch.
    """

    pass
