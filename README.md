# Call Graph MCP Server (FastMCP) – Quick Start

Follow these steps to generate a call graph for a repository, run the FastMCP server, and use it with Codex.

## 1) Configure Codex

Copy this to `~/.codex/config.toml` and edit the absolute paths for your machine:

```toml
[mcp_servers.call_graph]
command = "mcp"
args = ["run", "/Users/tq/Documents/GitHub/repo-parsing/mcp_server/mcp-call-graph.py"]
env = { "CALLGRAPH_OUT_DIR" = "/Users/tq/Documents/GitHub/repo-parsing/out" }
startup_timeout_ms = 20000
```

## 2) Add a repository

Place your target repo under `repos/[your-repo-name]`.

Example:

```
repos/pylint
```

## 3) Export the call graph

From the project root:

```bash
./export_callgraph.sh repos/[your-repo-name] out
```

You should now see:

- `out/methods.csv`
- `out/calls.csv`

## 4) (Optional) Test the MCP server

```bash
cd mcp_server
# Create and use a virtual environment (recommended)
python3 -m venv venv && source venv/bin/activate
# Install required packages
pip install mcp httpx

# Run with the MCP Inspector/dev harness
mcp dev mcp-call-graph.py
```

## 5) Run Codex

```bash
codex
```

Try prompts like:

- "What are the call graph statistics?"
- "Search for functions containing 'add_message'"
- "Show details for add_message"
- "Which functions call add_message?"
