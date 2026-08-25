import pytest
import time
import uuid
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock

from security.capability_token import TokenManager, IntentContext, CapabilityPayload
from execution.gateway import ExecutionGateway
from execution.adapters.mcp_adapter import RazorpayMCPAdapter
from execution.schema import ExecutionReceipt
from mcp.types import CallToolResult, TextContent

@pytest.fixture
def mock_token_manager():
    return TokenManager(secret=b"test-secret-key-must-be-at-least-32-bytes-long")

@pytest.fixture
def mock_mcp_adapter():
    adapter = RazorpayMCPAdapter(environment="test")
    # Mock network calls
    adapter._initialize_tools = AsyncMock()
    adapter.status = "CONNECTED"
    adapter.tool_cache = ["update_refund", "create_order"]
    
    # Mock ClientSession
    adapter._session = AsyncMock()
    adapter._exit_stack = AsyncMock()
    return adapter

@pytest.fixture
def gateway(mock_token_manager, mock_mcp_adapter):
    return ExecutionGateway(mock_token_manager, mock_mcp_adapter)

@pytest.fixture
def valid_intent():
    return IntentContext(
        intent_id=f"INT-{uuid.uuid4().hex[:6]}",
        agent_id="agent-01",
        action_type="refund",
        amount=5000,
        currency="INR",
        recipient="pay_xyz"
    )

@pytest.mark.asyncio
async def test_valid_capability_token_executes_mcp(gateway, valid_intent, mock_token_manager, mock_mcp_adapter):
    token = mock_token_manager.issue_token(valid_intent, "ALLOW", ttl_seconds=60)
    
    # Mock call_tool response
    mock_result = MagicMock(spec=CallToolResult)
    mock_result.is_error = False
    mock_result.content = [TextContent(type="text", text="rzp_123")]
    mock_mcp_adapter._session.call_tool.return_value = mock_result
    
    receipt = await gateway.execute(token, valid_intent)
    
    assert receipt.status == "SUCCESS"
    assert receipt.provider == "razorpay-mcp"
    assert mock_mcp_adapter._session.call_tool.call_count == 1 # MCP called exactly once

@pytest.mark.asyncio
async def test_no_token_means_no_mcp_call(gateway, valid_intent, mock_mcp_adapter):
    with pytest.raises(ValueError, match="Missing capability token"):
        await gateway.execute("", valid_intent)
        
    assert mock_mcp_adapter._session.call_tool.call_count == 0

@pytest.mark.asyncio
async def test_expired_token_means_no_mcp_call(gateway, valid_intent, mock_token_manager, mock_mcp_adapter):
    token = mock_token_manager.issue_token(valid_intent, "ALLOW", ttl_seconds=-10) # Expired 10s ago
    
    with pytest.raises(ValueError, match="expired"):
        await gateway.execute(token, valid_intent)
        
    assert mock_mcp_adapter._session.call_tool.call_count == 0

@pytest.mark.asyncio
async def test_tampered_token_means_no_mcp_call(gateway, valid_intent, mock_token_manager, mock_mcp_adapter):
    token = mock_token_manager.issue_token(valid_intent, "ALLOW", ttl_seconds=60)
    payload, sig = token.rsplit(".", 1)
    tampered_token = f"{payload}.{sig[:-1]}x"
    
    with pytest.raises(ValueError, match="signature"):
        await gateway.execute(tampered_token, valid_intent)
        
    assert mock_mcp_adapter._session.call_tool.call_count == 0

@pytest.mark.asyncio
async def test_amount_mismatch_means_no_mcp_call(gateway, valid_intent, mock_token_manager, mock_mcp_adapter):
    token = mock_token_manager.issue_token(valid_intent, "ALLOW", ttl_seconds=60)
    
    # Caller attempts to change amount
    malicious_intent = IntentContext(
        intent_id=valid_intent.intent_id,
        agent_id=valid_intent.agent_id,
        action_type=valid_intent.action_type,
        amount=valid_intent.amount * 10,
        currency=valid_intent.currency,
        recipient=valid_intent.recipient
    )
    
    with pytest.raises(ValueError, match="Amount mismatch"):
        await gateway.execute(token, malicious_intent)
        
    assert mock_mcp_adapter._session.call_tool.call_count == 0

@pytest.mark.asyncio
async def test_wrong_action_means_no_mcp_call(gateway, valid_intent, mock_token_manager, mock_mcp_adapter):
    token = mock_token_manager.issue_token(valid_intent, "ALLOW", ttl_seconds=60)
    
    malicious_intent = IntentContext(
        intent_id=valid_intent.intent_id,
        agent_id=valid_intent.agent_id,
        action_type="create_order", # Changed action
        amount=valid_intent.amount,
        currency=valid_intent.currency,
        recipient=valid_intent.recipient
    )
    
    with pytest.raises(ValueError, match="Action type mismatch"):
        await gateway.execute(token, malicious_intent)
        
    assert mock_mcp_adapter._session.call_tool.call_count == 0

@pytest.mark.asyncio
async def test_wrong_agent_means_no_mcp_call(gateway, valid_intent, mock_token_manager, mock_mcp_adapter):
    token = mock_token_manager.issue_token(valid_intent, "ALLOW", ttl_seconds=60)
    
    malicious_intent = IntentContext(
        intent_id=valid_intent.intent_id,
        agent_id="agent-hacker-99", # Changed agent
        action_type=valid_intent.action_type,
        amount=valid_intent.amount,
        currency=valid_intent.currency,
        recipient=valid_intent.recipient
    )
    
    with pytest.raises(ValueError, match="Agent ID mismatch"):
        await gateway.execute(token, malicious_intent)
        
    assert mock_mcp_adapter._session.call_tool.call_count == 0

