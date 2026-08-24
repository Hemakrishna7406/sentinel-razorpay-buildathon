"""
Tests for Execution Adapter failure modes.
"""

import pytest

from security.execution_adapter import ExecutionAdapter, ExecutionException
from security.capability_token import IntentContext, TokenManager


def test_execution_adapter_fails_closed_on_internal_error(monkeypatch):
    """If the execution adapter encounters a system error, it must raise ExecutionException."""
    manager = TokenManager(secret=b"test-secret-key-must-be-at-least-32-bytes-long")
    adapter = ExecutionAdapter(manager)
    
    intent = IntentContext("i1", "ag1", "payout", 1000, "INR", "rec1")
    token = manager.issue_token(intent, "ALLOW")
    
    # Mock verify_token to raise a random non-security exception
    def mock_verify(*args, **kwargs):
        raise MemoryError("Out of memory during verification")
        
    monkeypatch.setattr(adapter.token_manager, "verify_token", mock_verify)
    
    # Must fail closed with an ExecutionException
    with pytest.raises(ExecutionException, match="Internal failure during verification"):
        adapter.execute(intent, token)


def test_execution_denied_on_empty_token():
    adapter = ExecutionAdapter(TokenManager(secret=b"test-secret-key-must-be-at-least-32-bytes-long"))
    intent = IntentContext("i1", "ag1", "payout", 1000, "INR", "rec1")
    
    with pytest.raises(ExecutionException, match="Missing capability token"):
        adapter.execute(intent, "")
