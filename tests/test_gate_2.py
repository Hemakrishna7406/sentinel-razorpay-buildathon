import asyncio
import uuid
import logging
from security.capability_token import TokenManager, IntentContext
from execution.gateway import ExecutionGateway
from execution.adapters.mcp_adapter import RazorpayMCPAdapter
import os

logging.basicConfig(level=logging.INFO)


async def run_gate_2():
    print("=== GATE 2: DRY RUN ===")
    token_manager = TokenManager(secret=b"test-secret-key-must-be-at-least-32-bytes-long")
    adapter = RazorpayMCPAdapter(environment="dry_run")
    gateway = ExecutionGateway(token_manager, adapter)

    # 1. Valid create_order
    intent_valid = IntentContext(
        intent_id=f"INT-{uuid.uuid4().hex[:6]}",
        agent_id="test-agent",
        action_type="create_order",
        amount=5000,
        currency="INR",
        recipient="test_xyz",
    )
    token_valid = token_manager.issue_token(intent_valid, "ALLOW", ttl_seconds=60)

    receipt_valid = await gateway.execute(token_valid, intent_valid)
    print(f"1. Valid create_order -> {receipt_valid.status} | MCP Tool: {receipt_valid.mcp_tool}")
    assert receipt_valid.status == "SUCCESS_DRY_RUN"

    # 2. Expired Token
    token_expired = token_manager.issue_token(intent_valid, "ALLOW", ttl_seconds=-10)
    try:
        await gateway.execute(token_expired, intent_valid)
        print("2. Expired token -> FAILED (Unexpected)")
    except ValueError as e:
        print(f"2. Expired token -> Blocked ({str(e)})")

    # 3. Wrong Action
    intent_tampered = IntentContext(
        intent_id=intent_valid.intent_id,
        agent_id=intent_valid.agent_id,
        action_type="refund",  # Tampered!
        amount=intent_valid.amount,
        currency=intent_valid.currency,
        recipient=intent_valid.recipient,
    )
    try:
        await gateway.execute(token_valid, intent_tampered)
        print("3. Tampered action -> FAILED (Unexpected)")
    except ValueError as e:
        print(f"3. Tampered action -> Blocked ({str(e)})")

    if adapter._exit_stack:
        await adapter._exit_stack.aclose()


if __name__ == "__main__":
    asyncio.run(run_gate_2())