@pytest.mark.asyncio
async def test_wrong_transaction_means_no_mcp_call(gateway, valid_intent, mock_token_manager, mock_mcp_adapter):
    token = mock_token_manager.issue_token(valid_intent, "ALLOW", ttl_seconds=60)
    
    malicious_intent = IntentContext(
        intent_id="INT-ANOTHER-TX", # Changed intent/tx id
        agent_id=valid_intent.agent_id,
        action_type=valid_intent.action_type,
        amount=valid_intent.amount,
        currency=valid_intent.currency,
        recipient=valid_intent.recipient
    )
    
    with pytest.raises(ValueError, match="Intent ID mismatch"):
        await gateway.execute(token, malicious_intent)
        
    assert mock_mcp_adapter._session.call_tool.call_count == 0

@pytest.mark.asyncio
async def test_currency_mismatch_means_no_mcp_call(gateway, valid_intent, mock_token_manager, mock_mcp_adapter):
    token = mock_token_manager.issue_token(valid_intent, "ALLOW", ttl_seconds=60)
    
    malicious_intent = IntentContext(
        intent_id=valid_intent.intent_id,
        agent_id=valid_intent.agent_id,
        action_type=valid_intent.action_type,
        amount=valid_intent.amount,
        currency="USD", # Changed currency
        recipient=valid_intent.recipient
    )
    
    with pytest.raises(ValueError, match="Currency mismatch"):
        await gateway.execute(token, malicious_intent)
        
    assert mock_mcp_adapter._session.call_tool.call_count == 0

@pytest.mark.asyncio
async def test_replayed_jti_means_no_mcp_call(gateway, valid_intent, mock_token_manager, mock_mcp_adapter):
    token = mock_token_manager.issue_token(valid_intent, "ALLOW", ttl_seconds=60)
    
    mock_result = MagicMock(spec=CallToolResult)
    mock_result.isError = False
    mock_result.content = [TextContent(type="text", text="rzp_123")]
    mock_mcp_adapter._session.call_tool.return_value = mock_result
    
    # First execution succeeds
    await gateway.execute(token, valid_intent)
    assert mock_mcp_adapter._session.call_tool.call_count == 1
    
    # Second execution using same token fails
    with pytest.raises(ValueError, match="replay"):
        await gateway.execute(token, valid_intent)
        
    # Still only 1 MCP call
    assert mock_mcp_adapter._session.call_tool.call_count == 1

@pytest.mark.asyncio
async def test_unauthorized_mcp_tool_means_no_mcp_call(gateway, valid_intent, mock_token_manager, mock_mcp_adapter):
    # E.g. Action that is not in ALLOWED_ACTIONS
    unauthorized_intent = IntentContext(
        intent_id=valid_intent.intent_id,
        agent_id=valid_intent.agent_id,
        action_type="fetch_all_payouts",
        amount=valid_intent.amount,
        currency=valid_intent.currency,
        recipient=valid_intent.recipient
    )
    
    # Mock Policy giving capability for this anyway
    token = mock_token_manager.issue_token(unauthorized_intent, "ALLOW", ttl_seconds=60)
    
    receipt = await gateway.execute(token, unauthorized_intent)
    assert receipt.status == "FAILED"
    assert "not in the allowed MCP actions registry" in receipt.provider_reference
        
    assert mock_mcp_adapter._session.call_tool.call_count == 0

@pytest.mark.asyncio
async def test_mcp_outage_fails_closed(gateway, valid_intent, mock_token_manager, mock_mcp_adapter):
    token = mock_token_manager.issue_token(valid_intent, "ALLOW", ttl_seconds=60)
    
    mock_mcp_adapter._session.call_tool.side_effect = Exception("503 Service Unavailable")
    
    receipt = await gateway.execute(token, valid_intent)
    assert receipt.status == "FAILED"
        
    assert mock_mcp_adapter._session.call_tool.call_count == 1


@pytest.mark.asyncio
async def test_distributed_replay_protection_blocks_second_gateway(valid_intent, mock_mcp_adapter):
    """A shared Redis claim prevents replay across independent gateway instances."""
    class ReplayStore:
        def __init__(self):
            self.values = set()
            self.lock = asyncio.Lock()

        async def set(self, key, value, nx=False, ex=None):
            async with self.lock:
                if nx and key in self.values:
                    return None
                self.values.add(key)
                return True

    secret = b"test-secret-key-must-be-at-least-32-bytes-long"
    issuer = TokenManager(secret=secret)
    verifier_a = TokenManager(secret=secret)
    verifier_b = TokenManager(secret=secret)
    store = ReplayStore()
    gateway_a = ExecutionGateway(verifier_a, mock_mcp_adapter, replay_store=store)
    gateway_b = ExecutionGateway(verifier_b, mock_mcp_adapter, replay_store=store)
    token = issuer.issue_token(valid_intent, "ALLOW", ttl_seconds=60)

    mock_result = MagicMock(spec=CallToolResult)
    mock_result.isError = False
    mock_result.content = [TextContent(type="text", text="rzp_123")]
    mock_mcp_adapter._session.call_tool.return_value = mock_result

    await gateway_a.execute(token, valid_intent)
    with pytest.raises(ValueError, match="replay"):
        await gateway_b.execute(token, valid_intent)

    assert mock_mcp_adapter._session.call_tool.call_count == 1
