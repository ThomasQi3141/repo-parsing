#!/usr/bin/env python3

"""
Simple Python Call Graph Analyzer
This script reads Python source code directly to find actual function calls
"""

import os
import re
import ast
import json
from collections import defaultdict
from pathlib import Path

def find_python_files(directory):
    """Find all Python files in a directory recursively"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def extract_function_calls_from_source(file_path):
    """Extract function calls from Python source code using AST"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        # Get all function definitions
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'code': ast.unparse(node) if hasattr(ast, 'unparse') else source.split('\n')[node.lineno-1:node.end_lineno]
                })
        
        # Get all function calls
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append({
                        'function_name': node.func.id,
                        'line': node.lineno,
                        'context': 'direct_call'
                    })
                elif isinstance(node.func, ast.Attribute):
                    calls.append({
                        'function_name': node.func.attr,
                        'line': node.lineno,
                        'context': 'method_call',
                        'object': ast.unparse(node.func.value) if hasattr(ast, 'unparse') else 'unknown'
                    })
        
        return functions, calls
        
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return [], []

def build_call_graph_from_source(repo_path):
    """Build call graph by analyzing Python source code directly"""
    
    python_files = find_python_files(repo_path)
    print(f"Found {len(python_files)} Python files")
    
    all_functions = {}
    all_calls = []
    
    # Process each Python file
    for file_path in python_files:
        # Convert to relative path for display
        rel_path = os.path.relpath(file_path, repo_path)
        
        functions, calls = extract_function_calls_from_source(file_path)
        
        # Store functions with full identifier
        for func in functions:
            func_id = f"{rel_path}:{func['name']}"
            all_functions[func_id] = {
                'file': rel_path,
                'function': func['name'],
                'line': func['line'],
                'code': func['code']
            }
        
        # Store calls with file context
        for call in calls:
            call['file'] = rel_path
            all_calls.append(call)
    
    # Build call graph
    call_graph = defaultdict(list)
    called_by = defaultdict(list)
    
    # For each call, try to find the caller function
    for call in all_calls:
        call_file = call['file']
        callee_name = call['function_name']
        
        # Find the function that contains this call
        caller_func = None
        for func_id, func_info in all_functions.items():
            if func_info['file'] == call_file:
                # Check if this call is within the function's line range
                # This is a simplified approach - in practice you'd need more sophisticated analysis
                if func_info['line'] <= call['line']:
                    caller_func = func_id
                    break
        
        if caller_func:
            # Try to find the callee function
            callee_func = None
            for func_id, func_info in all_functions.items():
                if func_info['function'] == callee_name:
                    callee_func = func_id
                    break
            
            if callee_func:
                call_graph[caller_func].append(callee_func)
                called_by[callee_func].append(caller_func)
            else:
                # External function call
                external_callee = f"external:{callee_name}"
                call_graph[caller_func].append(external_callee)
                called_by[external_callee].append(caller_func)
    
    return all_functions, dict(call_graph), dict(called_by)

def generate_llm_index_from_source():
    """Generate LLM-friendly index from source code analysis"""
    
    repo_path = "../repos/test_repo"
    
    if not os.path.exists(repo_path):
        print(f"Repository not found: {repo_path}")
        return
    
    print("🔍 Analyzing Python source code for function calls...")
    
    # Build call graph from source
    functions, call_graph, called_by = build_call_graph_from_source(repo_path)
    
    print(f"✅ Found {len(functions)} functions")
    print(f"✅ Built call graph with {len(call_graph)} callers")
    
    # Generate output
    output_data = {
        "function_details": functions,
        "call_graphs": {"source_analysis": call_graph},
        "called_by": called_by
    }
    
    # Write JSON output
    output_file = "../out/llm_index_from_source.json"
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    
    # Generate text output
    text_output = []
    text_output.append("# Function Call Graph Analysis (from Source Code)")
    text_output.append("")
    
    # Function details
    text_output.append("## Function Details")
    for func_id, details in functions.items():
        text_output.append(f"### {func_id}")
        text_output.append(f"- File: {details['file']}")
        text_output.append(f"- Function: {details['function']}")
        text_output.append(f"- Line: {details['line']}")
        if isinstance(details['code'], list):
            text_output.append(f"- Code: {''.join(details['code'])}")
        else:
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
        if callers:
            text_output.append(f"- **{callee}** is called by:")
            for caller in callers:
                text_output.append(f"  - {caller}")
            text_output.append("")
    
    # Write text output
    text_file = "../out/llm_index_from_source.txt"
    with open(text_file, "w") as f:
        f.write("\n".join(text_output))
    
    print(f"✅ Generated source-based LLM index:")
    print(f"  - JSON: {output_file}")
    print(f"  - Text: {text_file}")
    print(f"  - Total functions: {len(functions)}")
    print(f"  - Total call relationships: {sum(len(callees) for callees in call_graph.values())}")

if __name__ == "__main__":
    generate_llm_index_from_source()
