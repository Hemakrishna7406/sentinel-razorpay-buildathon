import asyncio
from execution.adapters.mcp_adapter import RazorpayMCPAdapter

async def run():
    a = RazorpayMCPAdapter(environment="test")
    await a._initialize_tools()
    tools = (await a._session.list_tools()).tools
    for t in tools:
        if t.name == "create_order":
            print("create_order schema:", t.input_schema)
        if t.name == "update_refund":
            print("update_refund schema:", t.input_schema)
    if a._exit_stack:
        await a._exit_stack.aclose()

if __name__ == "__main__":
    asyncio.run(run())
