"""
Tests for Fail-Closed mechanisms.

Ensures that expected errors raise typed SentinelSecurityExceptions
and unexpected errors can be wrapped to fail closed.
"""

import pytest

from security.exceptions import (
    FailClosedException, 
    IdempotencyConflictException, 
    SentinelSecurityException
)
from security.policy import PolicyEngine


def test_exception_hierarchy():
    """Verify exceptions inherit from the base security exception."""
    assert issubclass(FailClosedException, SentinelSecurityException)
    assert issubclass(IdempotencyConflictException, SentinelSecurityException)


def test_policy_engine_fails_closed_on_token_error(monkeypatch):
    """If the token manager fails to issue, the policy engine must ESCALATE."""
    engine = PolicyEngine()
    
    # Force the token manager to raise a random exception
    def mock_issue(*args, **kwargs):
        raise ValueError("Database disconnected during token issuance")
        
    monkeypatch.setattr(engine.token_manager, "issue_token", mock_issue)
    
    from security.capability_token import IntentContext
    intent = IntentContext("i1", "ag1", "payout", 1000, "INR", "rec1")
    
    # Should safely catch the ValueError and return ESCALATE
    decision, reason, token = engine.evaluate(intent, {"has_sufficient_history": 1}, 0.1)
    
    assert decision == "ESCALATE"
    assert token is None
    assert "Failed to issue capability token" in reason
