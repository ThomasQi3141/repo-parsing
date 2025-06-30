import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
import json
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript

class CallGraphAnalyzer:
    def __init__(self):
        # Initialize parsers for both languages
        self.python_parser = Parser(language=Language(tspython.language()))
        self.js_parser = Parser(language=Language(tsjavascript.language()))
        
        # Store call graphs
        self.python_call_graph: Dict[str, Dict[str, List[str]]] = {}
        self.js_call_graph: Dict[str, Dict[str, List[str]]] = {}
        
        # Store function definitions with their paths
        self.python_functions: Dict[str, str] = {}  # function_name -> file_path
        self.js_functions: Dict[str, str] = {}      # function_name -> file_path

    def get_node_text(self, node, source_bytes: bytes) -> str:
        """Get the text content of a node."""
        return source_bytes[node.start_byte:node.end_byte].decode('utf8')

    def find_python_functions(self, node, source_bytes: bytes, file_path: str, current_class: str = None):
        """Find all function definitions in Python code."""
        if node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                func_name = self.get_node_text(name_node, source_bytes)
                # Create full path: file:class.function or file:function
                func_path = f"{file_path}:{current_class + '.' if current_class else ''}{func_name}"
                self.python_functions[func_name] = func_path
                self.python_call_graph[func_path] = {
                    'called_by': [],
                    'calls': []
                }
        
        elif node.type == 'class_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                current_class = self.get_node_text(name_node, source_bytes)
        
        for child in node.children:
            self.find_python_functions(child, source_bytes, file_path, current_class)

    def find_js_functions(self, node, source_bytes: bytes, file_path: str, current_class: str = None):
        """Find all function definitions in JavaScript code."""
        if node.type in ['function_declaration', 'method_definition']:
            name_node = node.child_by_field_name('name')
            if name_node:
                func_name = self.get_node_text(name_node, source_bytes)
                # Create full path: file:class.function or file:function
                func_path = f"{file_path}:{current_class + '.' if current_class else ''}{func_name}"
                self.js_functions[func_name] = func_path
                self.js_call_graph[func_path] = {
                    'called_by': [],
                    'calls': []
                }
        
        elif node.type == 'class_declaration':
            name_node = node.child_by_field_name('name')
            if name_node:
                current_class = self.get_node_text(name_node, source_bytes)
        
        for child in node.children:
            self.find_js_functions(child, source_bytes, file_path, current_class)

    def find_python_calls(self, node, source_bytes: bytes, current_function: str):
        """Find all function calls in Python code."""
        if node.type == 'call':
            name_node = node.child_by_field_name('function')
            if name_node:
                called_func = self.get_node_text(name_node, source_bytes)
                if called_func in self.python_functions:
                    called_path = self.python_functions[called_func]
                    # Add to call graph
                    self.python_call_graph[current_function]['calls'].append(called_path)
                    self.python_call_graph[called_path]['called_by'].append(current_function)
        
        for child in node.children:
            self.find_python_calls(child, source_bytes, current_function)

    def find_js_calls(self, node, source_bytes: bytes, current_function: str):
        """Find all function calls in JavaScript code."""
        if node.type == 'call_expression':
            name_node = node.child_by_field_name('function')
            if name_node:
                called_func = self.get_node_text(name_node, source_bytes)
                if called_func in self.js_functions:
                    called_path = self.js_functions[called_func]
                    # Add to call graph
                    self.js_call_graph[current_function]['calls'].append(called_path)
                    self.js_call_graph[called_path]['called_by'].append(current_function)
        
        for child in node.children:
            self.find_js_calls(child, source_bytes, current_function)

    def analyze_file(self, file_path: str):
        """Analyze a single file and update the call graph."""
        with open(file_path, 'rb') as f:
            source_bytes = f.read()
        
        if file_path.endswith('.py'):
            tree = self.python_parser.parse(source_bytes)
            self.find_python_functions(tree.root_node, source_bytes, file_path)
            # Second pass to find calls
            for func_path in self.python_call_graph:
                self.find_python_calls(tree.root_node, source_bytes, func_path)
        
        elif file_path.endswith('.js'):
            tree = self.js_parser.parse(source_bytes)
            self.find_js_functions(tree.root_node, source_bytes, file_path)
            # Second pass to find calls
            for func_path in self.js_call_graph:
                self.find_js_calls(tree.root_node, source_bytes, func_path)

    def analyze_directory(self, directory: str):
        """Analyze all Python and JavaScript files in a directory."""
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.py', '.js')):
                    file_path = os.path.join(root, file)
                    self.analyze_file(file_path)

    def get_call_graph(self) -> Dict:
        """Get the complete call graph."""
        return {
            'python': self.python_call_graph,
            'javascript': self.js_call_graph
        }

    def save_call_graph(self, output_file: str):
        """Save the call graph to a JSON file."""
        with open(output_file, 'w') as f:
            json.dump(self.get_call_graph(), f, indent=2)

def main():
    print("Initializing call graph analyzer...")
    analyzer = CallGraphAnalyzer()
    
    # Analyze the test_repo directory
    target_dir = 'test_repo'
    print(f"\nAnalyzing directory: {target_dir}")
    print("-" * 50)
    
    # First, find all Python files
    python_files = []
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files")
    
    # Analyze each file
    for i, file_path in enumerate(python_files, 1):
        print(f"\nAnalyzing file {i}/{len(python_files)}: {file_path}")
        try:
            analyzer.analyze_file(file_path)
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    # Save the call graph
    output_file = 'test_repo_call_graph.json'
    print(f"\nSaving call graph to {output_file}")
    analyzer.save_call_graph(output_file)
    
    # Print statistics
    print("\nCall Graph Statistics:")
    print("-" * 50)
    print(f"Python functions found: {len(analyzer.python_call_graph)}")
    
    # Print function relationships
    print("\nFunction Relationships:")
    print("-" * 50)
    for func_path, relationships in analyzer.python_call_graph.items():
        if relationships['called_by'] or relationships['calls']:
            print(f"\nFunction: {func_path}")
            if relationships['called_by']:
                print(f"Called by: {relationships['called_by']}")
            if relationships['calls']:
                print(f"Calls: {relationships['calls']}")

if __name__ == "__main__":
    main() 