#!/usr/bin/env python3

"""
MCP (Model Context Protocol) server for graph-based function relationship queries.
This server allows LLMs to query function call relationships and code details.
"""

import json
import os
import sys
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
        LoggingLevel,
    )
except ImportError:
    print("MCP library not found. Install with: pip install mcp")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphMCPServer:
    """MCP server for graph-based function relationship queries"""
    
    def __init__(self, graph_index_path: str = "out/llm_index.json"):
        self.graph_index_path = graph_index_path
        self.graph_data = self.load_graph_data()
        self.server = Server("graph-function-server")
        self.setup_server()
    
    def load_graph_data(self) -> Dict:
        """Load graph data from JSON file"""
        try:
            with open(self.graph_index_path, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded graph data with {len(data.get('function_details', {}))} functions")
                return data
        except FileNotFoundError:
            logger.warning(f"Graph index file {self.graph_index_path} not found")
            return {}
        except Exception as e:
            logger.error(f"Error loading graph data: {e}")
            return {}
    
    def setup_server(self):
        """Set up MCP server with tools and resources"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="get_function_callees",
                    description="Get all functions that a given function calls",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string",
                                "description": "Name of the function to query"
                            }
                        },
                        "required": ["function_name"]
                    }
                ),
                Tool(
                    name="get_function_callers",
                    description="Get all functions that call a given function",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string",
                                "description": "Name of the function to query"
                            }
                        },
                        "required": ["function_name"]
                    }
                ),
                Tool(
                    name="get_function_details",
                    description="Get detailed information about a function including code and metadata",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string",
                                "description": "Name of the function to query"
                            }
                        },
                        "required": ["function_name"]
                    }
                ),
                Tool(
                    name="search_functions",
                    description="Search for functions by name pattern",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Search pattern (supports partial matches)"
                            }
                        },
                        "required": ["pattern"]
                    }
                ),
                Tool(
                    name="get_call_chain",
                    description="Get the complete call chain starting from a function",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string",
                                "description": "Name of the starting function"
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "Maximum depth to traverse (default: 3)",
                                "default": 3
                            }
                        },
                        "required": ["function_name"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            
            if name == "get_function_callees":
                return await self.get_function_callees(arguments["function_name"])
            
            elif name == "get_function_callers":
                return await self.get_function_callers(arguments["function_name"])
            
            elif name == "get_function_details":
                return await self.get_function_details(arguments["function_name"])
            
            elif name == "search_functions":
                return await self.search_functions(arguments["pattern"])
            
            elif name == "get_call_chain":
                max_depth = arguments.get("max_depth", 3)
                return await self.get_call_chain(arguments["function_name"], max_depth)
            
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    async def get_function_callees(self, function_name: str) -> List[TextContent]:
        """Get all functions that the given function calls"""
        callees = []
        
        for graph_name, call_graph in self.graph_data.get("call_graphs", {}).items():
            if function_name in call_graph:
                callees.extend(call_graph[function_name])
        
        if callees:
            # Remove duplicates while preserving order
            unique_callees = list(dict.fromkeys(callees))
            
            # Get details for each callee
            callee_details = []
            for callee in unique_callees:
                details = self.graph_data.get("function_details", {}).get(callee, {})
                callee_details.append(f"- **{callee}** (Line: {details.get('line', 'N/A')})")
            
            result = f"Functions called by **{function_name}**:\n" + "\n".join(callee_details)
        else:
            result = f"Function **{function_name}** does not call any other functions."
        
        return [TextContent(type="text", text=result)]
    
    async def get_function_callers(self, function_name: str) -> List[TextContent]:
        """Get all functions that call the given function"""
        callers = []
        
        for graph_name, called_by in self.graph_data.get("called_by", {}).items():
            if function_name in called_by:
                callers.extend(called_by[function_name])
        
        if callers:
            # Remove duplicates while preserving order
            unique_callers = list(dict.fromkeys(callers))
            
            # Get details for each caller
            caller_details = []
            for caller in unique_callers:
                details = self.graph_data.get("function_details", {}).get(caller, {})
                caller_details.append(f"- **{caller}** (Line: {details.get('line', 'N/A')})")
            
            result = f"Functions that call **{function_name}**:\n" + "\n".join(caller_details)
        else:
            result = f"Function **{function_name}** is not called by any other functions."
        
        return [TextContent(type="text", text=result)]
    
    async def get_function_details(self, function_name: str) -> List[TextContent]:
        """Get detailed information about a function"""
        details = self.graph_data.get("function_details", {}).get(function_name, {})
        
        if details:
            result = f"""## Function: {function_name}

**Line:** {details.get('line', 'N/A')}
**Type:** {details.get('operation_type', 'N/A')}
**Code:** {details.get('snippet', 'N/A')}
**Graph:** {details.get('graph', 'N/A')}"""
        else:
            result = f"Function **{function_name}** not found in the codebase."
        
        return [TextContent(type="text", text=result)]
    
    async def search_functions(self, pattern: str) -> List[TextContent]:
        """Search for functions by name pattern"""
        matching_functions = []
        
        for func_name in self.graph_data.get("function_details", {}).keys():
            if pattern.lower() in func_name.lower():
                matching_functions.append(func_name)
        
        if matching_functions:
            # Sort alphabetically
            matching_functions.sort()
            
            result = f"Functions matching pattern '{pattern}':\n"
            for func_name in matching_functions:
                details = self.graph_data.get("function_details", {}).get(func_name, {})
                result += f"- **{func_name}** (Line: {details.get('line', 'N/A')})\n"
        else:
            result = f"No functions found matching pattern '{pattern}'."
        
        return [TextContent(type="text", text=result)]
    
    async def get_call_chain(self, function_name: str, max_depth: int = 3) -> List[TextContent]:
        """Get the complete call chain starting from a function"""
        def build_chain(start_func: str, depth: int = 0, visited: set = None) -> List[str]:
            if visited is None:
                visited = set()
            
            if depth >= max_depth or start_func in visited:
                return []
            
            visited.add(start_func)
            chain = [start_func]
            
            # Get callees
            for graph_name, call_graph in self.graph_data.get("call_graphs", {}).items():
                if start_func in call_graph:
                    for callee in call_graph[start_func]:
                        if callee not in visited:
                            sub_chain = build_chain(callee, depth + 1, visited.copy())
                            chain.extend(sub_chain)
            
            return chain
        
        chain = build_chain(function_name)
        
        if chain:
            result = f"Call chain starting from **{function_name}** (max depth: {max_depth}):\n"
            for i, func_name in enumerate(chain):
                details = self.graph_data.get("function_details", {}).get(func_name, {})
                indent = "  " * i
                result += f"{indent}- **{func_name}** (Line: {details.get('line', 'N/A')})\n"
        else:
            result = f"No call chain found for function **{function_name}**."
        
        return [TextContent(type="text", text=result)]
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="graph-function-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP server for graph-based function queries")
    parser.add_argument("--graph-index", default="out/llm_index.json", 
                       help="Path to graph index JSON file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run server
    server = GraphMCPServer(args.graph_index)
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 