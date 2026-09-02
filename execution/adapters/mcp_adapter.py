import os
import time
import base64
import uuid
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from contextlib import AsyncExitStack

# Using the official MCP python SDK
try:
    from mcp.client.streamable_http import streamable_http_client
    from mcp.client.session import ClientSession
    import httpx
except ImportError:
    streamable_http_client = None
    ClientSession = None
    httpx = None

from execution.provider import PaymentExecutionProvider
from execution.schema import ExecutionReceipt
from security.capability_token import CapabilityPayload

logger = logging.getLogger(__name__)

class RazorpayMCPAdapter(PaymentExecutionProvider):
    def __init__(self, environment: str = "test"):
        self.environment = environment
        self.mcp_url = "https://mcp.razorpay.com/mcp"
        from core.config import settings
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.status = "DISCONNECTED"
        self.last_health_check = None
        self.available_tools = 0
        self.tool_cache = []
        self.negotiated_protocol = None
        
        # We will hold the connection stack and session open
        self._exit_stack = None
        self._session = None
        self._init_result = None
        self._lock = asyncio.Lock()
        
        # Sentinel action -> Razorpay MCP Tool mapping
        self.ALLOWED_ACTIONS = {
            "refund": "update_refund",
            "create_order": "create_order",
            "simulate_timeout": "simulate_timeout"
        }
        
    async def _initialize_tools(self, force: bool = False):
        """
        Uses the official MCP ClientSession over Streamable HTTP.
        """
        if not self.key_id or not self.key_secret or not streamable_http_client:
            self.status = "FAILED"
            self.last_health_check = datetime.now(timezone.utc).isoformat()
            return
            
        async with self._lock:
            if self.status == "CONNECTED" and not force:
                return

            auth_str = base64.b64encode(f"{self.key_id}:{self.key_secret}".encode()).decode()
            headers = {
                "Authorization": f"Basic {auth_str}"
            }
            
            # Clean up old stack if retrying
            if self._exit_stack:
                try:
                    await self._exit_stack.aclose()
                except Exception:
                    pass
                self._exit_stack = None
                self._session = None
            
            try:
                self._exit_stack = AsyncExitStack()
                http_client = await self._exit_stack.enter_async_context(
                    httpx.AsyncClient(headers=headers, timeout=15.0)
                )
                
                streams = await self._exit_stack.enter_async_context(
                    streamable_http_client(self.mcp_url, http_client=http_client)
                )
                
                read_stream, write_stream = streams
                
                self._session = await self._exit_stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )
                
                self._init_result = await self._session.initialize()
                self.negotiated_protocol = self._init_result.protocol_version
                
                tools_result = await self._session.list_tools()
                self.tool_cache = [t.name for t in tools_result.tools]
                self.available_tools = len(self.tool_cache)
                self.status = "CONNECTED"
                
            except Exception as e:
                logger.error(f"MCP Connection/Discovery failed: {e}")
                self.status = "DEGRADED"
                if self._exit_stack:
                    await self._exit_stack.aclose()
                    self._exit_stack = None
                    self._session = None
            finally:
                self.last_health_check = datetime.now(timezone.utc).isoformat()
            
    async def execute(self, capability: CapabilityPayload, args: Dict[str, Any]) -> ExecutionReceipt:
        start_time = time.time()
        
        # 0. Background recovery
        if self.status != "CONNECTED":
            await self._initialize_tools()
            if self.status != "CONNECTED":
                raise Exception("Razorpay MCP is unavailable or degraded.")
        
        # 1. Action Mapping Boundary
        requested_action = capability.action_type
        if requested_action not in self.ALLOWED_ACTIONS:
            raise ValueError(f"Action '{requested_action}' is not in the allowed MCP actions registry.")
            
        mcp_tool = self.ALLOWED_ACTIONS[requested_action]
        
        if mcp_tool not in self.tool_cache:
            raise ValueError(f"Tool '{mcp_tool}' is not available on the MCP server.")
            
        receipt_id = f"exec_{uuid.uuid4().hex[:12]}"
        
        # 1.5 Validate and Map Arguments to Schema
        mcp_args = {}
        if mcp_tool == "create_order":
            mcp_args = {
                "amount": capability.amount,
                "currency": capability.currency,
                "receipt": capability.jti[:40] # max 40 chars
            }
        elif mcp_tool == "update_refund":
            mcp_args = {
                "refund_id": capability.recipient, # assuming recipient holds refund id
                "notes": {"reason": "Governed by Sentinel"}
            }
        else:
            mcp_args = args # fallback
        
        # 2. Short Circuit Dry Run
        if self.environment == "dry_run":
            latency = int((time.time() - start_time) * 1000)
            
            if mcp_tool == "simulate_timeout":
                time.sleep(0.5)
                return ExecutionReceipt(
                    execution_id=receipt_id,
                    intent_id=capability.intent_id,
                    decision_id=capability.decision,
                    capability_jti=capability.jti,
                    agent_id=capability.agent_id,
                    requested_action=requested_action,
                    mcp_tool=mcp_tool,
                    requested_amount=capability.amount,
                    executed_amount=0,
                    currency=capability.currency,
                    provider="razorpay-mcp",
                    environment="dry_run",
                    status="UNKNOWN",
                    latency_ms=latency,
                    verification_status="VERIFIED",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    provider_reference="simulated_timeout"
                )
                
            return ExecutionReceipt(
                execution_id=receipt_id,
                intent_id=capability.intent_id,
                decision_id=capability.decision,
                capability_jti=capability.jti,
                agent_id=capability.agent_id,
                requested_action=requested_action,
                mcp_tool=mcp_tool,
                requested_amount=capability.amount,
                executed_amount=0,
                currency=capability.currency,
                provider="razorpay-mcp",
                environment="dry_run",
                status="SUCCESS_DRY_RUN",
                latency_ms=latency,
                verification_status="VERIFIED",
                timestamp=datetime.now(timezone.utc).isoformat(),
                provider_reference=None
            )
            
        # 3. Execution using official ClientSession
        # Note: MCP standard doesn't natively expose custom headers per-call for idempotency via SDK easily,
        # but we can pass it via arguments if the tool supports it, or rely on the SDK's transport.
        # Razorpay tools typically accept parameters for idempotency.
        
        execution_status = "FAILED"
        result_data = None
        try:
            # We call the tool via the official SDK
            result = await self._session.call_tool(mcp_tool, arguments=mcp_args)
            if getattr(result, "isError", False):
                error_msg = "Unknown MCP Tool error"
                if result.content and len(result.content) > 0:
                    error_msg = result.content[0].text
                raise Exception(f"MCP Tool returned error: {error_msg}")
            
            # The result from an MCP tool call is a CallToolResult with content
            if result.content and len(result.content) > 0:
                result_data = result.content[0].text
                
            execution_status = "SUCCESS"
        except Exception as e:
            logger.error(f"MCP Call Failed: {e}")
            err_str = str(e).lower()
            
            # Trigger reconnection backoff on next attempt if session broke
            if "connection" in err_str or "stream" in err_str:
                self.status = "DEGRADED" 
                
            # Distinguish between definitive failure and ambiguous timeout
            if "timeout" in err_str or "readtimeout" in err_str:
                execution_status = "UNKNOWN"
            else:
                execution_status = "FAILED"
                
            result_data = f"Error: {str(e)}"
            
        latency = int((time.time() - start_time) * 1000)
        
        return ExecutionReceipt(
            execution_id=receipt_id,
            intent_id=capability.intent_id,
            decision_id=capability.decision,
            capability_jti=capability.jti,
            agent_id=capability.agent_id,
            requested_action=requested_action,
            mcp_tool=mcp_tool,
            requested_amount=capability.amount,
            executed_amount=capability.amount,
            currency=capability.currency,
            provider="razorpay-mcp",
            environment=self.environment,
            status=execution_status,
            latency_ms=latency,
            verification_status="VERIFIED",
            timestamp=datetime.now(timezone.utc).isoformat(),
            provider_reference=result_data # Store the raw result data loosely for now
        )

    async def get_health(self) -> Dict[str, Any]:
        if not self.last_health_check or (time.time() - datetime.fromisoformat(self.last_health_check).timestamp() > 60):
            await self._initialize_tools()
            
        return {
            "provider": "razorpay-mcp",
            "transport": "streamable-http",
            "environment": self.environment,
            "status": self.status,
            "available_tools": self.available_tools,
            "allowed_actions": len(self.ALLOWED_ACTIONS),
            "last_health_check": self.last_health_check
        }

    async def close(self):
        if self._exit_stack:
            try:
                await self._exit_stack.aclose()
            except Exception:
                pass
            self._exit_stack = None
            self._session = None
            self.status = "DISCONNECTED"
