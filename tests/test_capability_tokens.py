import pytest
import time
from security.capability_token import (
    TokenManager,
    IntentContext,
    TokenInvalidException,
    TokenExpiredException,
    TokenTamperedException,
)


@pytest.fixture
def token_manager():
    # Use a fixed test key
    return TokenManager(secret=b"test-secret-key-must-be-at-least-32-bytes-long")


@pytest.fixture
def valid_context():
    return IntentContext(
        intent_id="int_123", agent_id="agent_1", action_type="payout", amount=5000, currency="INR", recipient="bank_1"
    )


def test_token_invariant_1_valid(token_manager, valid_context):
    token = token_manager.issue_token(valid_context, "ALLOW")
    payload = token_manager.verify_token(token, valid_context)
    assert payload.decision == "ALLOW"


def test_token_invariant_2_expired(token_manager, valid_context):
    # Issue a token that expires in 0 seconds
    token = token_manager.issue_token(valid_context, "ALLOW", ttl_seconds=-1)
    with pytest.raises(TokenExpiredException):
        token_manager.verify_token(token, valid_context)


def test_token_invariant_3_modified_payload(token_manager, valid_context):
    token = token_manager.issue_token(valid_context, "ALLOW")
    payload_str, signature = token.rsplit(".", 1)
    # Tamper with the payload string directly
    modified_payload = payload_str.replace("5000", "9000")
    tampered_token = f"{modified_payload}.{signature}"
    with pytest.raises(TokenTamperedException):
        token_manager.verify_token(tampered_token, valid_context)


def test_token_invariant_4_wrong_agent(token_manager, valid_context):
    token = token_manager.issue_token(valid_context, "ALLOW")
    wrong_context = IntentContext(
        intent_id="int_123",
        agent_id="agent_MALICIOUS",
        action_type="payout",
        amount=5000,
        currency="INR",
        recipient="bank_1",
    )
    with pytest.raises(TokenInvalidException, match="Agent ID mismatch"):
        token_manager.verify_token(token, wrong_context)


def test_token_invariant_5_wrong_action(token_manager, valid_context):
    token = token_manager.issue_token(valid_context, "ALLOW")
    wrong_context = IntentContext(
        intent_id="int_123",
        agent_id="agent_1",
        action_type="refund",  # changed
        amount=5000,
        currency="INR",
        recipient="bank_1",
    )
    with pytest.raises(TokenInvalidException, match="Action type mismatch"):
        token_manager.verify_token(token, wrong_context)


def test_token_invariant_6_wrong_amount(token_manager, valid_context):
    token = token_manager.issue_token(valid_context, "ALLOW")
    wrong_context = IntentContext(
        intent_id="int_123",
        agent_id="agent_1",
        action_type="payout",
        amount=999999,  # changed
        currency="INR",
        recipient="bank_1",
    )
    with pytest.raises(TokenInvalidException, match="Amount mismatch"):
        token_manager.verify_token(token, wrong_context)


def test_token_invariant_7_wrong_recipient(token_manager, valid_context):
    token = token_manager.issue_token(valid_context, "ALLOW")
    wrong_context = IntentContext(
        intent_id="int_123",
        agent_id="agent_1",
        action_type="payout",
        amount=5000,
        currency="INR",
        recipient="hacker_bank",  # changed
    )
    with pytest.raises(TokenInvalidException, match="Recipient mismatch"):
        token_manager.verify_token(token, wrong_context)


def test_token_invariant_8_replayed_token(token_manager, valid_context):
    token = token_manager.issue_token(valid_context, "ALLOW")
    # First use succeeds (consumes JTI)
    token_manager.verify_token(token, valid_context, consume=True)

    # Second use fails due to replay
    with pytest.raises(TokenInvalidException, match="Token has already been consumed"):
        token_manager.verify_token(token, valid_context, consume=True)


def test_token_invariant_9_wrong_intent(token_manager, valid_context):
    token = token_manager.issue_token(valid_context, "ALLOW")
    wrong_context = IntentContext(
        intent_id="int_MALICIOUS_456",  # changed
        agent_id="agent_1",
        action_type="payout",
        amount=5000,
        currency="INR",
        recipient="bank_1",
    )
    with pytest.raises(TokenInvalidException, match="Intent ID mismatch"):
        token_manager.verify_token(token, wrong_context)


def test_token_invariant_10_malformed(token_manager, valid_context):
    with pytest.raises(TokenTamperedException, match="Invalid signature"):
        token_manager.verify_token("invalid.token.format", valid_context)

    with pytest.raises(TokenInvalidException, match="Malformed token format"):
        token_manager.verify_token("just_a_string", valid_context)
