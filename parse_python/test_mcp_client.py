#!/usr/bin/env python3

"""
Test client for the MCP graph server.
This demonstrates how to use the server to query function relationships.
"""

import asyncio
import json
import sys
from typing import Dict, Any

# MCP client imports
try:
    from mcp.client import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("MCP client library not found. Install with: pip install mcp")
    sys.exit(1)

async def test_mcp_server():
    """Test the MCP graph server with various queries"""
    
    # Connect to the server
    server_params = StdioServerParameters(
        command="python3",
        args=["mcp_graph_server.py"],
        env={"PYTHONPATH": "."}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            
            print("🔗 Connected to MCP Graph Server")
            print("=" * 50)
            
            # Test 1: Get function details
            print("\n📋 Test 1: Get function details")
            print("-" * 30)
            
            result = await session.call_tool("get_function_details", {
                "function_name": "calculate_sum"
            })
            print(result.content[0].text)
            
            # Test 2: Get function callees
            print("\n📋 Test 2: Get function callees")
            print("-" * 30)
            
            result = await session.call_tool("get_function_callees", {
                "function_name": "calculate_sum"
            })
            print(result.content[0].text)
            
            # Test 3: Get function callers
            print("\n📋 Test 3: Get function callers")
            print("-" * 30)
            
            result = await session.call_tool("get_function_callers", {
                "function_name": "calculate_average"
            })
            print(result.content[0].text)
            
            # Test 4: Search functions
            print("\n📋 Test 4: Search functions")
            print("-" * 30)
            
            result = await session.call_tool("search_functions", {
                "pattern": "calculate"
            })
            print(result.content[0].text)
            
            # Test 5: Get call chain
            print("\n📋 Test 5: Get call chain")
            print("-" * 30)
            
            result = await session.call_tool("get_call_chain", {
                "function_name": "main",
                "max_depth": 3
            })
            print(result.content[0].text)
            
            print("\n✅ All tests completed!")

def main():
    """Main entry point"""
    try:
        asyncio.run(test_mcp_server())
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 