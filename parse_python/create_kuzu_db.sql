-- KuzuDB schema and import script for CFG
-- Run this in the KuzuDB CLI or via Python API

CREATE TABLE Nodes(id INT, label STRING, graph_id INT, PRIMARY KEY(id, graph_id));
CREATE TABLE Edges(source INT, target INT, graph_id INT);

COPY Nodes FROM '../out/nodes.csv' (HEADER=TRUE);
COPY Edges FROM '../out/edges.csv' (HEADER=TRUE); 