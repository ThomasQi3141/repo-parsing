import os
import re
import csv

out_dir = os.path.join(os.path.dirname(__file__), '..', 'out')
node_rows = []
edge_rows = []

def parse_dot_file(filepath, graph_id):
    with open(filepath) as f:
        for line in f:
            # Node:  1 [label="entry"];
            m = re.match(r'\s*(\d+) \[label="([^"]+)"\];', line)
            if m:
                node_id, label = m.groups()
                node_rows.append([int(node_id), label, graph_id])
            # Edge:  1 -> 2;
            m = re.match(r'\s*(\d+) -> (\d+);', line)
            if m:
                src, tgt = m.groups()
                edge_rows.append([int(src), int(tgt), graph_id])

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

print("Exported nodes.csv and edges.csv for KuzuDB import in the 'out/' directory.") 