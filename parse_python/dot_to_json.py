import os
import re
import json

out_dir = os.path.join(os.path.dirname(__file__), '..', 'out')
graphs = []

def clean_label(label):
    """Clean up HTML entities and formatting in labels"""
    label = re.sub(r'<BR/>', ' ', label)
    label = re.sub(r'&lt;', '<', label)
    label = re.sub(r'&gt;', '>', label)
    label = re.sub(r'&quot;', '"', label)
    return label

def parse_node_label(label):
    """Parse node label to extract line number, operation type, and code snippet"""
    # Pattern: <operation_type, line_number<BR/>code_snippet>
    # Example: <&lt;operator&gt;.assignment, 5<BR/>__version__ = &quot;0.1.0&quot;>
    
    # Extract operation type and line number
    op_match = re.match(r'&lt;([^&]+)&gt;\.([^,]+),\s*(\d+)', label)
    if op_match:
        op_type = op_match.group(1) + "." + op_match.group(2)
        line_num = int(op_match.group(3))
        
        # Extract code snippet (everything after <BR/>)
        snippet_match = re.search(r'<BR/>(.*)', label)
        if snippet_match:
            snippet = clean_label(snippet_match.group(1))
        else:
            snippet = ""
            
        return {
            "operation_type": op_type,
            "line": line_num,
            "snippet": snippet
        }
    
    # Handle special cases like METHOD, METHOD_RETURN, etc.
    special_match = re.match(r'([A-Z_]+),\s*(\d+)<BR/>(.*)', label)
    if special_match:
        op_type = special_match.group(1)
        line_num = int(special_match.group(2))
        snippet = clean_label(special_match.group(3))
        
        return {
            "operation_type": op_type,
            "line": line_num,
            "snippet": snippet
        }
    
    # Fallback for other patterns
    return {
        "operation_type": "unknown",
        "line": 0,
        "snippet": clean_label(label)
    }

def parse_dot_file(filepath):
    """Parse a .dot file and return a graph dictionary"""
    nodes = []
    edges = []
    
    with open(filepath) as f:
        for line in f:
            # Node: "30064771072" [label = <...>]
            m = re.match(r'\s*"([^"]+)"\s*\[label\s*=\s*<(.*?)>\s*\]', line)
            if m:
                node_id, label = m.groups()
                node_info = parse_node_label(label)
                
                nodes.append({
                    "id": node_id,
                    "operation_type": node_info["operation_type"],
                    "line": node_info["line"],
                    "snippet": node_info["snippet"]
                })
            
            # Edge: "30064771072" -> "128849018880"
            m = re.match(r'\s*"([^"]+)" -> "([^"]+)"', line)
            if m:
                src, tgt = m.groups()
                edges.append([src, tgt])
    
    return {
        "nodes": nodes,
        "edges": edges
    }

# Parse all .dot files in the out directory
for fname in os.listdir(out_dir):
    if fname.endswith(".dot"):
        try:
            # Extract graph name from filename (e.g., "0-cfg.dot" -> "0-cfg")
            graph_name = fname.replace(".dot", "")
            filepath = os.path.join(out_dir, fname)
            
            graph_data = parse_dot_file(filepath)
            graph_data["name"] = graph_name
            
            graphs.append(graph_data)
            
        except Exception as e:
            print(f"Error parsing {fname}: {e}")

# Write to JSON file
output_file = os.path.join(out_dir, "graphs.json")
with open(output_file, "w") as f:
    json.dump(graphs, f, indent=2)

print(f"Exported {len(graphs)} graphs to {output_file}")
print(f"Total nodes: {sum(len(g['nodes']) for g in graphs)}")
print(f"Total edges: {sum(len(g['edges']) for g in graphs)}")

# Print a sample node for verification
if graphs and graphs[0]['nodes']:
    sample_node = graphs[0]['nodes'][0]
    print(f"\nSample node: {sample_node}") 