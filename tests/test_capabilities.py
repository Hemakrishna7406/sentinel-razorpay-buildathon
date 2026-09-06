"""
Tests for Capability Tokens.

Verifies the 10 strict invariants of the Zero-Trust execution model.
Every rejected test must explicitly assert that downstream MCP calls == 0.
"""

import time
import pytest
from security.capability_token import (
    IntentContext,
    TokenManager,
    TokenInvalidException,
    TokenExpiredException,
    TokenTamperedException,
)
from security.execution_adapter import ExecutionAdapter, ExecutionException


@pytest.fixture
def token_manager():
    # Use an explicit secure-length secret for tests to bypass the missing environment variable check
    return TokenManager(secret=b"test-secret-key-must-be-at-least-32-bytes-long")


@pytest.fixture
def execution_adapter(token_manager):
    return ExecutionAdapter(token_manager)


@pytest.fixture
def sample_intent():
    return IntentContext(
        intent_id="int_123",
        agent_id="agent_alpha",
        action_type="payout",
        amount=50000,
        currency="INR",
        recipient="bank_456",
    )


def test_invariant_10_explicit_allow(token_manager, sample_intent):
    """Invariant 10: Cannot issue token for non-ALLOW decision."""
    with pytest.raises(TokenInvalidException, match="non-ALLOW"):
        token_manager.issue_token(sample_intent, decision="ESCALATE")


def test_invariant_7_and_9_valid_signature(token_manager, execution_adapter, sample_intent):
    """Invariant 7, 9: Valid token passes execution adapter."""
    token = token_manager.issue_token(sample_intent, decision="ALLOW")
    tx_id = execution_adapter.execute(sample_intent, token)
    assert tx_id.startswith("tx_")
    assert execution_adapter.mcp_calls == 1


def test_invariant_8_immutability(token_manager, execution_adapter, sample_intent):
    """Invariant 8: Tampering with payload invalidates signature."""
    token = token_manager.issue_token(sample_intent, decision="ALLOW")

    # Tamper with the amount in the payload
    payload, sig = token.split(".")
    tampered_payload = payload.replace("50000", "99999")
    tampered_token = f"{tampered_payload}.{sig}"

    with pytest.raises(ExecutionException, match="Invalid signature"):
        execution_adapter.execute(sample_intent, tampered_token)
    assert execution_adapter.mcp_calls == 0


def test_invariant_6_replay_prevention(token_manager, execution_adapter, sample_intent):
    """Invariant 6: Token can only be used once."""
    token = token_manager.issue_token(sample_intent, decision="ALLOW")

    # First use succeeds
    execution_adapter.execute(sample_intent, token)
    assert execution_adapter.mcp_calls == 1

    # Second use fails
    with pytest.raises(ExecutionException, match="replay attack"):
        execution_adapter.execute(sample_intent, token)
    assert execution_adapter.mcp_calls == 1  # No additional calls


def test_invariant_5_expiration(token_manager, execution_adapter, sample_intent):
    """Invariant 5: Deterministic expiration race."""
    token = token_manager.issue_token(sample_intent, decision="ALLOW", ttl_seconds=0)

    # Wait to ensure it crosses the precise integer timestamp boundary
    time.sleep(1)

    with pytest.raises(ExecutionException, match="expired"):
        execution_adapter.execute(sample_intent, token)
    assert execution_adapter.mcp_calls == 0


def test_invariant_1_amount_lock(token_manager, execution_adapter, sample_intent):
    """Invariant 1: Execution amount must match token exactly."""
    token = token_manager.issue_token(sample_intent, decision="ALLOW")

    # Attempt to execute with a different intent amount
    malicious_intent = IntentContext(
        intent_id=sample_intent.intent_id,
        agent_id=sample_intent.agent_id,
        action_type=sample_intent.action_type,
        amount=99999,  # Changed
        currency=sample_intent.currency,
        recipient=sample_intent.recipient,
    )

    with pytest.raises(ExecutionException, match="Amount mismatch"):
        execution_adapter.execute(malicious_intent, token)
    assert execution_adapter.mcp_calls == 0


