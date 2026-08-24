"""
Sentinel — Execution Gateway

Responsible for simulated and live financial execution.
Validates the Capability Token BEFORE taking any action.
Ensures that no financial action occurs without an exact, valid token.
"""

import logging
from typing import Dict, Any, Optional
import os

from security.capability_token import (
    TokenManager as CapabilityTokenManager,
    IntentContext,
    CapabilityTokenException
)
from execution.provider import PaymentExecutionProvider
from execution.schema import ExecutionReceipt

logger = logging.getLogger(__name__)

class ExecutionGateway:
    def __init__(self, token_manager: CapabilityTokenManager, provider: PaymentExecutionProvider):
        self.token_manager = token_manager
        self.provider = provider
        
    async def execute(self, token: str, expected_intent: IntentContext) -> ExecutionReceipt:
        """
        Validates the capability token and executes the transaction via the provider.
        Raises ValueError (or specific exceptions) if token is invalid or does not match intent.
        """
        if not token:
            logger.error("Execution attempted without a capability token.")
            raise ValueError("Execution rejected: Missing capability token.")
            
        # 1. Capability Validation (Enforces all invariants)
        try:
            payload = self.token_manager.verify_token(token, expected_intent)
        except CapabilityTokenException as e:
            logger.error(f"Execution rejected: {str(e)}")
            raise ValueError(f"Execution rejected: {str(e)}")
            
        logger.info(f"Capability Token Validated (JTI: {payload.jti}). Delegating to provider.")
        
        # 2. Execution Delegation
        # We pass the validated payload so the adapter doesn't blindly trust the caller's requested action.
        
        # The adapter maps the action (e.g., 'refund') to its own MCP tool.
        # We pass the intent properties as arguments.
        args = {
            "amount": payload.amount,
            "currency": payload.currency,
            "recipient": payload.recipient
        }
        
        try:
            receipt = await self.provider.execute(payload, args)
            return receipt
        except Exception as e:
            logger.error(f"Execution Provider Error: {str(e)}")
            # Fail closed
            raise ValueError(f"Execution failed or provider unavailable: {str(e)}")

    def get_provider_status(self) -> Dict[str, Any]:
        return self.provider.get_health()
