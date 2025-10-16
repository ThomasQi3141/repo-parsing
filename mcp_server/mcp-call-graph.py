import os
import csv
import json
import asyncio
import logging
from typing import Dict, List, Optional, Set
from collections import defaultdict

from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (never print to stdout in MCP stdio servers)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("call-graph-mcp")

mcp = FastMCP("call-graph-analyzer")

# Resolve default OUT directory (absolute path) to avoid CWD issues
DEFAULT_OUT_DIR = os.environ.get(
    "CALLGRAPH_OUT_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
)

# Global, lazily-initialized parser
_parser = None
_parser_lock = asyncio.Lock()


class CSVCallGraphParser:
    def __init__(self, out_dir: str):
        self.out_dir = out_dir
        self.methods_file = os.path.join(out_dir, "methods.csv")
        self.calls_file = os.path.join(out_dir, "calls.csv")

        # Data structures
        self.methods: Dict[str, Dict] = {}  # method_id -> row dict
        self.methods_by_name: Dict[str, List[str]] = defaultdict(list)  # func_name -> [method_id]
        self.calls: List[Dict] = []  # rows from calls.csv

        self._load_data()

    def _load_data(self) -> None:
        if not os.path.exists(self.methods_file) or not os.path.exists(self.calls_file):
            raise FileNotFoundError(
                f"Missing CSV files in '{self.out_dir}'. "
                f"Expected methods.csv and calls.csv"
            )

        # Load methods.csv
        with open(self.methods_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                method_id = row["method_id"]
                self.methods[method_id] = row

                full_name = row["full_name"]
                func_name = self._extract_function_name(full_name)
                self.methods_by_name[func_name].append(method_id)

        logger.info("Loaded %d methods from %s", len(self.methods), self.methods_file)

        # Load calls.csv
        with open(self.calls_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.calls.append(row)

        logger.info("Loaded %d calls from %s", len(self.calls), self.calls_file)

    @staticmethod
    def _extract_function_name(full_name: str) -> str:
        # formats like "path/file.py:<module>.Class.method" or "path/file.py:func"
        if ":" in full_name:
            last = full_name.split(":")[-1]
            if "." in last:
                return last.split(".")[-1]
            return last
        return full_name

    def get_callers(self, function_name: str) -> List[str]:
        callers: Set[str] = set()
        method_ids = self.methods_by_name.get(function_name, [])
        if not method_ids:
            return []

        for call in self.calls:
            callee_id = call["callee_id"]
            if callee_id in method_ids:
                caller_id = call["caller_id"]
                if caller_id in self.methods:
                    callers.add(self.methods[caller_id]["full_name"])
        return sorted(callers)

    def get_callees(self, function_name: str) -> List[str]:
        callees: Set[str] = set()
        method_ids = self.methods_by_name.get(function_name, [])
        if not method_ids:
            return []

        for call in self.calls:
            caller_id = call["caller_id"]
            if caller_id in method_ids:
                callee_id = call["callee_id"]
                if callee_id != "-1" and callee_id in self.methods:
                    callees.add(self.methods[callee_id]["full_name"])
                else:
                    callee_full = call.get("callee_full_name")
                    if callee_full and callee_full != "<unknownFullName>":
                        callees.add(callee_full)
        return sorted(callees)

    def get_function_details(self, function_name: str) -> Optional[Dict]:
        method_ids = self.methods_by_name.get(function_name, [])
        if not method_ids:
            return None
        method_id = method_ids[0]
        method = self.methods[method_id]
        return {
            "method_id": method_id,
            "full_name": method["full_name"],
            "signature": method.get("signature", ""),
            "file": method.get("file", ""),
        }

    def search_functions(self, query: str) -> List[str]:
        q = query.lower()
        return sorted([name for name in self.methods_by_name.keys() if q in name.lower()])

    def get_stats(self) -> Dict:
        return {
            "total_methods": len(self.methods),
            "total_calls": len(self.calls),
            "unique_functions": len(self.methods_by_name),
            "methods_file": self.methods_file,
            "calls_file": self.calls_file,
            "methods_loaded": os.path.exists(self.methods_file),
            "calls_loaded": os.path.exists(self.calls_file),
        }


async def _ensure_parser_loaded() -> CSVCallGraphParser:
    global _parser
    if _parser is not None:
        return _parser
    async with _parser_lock:
        if _parser is None:
            out_dir = DEFAULT_OUT_DIR
            logger.info("Initializing CSV parser with data from %s", out_dir)
            _parser = CSVCallGraphParser(out_dir)
            logger.info("CSV parser initialized")
        return _parser


def _json(data: Dict) -> str:
    return json.dumps(data, indent=2)


# -------- MCP Tools (FastMCP) --------

@mcp.tool()
async def get_callees(function: str) -> str:
    """Get all functions that the given function calls."""
    try:
        parser = await _ensure_parser_loaded()
        results = parser.get_callees(function)
        return _json({"function": function, "callees": results, "count": len(results), "success": True})
    except Exception as e:
        logger.exception("get_callees error")
        return _json({"function": function, "callees": [], "success": False, "error": str(e)})


@mcp.tool()
async def get_callers(function: str) -> str:
    """Get all functions that call the given function."""
    try:
        parser = await _ensure_parser_loaded()
        results = parser.get_callers(function)
        return _json({"function": function, "callers": results, "count": len(results), "success": True})
    except Exception as e:
        logger.exception("get_callers error")
        return _json({"function": function, "callers": [], "success": False, "error": str(e)})


@mcp.tool()
async def get_function_details(function: str) -> str:
    """Get detailed information about a function (file, signature, etc.)."""
    try:
        parser = await _ensure_parser_loaded()
        details = parser.get_function_details(function)
        if details:
            return _json({"function": function, "details": details, "success": True})
        return _json({"function": function, "details": None, "success": False, "error": "Function not found"})
    except Exception as e:
        logger.exception("get_function_details error")
        return _json({"function": function, "details": None, "success": False, "error": str(e)})


@mcp.tool()
async def search_functions(query: str) -> str:
    """Search for functions by name pattern."""
    try:
        parser = await _ensure_parser_loaded()
        results = parser.search_functions(query)
        return _json({"query": query, "results": results, "count": len(results), "success": True})
    except Exception as e:
        logger.exception("search_functions error")
        return _json({"query": query, "results": [], "success": False, "error": str(e)})


@mcp.tool()
async def get_call_graph_stats() -> str:
    """Get statistics about the loaded call graph data."""
    try:
        parser = await _ensure_parser_loaded()
        stats = parser.get_stats()
        stats["success"] = True
        return _json(stats)
    except Exception as e:
        logger.exception("get_call_graph_stats error")
        return _json({"success": False, "error": str(e)})


if __name__ == "__main__":
    mcp.run(transport="stdio")