import os
import re
import csv

out_dir = os.path.join(os.path.dirname(__file__), '..', 'out')
node_rows = []
edge_rows = []

def parse_dot_file(filepath, graph_id):
    with open(filepath) as f:
        for line in f:
            # Node: "30064771072" [label = <...>]
            m = re.match(r'\s*"([^"]+)"\s*\[label\s*=\s*<(.*?)>\s*\]', line)
            if m:
                node_id, label = m.groups()
                # Clean up the label - remove HTML tags and decode entities
                label = re.sub(r'<BR/>', ' ', label)
                label = re.sub(r'&lt;', '<', label)
                label = re.sub(r'&gt;', '>', label)
                label = re.sub(r'&quot;', '"', label)
                node_rows.append([node_id, label, graph_id])
            
            # Edge: "30064771072" -> "128849018880"
            m = re.match(r'\s*"([^"]+)" -> "([^"]+)"', line)
            if m:
                src, tgt = m.groups()
                edge_rows.append([src, tgt, graph_id])

for fname in os.listdir(out_dir):
    if fname.endswith("-cfg.dot"):
        try:
            graph_id = int(fname.split("-")[0])
        except Exception:
            continue
        parse_dot_file(os.path.join(out_dir, fname), graph_id)

with open(os.path.join(out_dir, "nodes.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "label", "graph_id"])
    writer.writerows(node_rows)

with open(os.path.join(out_dir, "edges.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["source", "target", "graph_id"])
    writer.writerows(edge_rows)

print(f"Exported {len(node_rows)} nodes and {len(edge_rows)} edges to nodes.csv and edges.csv for KuzuDB import in the 'out/' directory.") 