# Capability Security & Invariants

Sentinel issues Cryptographic Capability Tokens representing precise, ephemeral authorizations. To successfully invoke the Razorpay MCP, an execution request must satisfy all 10 invariants.

## The 10 Invariants

1. **Amount Lock**: Execution amount must precisely match the token payload.
2. **Action Lock**: Execution action (e.g., `create_order`) must precisely match the token payload.
3. **Recipient Lock**: The financial destination must precisely match the token payload.
4. **Agent Bind**: The `agent_id` initiating the execution must precisely match the token payload (prevents substitution).
5. **Expiration (TTL)**: The current timestamp must be strictly `issued_at <= now <= expires_at`.
6. **Replay Protection (JTI)**: The token's unique identifier (JTI) must not have been previously consumed. A valid capability is not necessarily reusable.
7. **Cryptographic Validity**: The HMAC-SHA256 signature must be valid.
8. **Immutability**: The payload must not have been modified post-issuance.
9. **Currency Lock**: The currency code must precisely match the token payload.
10. **Explicit ALLOW**: The token payload's decision must explicitly read `ALLOW`.

## Cryptographic Security
Tokens are signed using a server-side `CAPABILITY_SIGNING_KEY` (HMAC-SHA256). This secret is isolated from the React frontend and securely injected via environment variables.

## Principle of Exact Action
A capability is not a general permission (e.g., "Agent A is allowed to create orders"). It is a hyper-specific, one-time permission: "Agent A is allowed to create an order for exactly ₹5,000 to recipient bank_456, and only within the next 5 seconds."
