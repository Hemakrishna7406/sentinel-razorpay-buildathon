import asyncio
import logging
import mcp
import time
from dotenv import load_dotenv
load_dotenv()
from execution.adapters.mcp_adapter import RazorpayMCPAdapter
from security.capability_token import CapabilityPayload

logging.getLogger("httpx").setLevel(logging.WARNING)

async def test_connectivity():
    adapter = RazorpayMCPAdapter(environment="test")
    await adapter._initialize_tools()
    health = await adapter.get_health()
    
    import importlib.metadata
    mcp_version = importlib.metadata.version("mcp")
    
    print(f"MCP SDK version: {mcp_version}")
    print(f"Transport: Streamable HTTP")
    print(f"Endpoint: {adapter.mcp_url}")
    print(f"Initialize: {'SUCCESS' if adapter._init_result else 'FAILED'}")
    print(f"Negotiated protocol version: {adapter.negotiated_protocol}")
    print(f"tools/list: {'SUCCESS' if adapter.tool_cache else 'FAILED'}")
    print(f"Discovered tools: {adapter.available_tools}")
    print(f"Allowed Sentinel tools:")
    for tool in adapter.ALLOWED_ACTIONS.values():
        print(f"  - {tool}")
    print(f"Provider status: {health['status']}")
    
    print("\n--- Testing Positive Valid Capability ---")
    valid_cap = CapabilityPayload(
        jti="test_jti_12345",
        intent_id="intent_123",
        agent_id="agent_foo",
        decision="ALLOW",
        action_type="create_order",
        amount=50000,
        currency="INR",
        recipient="test_recipient",
        issued_at=int(time.time()),
        expires_at=9999999999
    )
    
    try:
        receipt = await adapter.execute(valid_cap, {})
        print(f"MCP CALL: 1")
        print(f"Receipt ID: {receipt.execution_id}")
        print(f"Razorpay Action: {receipt.mcp_tool}")
        print(f"Status: {receipt.status}")
        print(f"Latency: {receipt.latency_ms}ms")
    except Exception as e:
        print(f"Execution failed: {e}")
        
    print("\n--- Testing Negative Invalid Capability ---")
    invalid_cap = CapabilityPayload(
        jti="test_jti_67890",
        intent_id="intent_456",
        agent_id="agent_foo",
        decision="ALLOW",
        action_type="unknown_action",
        amount=50000,
        currency="INR",
        recipient="test_recipient",
        issued_at=int(time.time()),
        expires_at=9999999999
    )
    
    try:
        await adapter.execute(invalid_cap, {})
        print("FAILED: Expected execution to be blocked")
    except Exception as e:
        print(f"MCP CALL: 0 (Blocked by gateway: {e})")
        
    await adapter.close()

if __name__ == "__main__":
    asyncio.run(test_connectivity())
