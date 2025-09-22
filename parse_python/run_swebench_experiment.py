#!/usr/bin/env python3

"""
Complete SWEbench experiment workflow with graph-enhanced evaluation.
This script runs the full pipeline:
1. Parse repository with Joern
2. Generate graph index
3. Run SWEbench baseline (without graphs)
4. Run SWEbench with graphs
5. Compare results
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional

def run_command(cmd: List[str], cwd: str = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    if cwd:
        print(f"Working directory: {cwd}")
    
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)
    
    if result.stdout:
        print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result

def parse_repository_with_joern(repo_path: str, output_dir: str = "out") -> bool:
    """Parse repository using Joern and generate .dot files"""
    print(f"Parsing repository: {repo_path}")
    
    # Update the script to use the correct repository
    script_path = os.path.join(os.path.dirname(__file__), '..', 'parse_cfg_with_joern.sh')
    
    # Create a temporary script with the correct repo path
    temp_script = f"""#!/bin/bash
set -e

JOERN_PATH=/usr/local/bin
CODE_DIR={repo_path}
OUT_DIR={output_dir}

# Check if Joern exists
if [ ! -x "$JOERN_PATH/joern" ]; then
  echo "Error: Joern not found at $JOERN_PATH/joern."
  exit 1
fi

# Check if code directory exists
if [ ! -d "$CODE_DIR" ]; then
  echo "Error: Code directory $CODE_DIR not found."
  exit 1
fi

# Clean up previous output
echo "Cleaning up previous output..."
rm -rf $OUT_DIR
mkdir $OUT_DIR

# Run Joern to generate and export CFG and call graph
echo "Importing code and exporting CFG using dumpcfg plugin..."
$JOERN_PATH/joern --src $CODE_DIR --language python --overwrite --run dumpcfg

echo "Exporting call graph using callgraph plugin..."
$JOERN_PATH/joern --src $CODE_DIR --language python --overwrite --run callgraph

