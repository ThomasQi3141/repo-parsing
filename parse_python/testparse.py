import tree_sitter_python as tspython
from tree_sitter import Language, Parser

def get_language():
    return Language(tspython.language())

def parse_file(file_path: str, parser: Parser):
    # Return both the parsed tree and the raw bytes
    with open(file_path, 'rb') as f:
        source_bytes = f.read()
    tree = parser.parse(source_bytes)
    return tree, source_bytes

def get_node_text(node, source_bytes):
    # start_byte/end_byte are the slice bounds
    return source_bytes[node.start_byte:node.end_byte].decode('utf8')

def print_tree(node, source_bytes, indent=0):
    text = get_node_text(node, source_bytes)
    print(
        '  ' * indent +
        f"{node.type} ({node.start_point[0]}:{node.start_point[1]}-"
        f"{node.end_point[0]}:{node.end_point[1]}) → {repr(text)}"
    )
    for child in node.children:
        print_tree(child, source_bytes, indent+1)
        
def print_tree_tokens(node, source_bytes, indent: int = 0):
    """Recursively print each node’s token (text), indented by depth."""
    text = get_node_text(node, source_bytes)
    print('  ' * indent + repr(text))
    for child in node.children:
        print_tree_tokens(child, source_bytes, indent + 1)
        
def main():
    parser = Parser(language=get_language())
    tree, source = parse_file('sampleFile.py', parser)
    # print_tree(tree.root_node, source)
    print_tree_tokens(tree.root_node, source)

if __name__ == "__main__":
    main()
