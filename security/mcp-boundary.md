# The MCP Boundary Principle

## Discovery ≠ Authorization

The Model Context Protocol (MCP) allows AI agents to dynamically discover tools exposed by an MCP Server. However, in financial contexts, **discovery does not imply authorization**.

Just because an agent discovers a `delete_account` or `fetch_all_payouts` tool does not mean it is permitted to invoke it.

## Static Allowlist
Sentinel maintains a strictly governed, static `ALLOWED_ACTIONS` registry within the `RazorpayMCPAdapter`:

```python
ALLOWED_ACTIONS = {
    "refund": "update_refund",
    "create_order": "create_order"
}
```

If an agent attempts to invoke an MCP tool that is not explicitly in this allowlist, Sentinel will raise an exception and `BLOCK` the execution, regardless of whether the tool physically exists on the Razorpay MCP server.

## Execution Governance
Sentinel's architecture ensures:
1. **No direct MCP path**: Application code cannot bypass the `ExecutionGateway` to call MCP directly.
2. **Action Mapping**: Semantic intents (e.g., `refund`) are mapped securely to specific MCP capabilities, preventing arbitrary tool invocations.

The existence of an MCP tool does not grant an agent permission to invoke it. Only a cryptographically signed Capability Token, matching an allowed action, can authorize an execution.
