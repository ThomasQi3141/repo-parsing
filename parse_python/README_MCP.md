# MCP Graph Function Server

This MCP (Model Context Protocol) server provides structured access to function relationship data extracted from codebases using Joern.

## Features

The server provides the following tools for LLMs to query function relationships:

### 🔍 **get_function_callees**

Get all functions that a given function calls.

**Input:** `{"function_name": "calculate_sum"}`
**Output:** List of functions called by the specified function

### 🔍 **get_function_callers**

Get all functions that call a given function.

**Input:** `{"function_name": "calculate_average"}`
**Output:** List of functions that call the specified function

### 📋 **get_function_details**

Get detailed information about a function including code and metadata.

**Input:** `{"function_name": "calculate_sum"}`
**Output:** Function details (line, type, code snippet, graph)

### 🔎 **search_functions**

Search for functions by name pattern.

**Input:** `{"pattern": "calculate"}`
**Output:** List of functions matching the pattern

### 🔗 **get_call_chain**

Get the complete call chain starting from a function.

**Input:** `{"function_name": "main", "max_depth": 3}`
**Output:** Hierarchical call chain with depth limit

## Setup

### 1. Install Dependencies

```bash
pip install mcp
```

### 2. Generate Graph Data

First, ensure you have graph data available:

```bash
# Parse repository with Joern
python3 dot_to_llm_index.py

# This creates out/llm_index.json
```

### 3. Start the MCP Server

```bash
python3 mcp_graph_server.py --graph-index out/llm_index.json
```

## Usage Examples

### With Claude/GPT-4

The LLM can now use tools like:

```
@get_function_callees({"function_name": "calculate_sum"})
```

```
@get_function_callers({"function_name": "calculate_average"})
```

### With MCP Client

```python
import asyncio
from mcp.client import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def query_function():
    server_params = StdioServerParameters(
        command="python3",
        args=["mcp_graph_server.py"],
        env={"PYTHONPATH": "."}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            result = await session.call_tool("get_function_callees", {
                "function_name": "calculate_sum"
            })
            print(result.content[0].text)

asyncio.run(query_function())
```

## Integration with SWEbench

You can integrate this MCP server with your SWEbench experiments:

1. **Start the MCP server** alongside your LLM
2. **LLM can query function relationships** during code analysis
3. **Enhanced context** for better patch generation

### Example SWEbench Integration

```python
# In your SWEbench evaluation
async def enhanced_evaluation():
    # LLM can now use tools like:
    # @get_function_callees({"function_name": "main"})
    # @get_function_callers({"function_name": "calculate_average"})
    # @get_call_chain({"function_name": "main", "max_depth": 3})
    pass
```

## Configuration

### MCP Config File

Create `mcp_config.json`:

```json
{
  "mcpServers": {
    "graph-function-server": {
      "command": "python3",
      "args": ["mcp_graph_server.py"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

### Environment Variables

- `PYTHONPATH`: Set to include the parse_python directory
- `GRAPH_INDEX_PATH`: Path to the graph index JSON file

## Testing

Run the test client to verify the server works:

```bash
python3 test_mcp_client.py
```

This will test all available tools with sample data.

## Output Format

All tools return structured text responses:

```
Functions called by **calculate_sum**:
- **calculate_average** (Line: 15)
- **sum** (Line: 20)

Functions that call **calculate_average**:
- **calculate_sum** (Line: 5)
- **main** (Line: 25)
```

## Benefits for LLMs

1. **Structured Access**: LLMs can query function relationships programmatically
2. **Rich Context**: Access to code snippets, line numbers, and call chains
3. **Real-time Queries**: Dynamic lookups during code analysis
4. **Standard Protocol**: Uses MCP for compatibility with various LLM frameworks

## Troubleshooting

### Common Issues

1. **MCP library not found**: `pip install mcp`
2. **Graph index not found**: Run `python3 dot_to_llm_index.py` first
3. **Server connection failed**: Check Python path and dependencies

### Debug Mode

Run with debug logging:

```bash
python3 mcp_graph_server.py --debug
```

## Next Steps

1. **Integrate with your LLM framework** (Claude, GPT-4, etc.)
2. **Add more query types** (data flow, dependency analysis)
3. **Scale to larger codebases** with optimized indexing
4. **Add caching** for frequently accessed data
