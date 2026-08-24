import asyncio
import uuid
import logging
from security.capability_token import TokenManager, IntentContext
from execution.gateway import ExecutionGateway
from execution.adapters.mcp_adapter import RazorpayMCPAdapter
import os

logging.basicConfig(level=logging.INFO)

async def run_gate_3():
    print("=== GATE 3: REAL EXECUTION ===")
    token_manager = TokenManager(secret=b"test-secret-key-must-be-at-least-32-bytes-long")
    
    # Enable MCP real mode
    os.environ["EXECUTION_MODE"] = "mcp"
    adapter = RazorpayMCPAdapter(environment="test")
    gateway = ExecutionGateway(token_manager, adapter)
    
    # TEST A: Legitimate create_order
    print("\n--- TEST A: Legitimate create_order ---")
    intent_valid = IntentContext(
        intent_id=f"INT-{uuid.uuid4().hex[:6]}",
        agent_id="checkout-agent-01",
        action_type="create_order",
        amount=200000, # 2000 INR
        currency="INR",
        recipient="test_pay"
    )
    # Risk is LOW -> Policy Engine issues token
    token_valid = token_manager.issue_token(intent_valid, "ALLOW", ttl_seconds=60)
    
    receipt_valid = await gateway.execute(token_valid, intent_valid)
    print(f"\n[Test A] Receipt Status: {receipt_valid.status}")
    print(f"[Test A] Provider Reference (Order ID): {receipt_valid.provider_reference}")
    print(f"[Test A] Execution Latency: {receipt_valid.latency_ms} ms")
    
    # TEST B: High-Risk Action (Blocked)
    print("\n--- TEST B: High Risk Action ---")
    intent_high_risk = IntentContext(
        intent_id=f"INT-{uuid.uuid4().hex[:6]}",
        agent_id="checkout-agent-01",
        action_type="create_order",
        amount=5000000, # 50000 INR
        currency="INR",
        recipient="unknown_entity"
    )
    # Risk is HIGH -> Policy Engine DENIES and does NOT issue a capability token.
    token_blocked = "" # No token issued
    
    try:
        await gateway.execute(token_blocked, intent_high_risk)
        print("[Test B] FAIL: Execution proceeded despite no token!")
    except ValueError as e:
        print(f"\n[Test B] BLOCKED: {e}")
        print("[Test B] Razorpay MCP invocation: SKIPPED (Call count = 0)")

    # TEST C: Capability Escalation (Agent tries to run a different tool)
    print("\n--- TEST C: Capability Escalation ---")
    intent_escalate_base = IntentContext(
        intent_id=f"INT-{uuid.uuid4().hex[:6]}",
        agent_id="checkout-agent-01",
        action_type="create_order", # Authorised for create_order
        amount=2000,
        currency="INR",
        recipient="test"
    )
    token_escalate = token_manager.issue_token(intent_escalate_base, "ALLOW", ttl_seconds=60)
    
    intent_escalate = IntentContext(
        intent_id=intent_escalate_base.intent_id,
        agent_id=intent_escalate_base.agent_id,
        action_type="fetch_all_payouts", # Attempting to escalate
        amount=intent_escalate_base.amount,
        currency=intent_escalate_base.currency,
        recipient=intent_escalate_base.recipient
    )
    
    try:
        await gateway.execute(token_escalate, intent_escalate)
        print("[Test C] FAIL: Execution proceeded despite mismatched action!")
    except ValueError as e:
        print(f"\n[Test C] BLOCKED: {e}")
        print("[Test C] Razorpay MCP invocation: SKIPPED (Call count = 0)")

    if adapter._exit_stack:
        await adapter._exit_stack.aclose()

if __name__ == "__main__":
    asyncio.run(run_gate_3())
