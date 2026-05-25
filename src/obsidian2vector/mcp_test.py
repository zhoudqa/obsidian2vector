#!/usr/bin/env python3
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python3",
        args=["mcp_server.py"],
        env={"PYTHONPATH": "."}
    )

    async with stdio_client(server_params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()

            print("=== Test 1: Search notes ===")
            result = await session.call_tool("search_obsidian", {"query": "论文", "top_k": 2})
            print(result.content[0].text[:500])

            print("\n=== Test 2: List tags ===")
            result = await session.call_tool("list_all_tags", {})
            print(result.content[0].text[:300])

            print("\n=== Test 3: Get note by path ===")
            result = await session.call_tool("get_note_by_path", {"path": "Persons/Scholars/宋爽.md"})
            print(result.content[0].text[:400])

if __name__ == "__main__":
    asyncio.run(main())