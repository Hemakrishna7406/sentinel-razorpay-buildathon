import pytest
from execution.adapters.mcp_adapter import RazorpayMCPAdapter
from security.capability_token import CapabilityPayload
import time
import os

@pytest.mark.asyncio
async def test_unauthorized_tool_call_blocked():
    """
    Even if an MCP tool is discovered, it cannot be invoked unless it is explicitly
    in the static ALLOWED_ACTIONS registry.
    """
    adapter = RazorpayMCPAdapter(environment="dry_run")
    # Simulate a discovered tool
    adapter.tool_cache = ["update_refund", "create_order", "fetch_all_payouts", "delete_account"]
    adapter.status = "CONNECTED"
    
    # Create a capability token payload for a malicious action
    capability = CapabilityPayload(
        intent_id="int_malicious",
        agent_id="agent_123",
        action_type="fetch_all_payouts", # Not in ALLOWED_ACTIONS
        amount=0,
        currency="INR",
        recipient="",
        decision="ALLOW",
        jti="12345",
        issued_at=int(time.time()),
        expires_at=int(time.time()) + 300
    )
    
    with pytest.raises(ValueError, match="is not in the allowed MCP actions registry"):
        await adapter.execute(capability, {})


def test_no_direct_mcp_path():
    """
    Assert that the MCP adapter is not directly imported or instantiated
    outside of the official ExecutionGateway dependencies.
    """
    # Check api/main.py and worker/ to ensure they don't use RazorpayMCPAdapter directly
    import glob
    
    project_root = os.path.join(os.path.dirname(__file__), "..")
    
    forbidden_imports = [
        "from execution.adapters.mcp_adapter import RazorpayMCPAdapter",
        "import RazorpayMCPAdapter"
    ]
    
    allowed_files = [
        "mcp_adapter.py",
        "dependencies.py", # Where the dependency is wired
        "test_mcp_gates.py", # Tests
        "test_mcp.py",
        "test_execution_gateway.py",
        "test_mcp_boundary.py",
        "test_gate_2.py",
        "test_gate_3.py",
        "test_get_schema.py",
        "test_19_4_unit_chaos.py"
    ]
    
    violations = []
    
    for root, dirs, files in os.walk(project_root):
        if "node_modules" in dirs: dirs.remove("node_modules")
        if ".venv" in dirs: dirs.remove(".venv")
        
        for file in files:
            if file.endswith(".py") and file not in allowed_files:
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    for forbidden in forbidden_imports:
                        if forbidden in content:
                            violations.append(f"{file} contains direct MCP invocation path!")
                            
    assert not violations, "Found direct MCP invocation paths outside of governance boundary:\\n" + "\\n".join(violations)
