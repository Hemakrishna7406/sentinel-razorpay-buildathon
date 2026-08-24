# Sentinel — Capability Token Architecture

**Version:** 1.0

---

## 1. Zero-Trust Execution

Sentinel treats the downstream payment/execution gateway as a zero-trust environment. The gateway must never assume that an incoming HTTP request from the business logic layer is authorized, even if it comes from an internal microservice.

To enforce this, all mutating actions (payouts, refunds, checkouts) strictly require a **Capability Token**.

---

## 2. The 10 Invariants

Every Capability Token guarantees 10 strict invariants. If any invariant is violated, the Execution Adapter immediately fails closed and drops the request.

1. **Amount Lock:** The token strictly bounds the `amount` that can be executed. Attempting to execute 50,001 paise with a token authorized for 50,000 paise will fail.
2. **Action Lock:** The `action_type` (e.g., `refund`, `payout`) is cryptographically bound. You cannot use a checkout token to initiate a refund.
3. **Recipient Lock:** The `recipient` (e.g., bank account ID) is locked. Funds cannot be diverted.
4. **Currency Lock:** The `currency` is locked (e.g., `INR`).
5. **Expiration:** Tokens are short-lived. By default, they expire exactly 5 seconds after issuance, preventing delayed replay attacks.
6. **Replay Prevention:** Every token contains a unique Nonce (`jti`). The Execution Adapter consumes this nonce upon verification. A token can be used exactly once.
7. **Cryptographic Signature:** The token payload is serialized and signed via HMAC-SHA256 using a KMS secret known only to the Policy Engine and the verifier.
8. **Immutability:** Business logic cannot modify the token in transit. Any bitflip invalidates the signature.
9. **Independent Verification:** The Execution Adapter recalculates and verifies the signature completely independently, right at the boundary of execution.
10. **Explicit ALLOW:** The payload explicitly contains the string `decision: "ALLOW"`. A token cannot be issued for an `ESCALATE` decision.

---

## 3. Threat Models Mitigated

### Server-Side Request Forgery (SSRF)
If an attacker compromises an internal microservice and attempts to forge requests to the Execution Adapter, they will fail because they lack the cryptographic signing key to forge a Capability Token.

### Time-of-Check to Time-of-Use (TOCTOU)
An attacker cannot get authorization for a $5 transfer, intercept the request in transit, change the body to $50,000, and pass it to the execution adapter. The token payload strictly locks the amount to $5, and the execution adapter verifies the actual execution intent against the token's locked amount.

### Replay Attacks
An attacker capturing a valid token on the network cannot replay it 100 times to drain an account. The JTI is consumed on the first use, and the 5-second expiration limits the window of utility even if the nonce cache were flushed.
