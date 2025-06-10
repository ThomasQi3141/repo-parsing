import tree_sitter_python as tspython
from tree_sitter import Language, Parser
import os
from pathlib import Path

def get_language():
    """Get the Python language parser."""
    # Try to load the language from the default location
    PY_LANGUAGE = Language(tspython.language())
    return PY_LANGUAGE

def parse_file(file_path: str, parser: Parser):
    """Parse a Python file and return its syntax tree."""
    with open(file_path, 'rb') as f:
        source_code = f.read()
    return parser.parse(source_code)

def print_tree(node, indent: int = 0):
    """Print the syntax tree in a readable format."""
    print('  ' * indent + f'{node.type} ({node.start_point[0]}:{node.start_point[1]}-{node.end_point[0]}:{node.end_point[1]})')
    for child in node.children:
        print_tree(child, indent + 1)

def main():
    # Initialize parser with language
    parser = Parser(language=get_language())
    
    # Parse sampleFile.py
    file_path = 'sampleFile.py'
    print(f"\nParsing {file_path}:")
    print("-" * 50)
    
    try:
        tree = parse_file(file_path, parser)
        print_tree(tree.root_node)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

if __name__ == "__main__":
    main()