def test_invariant_2_action_lock(token_manager, execution_adapter, sample_intent):
    """Invariant 2: Execution action must match token exactly."""
    token = token_manager.issue_token(sample_intent, decision="ALLOW")

    malicious_intent = IntentContext(
        intent_id=sample_intent.intent_id,
        agent_id=sample_intent.agent_id,
        action_type="refund",  # Changed
        amount=sample_intent.amount,
        currency=sample_intent.currency,
        recipient=sample_intent.recipient,
    )

    with pytest.raises(ExecutionException, match="Action type mismatch"):
        execution_adapter.execute(malicious_intent, token)
    assert execution_adapter.mcp_calls == 0


def test_invariant_3_recipient_lock(token_manager, execution_adapter, sample_intent):
    """Invariant 3: Execution recipient must match token exactly."""
    token = token_manager.issue_token(sample_intent, decision="ALLOW")

    malicious_intent = IntentContext(
        intent_id=sample_intent.intent_id,
        agent_id=sample_intent.agent_id,
        action_type=sample_intent.action_type,
        amount=sample_intent.amount,
        currency=sample_intent.currency,
        recipient="attacker_bank",  # Changed
    )

    with pytest.raises(ExecutionException, match="Recipient mismatch"):
        execution_adapter.execute(malicious_intent, token)
    assert execution_adapter.mcp_calls == 0


def test_invariant_4_agent_impersonation(token_manager, execution_adapter, sample_intent):
    """Invariant 4: Execution agent must match token exactly (impersonation)."""
    token = token_manager.issue_token(sample_intent, decision="ALLOW")

    malicious_intent = IntentContext(
        intent_id=sample_intent.intent_id,
        agent_id="agent_malicious",  # Changed
        action_type=sample_intent.action_type,
        amount=sample_intent.amount,
        currency=sample_intent.currency,
        recipient=sample_intent.recipient,
    )

    with pytest.raises(ExecutionException, match="Agent ID mismatch"):
        execution_adapter.execute(malicious_intent, token)
    assert execution_adapter.mcp_calls == 0


def test_invariant_9_currency_lock(token_manager, execution_adapter, sample_intent):
    """Invariant 9: Currency mismatch."""
    token = token_manager.issue_token(sample_intent, decision="ALLOW")

    malicious_intent = IntentContext(
        intent_id=sample_intent.intent_id,
        agent_id=sample_intent.agent_id,
        action_type=sample_intent.action_type,
        amount=sample_intent.amount,
        currency="USD",  # Changed
        recipient=sample_intent.recipient,
    )

    with pytest.raises(ExecutionException, match="Currency mismatch"):
        execution_adapter.execute(malicious_intent, token)
    assert execution_adapter.mcp_calls == 0


def test_token_substitution(token_manager, execution_adapter, sample_intent):
    """Token substitution: Agent B attempts to use Agent A's token for identical intent."""
    token_a = token_manager.issue_token(sample_intent, decision="ALLOW")

    # Agent B has their own intent that matches Agent A's exactly, but is issued for B
    intent_b = IntentContext(
        intent_id=sample_intent.intent_id,
        agent_id="agent_beta",  # Different agent
        action_type=sample_intent.action_type,
        amount=sample_intent.amount,
        currency=sample_intent.currency,
        recipient=sample_intent.recipient,
    )

    # Agent B tries to execute with Agent A's token
    with pytest.raises(ExecutionException, match="Agent ID mismatch"):
        execution_adapter.execute(intent_b, token_a)
    assert execution_adapter.mcp_calls == 0


def test_missing_token_blocked(execution_adapter, sample_intent):
    """Execution without a token is completely denied."""
    with pytest.raises(ExecutionException, match="Missing capability token"):
        execution_adapter.execute(sample_intent, None)
    assert execution_adapter.mcp_calls == 0
