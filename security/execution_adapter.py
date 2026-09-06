"""
Sentinel — Execution Adapter

Zero-trust boundary for external mutations.
Simulates a downstream service (like a payment gateway) that strictly demands
a cryptographically signed capability token before executing any state change.
"""

from typing import Optional

from security.capability_token import IntentContext, TokenManager, CapabilityTokenException


class ExecutionException(Exception):
    pass


class ExecutionAdapter:
    """Mock external execution system (e.g. Razorpay Core)."""

    def __init__(self, token_manager: TokenManager):
        # We share the token_manager in this monolithic simulation,
        # but logically this represents the remote verifier.
        self.token_manager = token_manager
        self.mcp_calls = 0

    def execute(self, intent: IntentContext, capability_token: Optional[str]) -> str:
        """
        Execute an intent. Strictly requires a valid capability token.
        Returns a transaction ID if successful.
        """
        if not capability_token:
            raise ExecutionException("Execution denied: Missing capability token.")

        try:
            # 1. Cryptographically verify the token and its invariants
            payload = self.token_manager.verify_token(capability_token, intent)

            # 2. Extract instructions strictly from the verified payload, NOT the request intent
            # (Though verify_token ensures they match exactly)
            executed_amount = payload.amount
            executed_action = payload.action_type
            executed_recipient = payload.recipient

            # 3. Simulate execution
            self.mcp_calls += 1
            tx_id = f"tx_{payload.jti}"

            return tx_id

        except CapabilityTokenException as e:
            raise ExecutionException(f"Execution denied: Invalid capability token. {str(e)}")
        except Exception as e:
            # Fallback fail-closed
            raise ExecutionException(f"Execution denied: Internal failure during verification. {str(e)}")
