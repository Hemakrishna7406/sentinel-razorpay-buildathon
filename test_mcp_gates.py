import asyncio
import logging
import mcp
from execution.adapters.mcp_adapter import RazorpayMCPAdapter

logging.getLogger("httpx2").setLevel(logging.WARNING)

async def test_connectivity():
    adapter = RazorpayMCPAdapter(environment="test")
    await adapter._initialize_tools()
    health = await adapter.get_health()
    
    import importlib.metadata
    mcp_version = importlib.metadata.version("mcp")
    
    print(f"MCP SDK version: {mcp_version}")
    print(f"Transport: Streamable HTTP")
    print(f"Endpoint: {adapter.mcp_url}")
    print(f"Initialize: {'SUCCESS' if adapter._init_result else 'FAILED'}")
    print(f"Negotiated protocol version: {adapter.negotiated_protocol}")
    print(f"tools/list: {'SUCCESS' if adapter.tool_cache else 'FAILED'}")
    print(f"Discovered tools: {adapter.available_tools}")
    print(f"Allowed Sentinel tools:")
    for tool in adapter.ALLOWED_ACTIONS.values():
        print(f"  - {tool}")
    print(f"Provider status: {health['status']}")

if __name__ == "__main__":
    asyncio.run(test_connectivity())
