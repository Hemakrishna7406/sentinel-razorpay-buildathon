"""
Sentinel — Capability Token

Cryptographic token guaranteeing that a specific action has been explicitly authorized
by the Policy Engine. Required by the Execution Adapter before any external
mutation occurs. Implements 10 strict invariants.
"""

import hmac
import hashlib
import json
import secrets
import time
from dataclasses import asdict, dataclass
from typing import Optional


@dataclass(frozen=True)
class IntentContext:
    intent_id: str
    agent_id: str
    action_type: str
    amount: int
    currency: str
    recipient: str


@dataclass(frozen=True)
class CapabilityPayload:
    intent_id: str
    agent_id: str
    action_type: str
    amount: int
    currency: str
    recipient: str
    decision: str
    jti: str
    issued_at: int
    expires_at: int


class CapabilityTokenException(Exception):
    """Base exception for capability token failures."""
    pass


class TokenExpiredException(CapabilityTokenException):
    pass


class TokenTamperedException(CapabilityTokenException):
    pass


class TokenInvalidException(CapabilityTokenException):
    pass


import os

class TokenManager:
    """Issues and verifies capability tokens."""
    
    def __init__(self, secret: Optional[bytes] = None):
        if secret is None:
            key_str = os.environ.get("CAPABILITY_SIGNING_KEY")
            if not key_str:
                raise ValueError("Startup failure: CAPABILITY_SIGNING_KEY is missing or empty.")
            if len(key_str) < 32:
                raise ValueError("Startup failure: CAPABILITY_SIGNING_KEY is too weak (must be >= 32 characters).")
            # Protect against known test keys in production
            if key_str == "sentinel-local-dev-secret-do-not-use-in-prod" and os.environ.get("ENVIRONMENT", "production") == "production":
                raise ValueError("Startup failure: Cannot use development signing key in production environment.")
            self._secret = key_str.encode("utf-8")
        else:
            # Allow passing explicit secret for tests
            self._secret = secret
            
        self._consumed_jtis = set()  # In-memory replay cache (mocking Redis)

    def _sign(self, payload_str: str) -> str:
        """Sign a string payload using HMAC-SHA256."""
        return hmac.new(self._secret, payload_str.encode("utf-8"), hashlib.sha256).hexdigest()

    def issue_token(self, intent: IntentContext, decision: str, ttl_seconds: int = 5) -> str:
        """
        Issue a signed capability token for an ALLOWED decision.
        If decision is not ALLOWED, raises an exception (defense in depth).
        """
        if decision != "ALLOW":
            raise TokenInvalidException("Cannot issue capability token for non-ALLOW decision.")
            
        now = int(time.time())
        jti = secrets.token_hex(16)
        
        payload = CapabilityPayload(
            intent_id=intent.intent_id,
            agent_id=intent.agent_id,
            action_type=intent.action_type,
            amount=intent.amount,
            currency=intent.currency,
            recipient=intent.recipient,
            decision=decision,
            jti=jti,
            issued_at=now,
            expires_at=now + ttl_seconds
        )
        
        payload_dict = asdict(payload)
        # Sort keys to ensure deterministic serialization for signature
        payload_str = json.dumps(payload_dict, sort_keys=True)
        signature = self._sign(payload_str)
        
        return f"{payload_str}.{signature}"

    def verify_token(self, token: str, context: IntentContext) -> CapabilityPayload:
        """
        Verify a token against the execution context.
        Enforces all 10 invariants.
        """
        try:
            payload_str, signature = token.rsplit(".", 1)
        except ValueError:
            raise TokenInvalidException("Malformed token format.")
            
        # Invariant 7 & 8: Cryptographic signature (Tamper-proof)
        expected_sig = self._sign(payload_str)
        if not hmac.compare_digest(expected_sig, signature):
            raise TokenTamperedException("Invalid signature.")
            
        try:
            payload_dict = json.loads(payload_str)
            payload = CapabilityPayload(**payload_dict)
        except Exception:
            raise TokenInvalidException("Invalid token payload format.")
            
        # Invariant 10: Explicit ALLOW
        if payload.decision != "ALLOW":
            raise TokenInvalidException(f"Token decision is not ALLOW, got {payload.decision}")
            
        # Invariant 5: Expiration
        now = int(time.time())
        if now > payload.expires_at:
            raise TokenExpiredException(f"Token expired {now - payload.expires_at} seconds ago.")
            
        # Invariant 6: Replay prevention (Nonce/JTI)
        if payload.jti in self._consumed_jtis:
            raise TokenInvalidException("Token has already been consumed (replay attack).")
            
        # Invariant 1, 2, 3, 4, 9: Strict bounding to context
        if payload.intent_id != context.intent_id:
            raise TokenInvalidException("Intent ID mismatch.")
        if payload.agent_id != context.agent_id:
            raise TokenInvalidException("Agent ID mismatch.")
        if payload.action_type != context.action_type:
            raise TokenInvalidException("Action type mismatch.")
        if payload.amount != context.amount:
            raise TokenInvalidException(f"Amount mismatch. Token authorizes {payload.amount}, request is {context.amount}")
        if payload.currency != context.currency:
            raise TokenInvalidException("Currency mismatch.")
        if payload.recipient != context.recipient:
            raise TokenInvalidException("Recipient mismatch.")
            
        # Consume the token
        self._consumed_jtis.add(payload.jti)
        
        return payload
