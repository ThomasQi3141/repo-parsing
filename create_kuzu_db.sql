-- KuzuDB Schema and Import Script
-- Run this with: ./kuzu_shell < create_kuzu_db.sql

-- Create the Node table
CREATE NODE TABLE Node(id STRING, label STRING, graph_id INT64, PRIMARY KEY (id));

-- Create the Edge table
CREATE REL TABLE Edge(FROM Node TO Node, graph_id INT64);

-- Import the CSV files
COPY Node FROM 'out/nodes.csv' (HEADER=true);
COPY Edge FROM 'out/edges.csv' (HEADER=true);

-- Verify the import
MATCH (n:Node) RETURN COUNT(*) AS node_count;
MATCH ()-[e:Edge]->() RETURN COUNT(*) AS edge_count;

-- Show some sample data
MATCH (n:Node) RETURN n.id, n.label, n.graph_id LIMIT 5;
MATCH (n1:Node)-[e:Edge]->(n2:Node) RETURN n1.id, n2.id, e.graph_id LIMIT 5; 