echo "CFG and call graph export completed. Check $OUT_DIR/ for .dot files."
"""
    
    # Write temporary script
    temp_script_path = "/tmp/parse_repo_temp.sh"
    with open(temp_script_path, 'w') as f:
        f.write(temp_script)
    
    # Make executable and run
    os.chmod(temp_script_path, 0o755)
    
    try:
        result = run_command([temp_script_path])
        return result.returncode == 0
    finally:
        # Clean up
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)

def generate_graph_index(output_dir: str = "out") -> str:
    """Generate LLM-friendly graph index from .dot files"""
    print("Generating graph index...")
    
    script_path = os.path.join(os.path.dirname(__file__), 'dot_to_llm_index.py')
    result = run_command([sys.executable, script_path], cwd=os.path.dirname(__file__))
    
    if result.returncode == 0:
        json_path = os.path.join(output_dir, "llm_index.json")
        if os.path.exists(json_path):
            print(f"Graph index generated: {json_path}")
            return json_path
    
    print("Failed to generate graph index")
    return None

def run_swebench_evaluation(
    dataset_path: str,
    model_name: str,
    output_dir: str,
    graph_index_path: Optional[str] = None,
    baseline: bool = False
) -> str:
    """Run SWEbench evaluation with or without graph information"""
    
    if baseline:
        print("Running SWEbench baseline (without graphs)...")
        # Use original SWEbench
        cmd = [
            sys.executable, 
            os.path.join(os.path.dirname(__file__), '..', 'SWE-bench', 'swebench', 'inference', 'run_api.py'),
            "--dataset", dataset_path,
            "--split", "test",
            "--model", model_name,
            "--output-dir", os.path.join(output_dir, "baseline"),
            "--shard-id", "0",
            "--num-shards", "1"
        ]
    else:
        print("Running SWEbench with graph enhancement...")
        # Use our modified version
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), 'swebench_with_graphs.py'),
            "--dataset", dataset_path,
            "--split", "test", 
            "--model", model_name,
            "--output-dir", os.path.join(output_dir, "with_graphs"),
            "--graph-index", graph_index_path,
            "--shard-id", "0",
            "--num-shards", "1"
        ]
    
    result = run_command(cmd)
    
    if result.returncode == 0:
        results_file = os.path.join(output_dir, "baseline" if baseline else "with_graphs", "results_0.jsonl")
        if os.path.exists(results_file):
            print(f"Results saved: {results_file}")
            return results_file
    
    print("SWEbench evaluation failed")
    return None

def compare_results(baseline_file: str, enhanced_file: str) -> Dict:
    """Compare baseline and graph-enhanced results"""
    print("Comparing results...")
    
    def load_results(file_path: str) -> List[Dict]:
        results = []
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))
        return results
    
    baseline_results = load_results(baseline_file)
    enhanced_results = load_results(enhanced_file)
    
    # Simple comparison - count successful patches
    baseline_success = sum(1 for r in baseline_results if r.get("model_patch"))
    enhanced_success = sum(1 for r in enhanced_results if r.get("model_patch"))
    
    comparison = {
        "baseline_total": len(baseline_results),
        "enhanced_total": len(enhanced_results),
        "baseline_successful_patches": baseline_success,
        "enhanced_successful_patches": enhanced_success,
        "baseline_success_rate": baseline_success / len(baseline_results) if baseline_results else 0,
        "enhanced_success_rate": enhanced_success / len(enhanced_results) if enhanced_results else 0,
        "improvement": enhanced_success - baseline_success,
        "improvement_rate": (enhanced_success - baseline_success) / len(baseline_results) if baseline_results else 0
    }
    
    return comparison

def main():
    """Main experiment workflow"""
    parser = argparse.ArgumentParser(description="Run SWEbench experiment with graph enhancement")
    parser.add_argument("--repo-path", required=True, help="Path to repository to analyze")
    parser.add_argument("--dataset-path", required=True, help="Path to SWEbench dataset")
    parser.add_argument("--model", required=True, help="LLM model name (e.g., gpt-4, claude-3-sonnet)")
    parser.add_argument("--output-dir", default="experiment_results", help="Output directory for results")
    parser.add_argument("--skip-parsing", action="store_true", help="Skip repository parsing (use existing graphs)")
    parser.add_argument("--max-cost", type=float, help="Maximum cost limit for API calls")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Step 1: Parse repository (unless skipped)
    if not args.skip_parsing:
        print("=" * 50)
        print("STEP 1: Parsing repository with Joern")
        print("=" * 50)
        
        if not parse_repository_with_joern(args.repo_path):
            print("Failed to parse repository. Exiting.")
            return 1
    
    # Step 2: Generate graph index
    print("=" * 50)
    print("STEP 2: Generating graph index")
    print("=" * 50)
    
    graph_index_path = generate_graph_index()
    if not graph_index_path:
        print("Failed to generate graph index. Exiting.")
        return 1
    
    # Step 3: Run baseline evaluation
    print("=" * 50)
    print("STEP 3: Running baseline SWEbench evaluation")
    print("=" * 50)
    
    baseline_results = run_swebench_evaluation(
        args.dataset_path,
        args.model,
        args.output_dir,
        baseline=True
    )
    
    if not baseline_results:
        print("Baseline evaluation failed. Exiting.")
        return 1
    
    # Step 4: Run enhanced evaluation
    print("=" * 50)
    print("STEP 4: Running graph-enhanced SWEbench evaluation")
    print("=" * 50)
    
    enhanced_results = run_swebench_evaluation(
        args.dataset_path,
        args.model,
        args.output_dir,
        graph_index_path,
        baseline=False
    )
    
    if not enhanced_results:
        print("Enhanced evaluation failed. Exiting.")
        return 1
    
    # Step 5: Compare results
    print("=" * 50)
    print("STEP 5: Comparing results")
    print("=" * 50)
    
    comparison = compare_results(baseline_results, enhanced_results)
    
    # Save comparison results
    comparison_file = os.path.join(args.output_dir, "comparison.json")
    with open(comparison_file, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 50)
    print("EXPERIMENT RESULTS")
    print("=" * 50)
    print(f"Baseline successful patches: {comparison['baseline_successful_patches']}/{comparison['baseline_total']} ({comparison['baseline_success_rate']:.2%})")
    print(f"Enhanced successful patches: {comparison['enhanced_successful_patches']}/{comparison['enhanced_total']} ({comparison['enhanced_success_rate']:.2%})")
    print(f"Improvement: +{comparison['improvement']} patches ({comparison['improvement_rate']:.2%})")
    print(f"\nDetailed results saved to: {comparison_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 