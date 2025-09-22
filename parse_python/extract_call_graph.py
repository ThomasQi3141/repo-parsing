#!/usr/bin/env python3

"""
Extract actual function call relationships from Joern CPG
This script queries the CPG directly instead of parsing CFG files
"""

import os
import json
import subprocess
from collections import defaultdict

def extract_call_graph_from_cpg(cpg_path):
    """
    Extract call graph from Joern CPG using CPGQL queries
    """
    
    # Create a temporary script to query the CPG
    script_content = f'''
importCpg("{cpg_path}")

// Get all method definitions with their file information
val methods = cpg.method.nameNot("<global>").map {{ m =>
  Map(
    "id" -> m.id.toString,
    "name" -> m.name,
    "fullName" -> m.fullName,
    "filename" -> m.filename,
    "lineNumber" -> m.lineNumber.getOrElse(0),
    "code" -> m.code
  )
}}.toList

// Get all call relationships
val calls = cpg.call.map {{ c =>
  Map(
    "callerId" -> c.method.id.toString,
    "callerName" -> c.method.name,
    "callerFile" -> c.method.filename,
    "callerLine" -> c.method.lineNumber.getOrElse(0),
    "calleeName" -> c.name,
    "calleeCode" -> c.code,
    "lineNumber" -> c.lineNumber.getOrElse(0)
  )
}}.toList

// Output results
println("=== METHODS ===")
methods.foreach {{ m =>
  println(s"METHOD: ${{m("id")}}|${{m("name")}}|${{m("fullName")}}|${{m("filename")}}|${{m("lineNumber")}}|${{m("code")}}")
}}

println("=== CALLS ===")
calls.foreach {{ c =>
  println(s"CALL: ${{c("callerId")}}|${{c("callerName")}}|${{c("callerFile")}}|${{c("callerLine")}}|${{c("calleeName")}}|${{c("calleeCode")}}|${{c("lineNumber")}}")
}}
'''
    
    # Write the script to a temporary file
    script_file = "temp_cpg_query.sc"
    with open(script_file, "w") as f:
        f.write(script_content)
    
    try:
        # Run the script with Joern
        result = subprocess.run(
            ["joern", "--script", script_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"Error running Joern script: {result.stderr}")
            return None
        
        return result.stdout
        
    finally:
        # Clean up
        if os.path.exists(script_file):
            os.remove(script_file)

def parse_cpg_output(output):
    """
    Parse the output from the CPG query
    """
    methods = {}
    calls = []
    method_refs = {}
    
    lines = output.strip().split('\n')
    
    for line in lines:
        if line.startswith("METHOD: "):
            parts = line[8:].split('|')
            if len(parts) >= 6:
                method_id = parts[0]
                methods[method_id] = {
                    "name": parts[1],
                    "fullName": parts[2],
                    "filename": parts[3],
                    "lineNumber": int(parts[4]) if parts[4].isdigit() else 0,
                    "code": parts[5]
                }
        
        elif line.startswith("CALL: "):
            parts = line[7:].split('|')
            if len(parts) >= 7:
                calls.append({
                    "callerId": parts[0],
                    "callerName": parts[1],
                    "callerFile": parts[2],
                    "callerLine": int(parts[3]) if parts[3].isdigit() else 0,
                    "calleeName": parts[4],
                    "calleeCode": parts[5],
                    "lineNumber": int(parts[6]) if parts[6].isdigit() else 0
                })
        
        elif line.startswith("METHOD_REF: "):
            parts = line[12:].split('|')
            if len(parts) >= 4:
                method_ref_id = parts[0]
                method_refs[method_ref_id] = {
                    "name": parts[1],
                    "code": parts[2],
                    "lineNumber": int(parts[3]) if parts[3].isdigit() else 0
                }
    
    return methods, calls, method_refs

def build_call_graph(methods, calls, method_refs):
    """
    Build the actual call graph from the parsed data
    """
    call_graph = defaultdict(list)
    called_by = defaultdict(list)
    
    # Process each call
    for call in calls:
        caller_id = call["callerId"]
        callee_name = call["calleeName"]
        
        # Get caller information
        if caller_id in methods:
            caller_info = methods[caller_id]
            caller_file = caller_info["filename"]
            caller_name = caller_info["name"]
            
            # Create full function identifier
            caller_full = f"{caller_file}:{caller_name}"
            
            # Try to find the callee in methods
            callee_full = None
            
            # Look for exact name match in methods
            for method_id, method_info in methods.items():
                if method_info["name"] == callee_name:
                    callee_full = f"{method_info['filename']}:{method_info['name']}"
                    break
            
            # If not found in methods, it might be a built-in or external function
            if not callee_full:
                # For now, we'll use the callee name as is
                # In a real implementation, you might want to map these to their actual locations
                callee_full = f"builtin:{callee_name}"
            
            # Add to call graph
            call_graph[caller_full].append(callee_full)
            called_by[callee_full].append(caller_full)
        else:
            print(f"Debug: Caller ID {caller_id} not found in methods")
            if len(calls) <= 5:  # Only print first few for debugging
                print(f"  Call: {call}")
    
    print(f"Debug: Processed {len(calls)} calls")
    print(f"Debug: Found {len(call_graph)} callers in call graph")
    print(f"Debug: Found {len(called_by)} callees in called_by")
    print(f"Debug: Method IDs: {list(methods.keys())[:5]}")  # Show first few method IDs
    print(f"Debug: Caller IDs: {[c['callerId'] for c in calls[:5]]}")  # Show first few caller IDs
    
    return dict(call_graph), dict(called_by)

def generate_llm_index_from_cpg():
    """
    Generate LLM-friendly index from CPG call graph data
    """
    # Path to the CPG file
    cpg_path = "../workspace/test_repo1/cpg.bin"
    
    if not os.path.exists(cpg_path):
        print(f"CPG file not found: {cpg_path}")
        return
    
    print("🔍 Extracting call graph from CPG...")
    
    # Extract data from CPG
    output = extract_call_graph_from_cpg(cpg_path)
    if not output:
        print("❌ Failed to extract data from CPG")
        return
    
    print("📊 Parsing CPG output...")
    
    # Parse the output
    methods, calls, method_refs = parse_cpg_output(output)
    
    print(f"✅ Found {len(methods)} methods, {len(calls)} calls, {len(method_refs)} method references")
    
    # Build call graph
    call_graph, called_by = build_call_graph(methods, calls, method_refs)
    
    print(f"✅ Built call graph with {len(call_graph)} callers and {len(called_by)} callees")
    
    # Create function details
    function_details = {}
    for method_id, method_info in methods.items():
        full_func_id = f"{method_info['filename']}:{method_info['name']}"
        function_details[full_func_id] = {
            "line": method_info["lineNumber"],
            "code": method_info["code"],
            "fullName": method_info["fullName"],
            "filename": method_info["filename"],
            "function_name": method_info["name"]
        }
    
    # Generate output
    output_data = {
        "function_details": function_details,
        "call_graphs": {"cpg_call_graph": call_graph},
        "called_by": called_by
    }
    
    # Write JSON output
    output_file = "../out/llm_index_from_cpg.json"
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    
    # Generate text output
    text_output = []
    text_output.append("# Function Call Graph Analysis (from CPG)")
    text_output.append("")
    
    # Function details
    text_output.append("## Function Details")
    for func_id, details in function_details.items():
        text_output.append(f"### {func_id}")
        text_output.append(f"- File: {details['filename']}")
        text_output.append(f"- Function: {details['function_name']}")
        text_output.append(f"- Line: {details['line']}")
        text_output.append(f"- Code: {details['code']}")
        text_output.append("")
    
    # Call relationships
    text_output.append("## Function Call Relationships")
    for caller, callees in call_graph.items():
        if callees:
            text_output.append(f"- **{caller}** calls:")
            for callee in callees:
                text_output.append(f"  - {callee}")
            text_output.append("")
    
    # Called by relationships
    text_output.append("## Function Called By Relationships")
    for callee, callers in called_by.items():
        if callees:
            text_output.append(f"- **{callee}** is called by:")
            for caller in callers:
                text_output.append(f"  - {caller}")
            text_output.append("")
    
    # Write text output
    text_file = "../out/llm_index_from_cpg.txt"
    with open(text_file, "w") as f:
        f.write("\n".join(text_output))
    
    print(f"✅ Generated CPG-based LLM index:")
    print(f"  - JSON: {output_file}")
    print(f"  - Text: {text_file}")
    print(f"  - Total functions: {len(function_details)}")
    print(f"  - Total call relationships: {sum(len(callees) for callees in call_graph.values())}")

if __name__ == "__main__":
    generate_llm_index_from_cpg()
