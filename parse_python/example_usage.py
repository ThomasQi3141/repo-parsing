#!/usr/bin/env python3

"""
Example usage of SWEbench experiment with graph enhancement.

This script demonstrates how to:
1. Run the complete experiment pipeline
2. Use a specific SWEbench repository
3. Compare results with and without graph information
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Example usage of the SWEbench experiment"""
    
    # Example configuration
    config = {
        "repo_path": "repos/pylint",  # Path to the repository to analyze
        "dataset_path": "path/to/swebench/dataset",  # SWEbench dataset path
        "model": "gpt-4",  # LLM model to use
        "output_dir": "experiment_results",  # Output directory
        "max_cost": 50.0  # Maximum cost limit
    }
    
    print("SWEbench Experiment with Graph Enhancement")
    print("=" * 50)
    print()
    print("This example shows how to run the complete experiment pipeline:")
    print("1. Parse repository with Joern to extract CFG and call graphs")
    print("2. Generate LLM-friendly graph index")
    print("3. Run SWEbench baseline (without graphs)")
    print("4. Run SWEbench with graph enhancement")
    print("5. Compare results")
    print()
    
    # Check if required files exist
    script_path = os.path.join(os.path.dirname(__file__), 'run_swebench_experiment.py')
    if not os.path.exists(script_path):
        print(f"Error: Experiment script not found at {script_path}")
        return 1
    
    # Example command
    cmd = [
        sys.executable, script_path,
        "--repo-path", config["repo_path"],
        "--dataset-path", config["dataset_path"],
        "--model", config["model"],
        "--output-dir", config["output_dir"],
        "--max-cost", str(config["max_cost"])
    ]
    
    print("Example command:")
    print(" ".join(cmd))
    print()
    
    # Check if repository exists
    if not os.path.exists(config["repo_path"]):
        print(f"Warning: Repository path {config['repo_path']} does not exist.")
        print("You need to:")
        print("1. Clone a repository to analyze")
        print("2. Update the repo_path in this script")
        print()
        print("Example:")
        print("git clone https://github.com/pylint-dev/pylint.git repos/pylint")
        print()
    
    # Check if SWEbench dataset exists
    if not os.path.exists(config["dataset_path"]):
        print(f"Warning: Dataset path {config['dataset_path']} does not exist.")
        print("You need to:")
        print("1. Download a SWEbench dataset")
        print("2. Update the dataset_path in this script")
        print()
        print("Example SWEbench datasets:")
        print("- SWE-bench: https://huggingface.co/datasets/princeton-nlp/SWE-bench")
        print("- SWE-bench_lite: https://huggingface.co/datasets/princeton-nlp/SWE-bench_lite")
        print()
    
    print("To run the experiment:")
    print("1. Update the configuration above")
    print("2. Run: python3 example_usage.py")
    print("3. Check results in the output directory")
    print()
    
    print("Alternative: Run individual steps manually")
    print("=" * 50)
    print()
    
    # Step 1: Parse repository
    print("Step 1: Parse repository with Joern")
    print("python3 dot_to_llm_index.py")
    print()
    
    # Step 2: Generate graph index
    print("Step 2: Generate graph index")
    print("python3 dot_to_llm_index.py")
    print()
    
    # Step 3: Run SWEbench with graphs
    print("Step 3: Run SWEbench with graph enhancement")
    print("python3 swebench_with_graphs.py \\")
    print("  --dataset path/to/dataset \\")
    print("  --model gpt-4 \\")
    print("  --output-dir results_with_graphs \\")
    print("  --graph-index out/llm_index.json")
    print()
    
    print("Step 4: Run SWEbench baseline (without graphs)")
    print("python3 ../SWE-bench/swebench/inference/run_api.py \\")
    print("  --dataset path/to/dataset \\")
    print("  --model gpt-4 \\")
    print("  --output-dir results_baseline")
    print()
    
    print("Step 5: Compare results")
    print("Compare the results in:")
    print("- results_with_graphs/results_0.jsonl")
    print("- results_baseline/results_0.jsonl")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 