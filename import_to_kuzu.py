#!/usr/bin/env python3
"""
Script to import CSV files into KuzuDB
"""

import subprocess
import os
import sys

def run_kuzu_import():
    """Run the KuzuDB import process"""
    
    # Check if CSV files exist
    nodes_csv = "out/nodes.csv"
    edges_csv = "out/edges.csv"
    
    if not os.path.exists(nodes_csv):
        print(f"Error: {nodes_csv} not found!")
        return False
    
    if not os.path.exists(edges_csv):
        print(f"Error: {edges_csv} not found!")
        return False
    
    # Check if KuzuDB binary exists
    kuzu_binary = "./kuzu_shell"
    if not os.path.exists(kuzu_binary):
        print(f"Error: {kuzu_binary} not found!")
        print("Please download KuzuDB from: https://github.com/kuzudb/kuzu/releases")
        return False
    
    # Create database directory
    db_dir = "kuzu_db"
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"Created database directory: {db_dir}")
    
    # SQL commands to run
    sql_commands = [
        "CREATE NODE TABLE Node(id STRING, label STRING, graph_id INT64, PRIMARY KEY (id));",
        "CREATE REL TABLE Edge(FROM Node TO Node, graph_id INT64);",
        f"COPY Node FROM '{nodes_csv}' (HEADER=true);",
        f"COPY Edge FROM '{edges_csv}' (HEADER=true);",
        "MATCH (n:Node) RETURN COUNT(*) AS node_count;",
        "MATCH ()-[e:Edge]->() RETURN COUNT(*) AS edge_count;",
        "MATCH (n:Node) RETURN n.id, n.label, n.graph_id LIMIT 3;",
        "MATCH (n1:Node)-[e:Edge]->(n2:Node) RETURN n1.id, n2.id, e.graph_id LIMIT 3;",
        ".quit"
    ]
    
    # Write SQL commands to a temporary file
    with open("temp_import.sql", "w") as f:
        for cmd in sql_commands:
            f.write(cmd + "\n")
    
    try:
        # Run KuzuDB with the SQL file
        print("Starting KuzuDB import...")
        result = subprocess.run([kuzu_binary, db_dir], 
                              input=open("temp_import.sql").read(),
                              text=True, 
                              capture_output=True)
        
        if result.returncode == 0:
            print("✅ Import successful!")
            print("\nOutput:")
            print(result.stdout)
        else:
            print("❌ Import failed!")
            print("Error output:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running KuzuDB: {e}")
        return False
    finally:
        # Clean up temporary file
        if os.path.exists("temp_import.sql"):
            os.remove("temp_import.sql")
    
    return True

if __name__ == "__main__":
    print("🚀 KuzuDB CSV Import Script")
    print("=" * 40)
    
    success = run_kuzu_import()
    
    if success:
        print("\n🎉 Import completed successfully!")
        print("You can now query your graph with:")
        print("  ./kuzu_shell kuzu_db")
    else:
        print("\n💥 Import failed. Please check the errors above.")
        sys.exit(1) 