#!/usr/bin/env python3

"""
Modified SWEbench runner that integrates graph information into LLM prompts.
This enhances the LLM's understanding of code relationships and call graphs.
"""

import json
import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Optional

# Add SWEbench to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'SWE-bench'))

from swebench.inference.run_api import (
    openai_inference, 
    anthropic_inference,
    parse_model_args,
    main as swebench_main
)
from swebench.inference.make_datasets.utils import extract_diff

def load_graph_index(graph_file: str) -> Dict:
    """Load the graph index from JSON file"""
    try:
        with open(graph_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Graph index file {graph_file} not found")
        return {}

def create_graph_context(graph_data: Dict, target_function: str = None) -> str:
    """Create a context string from graph data for LLM consumption"""
    if not graph_data:
        return ""
    
    context_parts = []
    
    # Add function details
    if "function_details" in graph_data:
        context_parts.append("## Function Details")
        for func_name, details in graph_data["function_details"].items():
            context_parts.append(f"### {func_name}")
            context_parts.append(f"- Line: {details.get('line', 'N/A')}")
            context_parts.append(f"- Code: {details.get('snippet', 'N/A')}")
            context_parts.append(f"- Type: {details.get('operation_type', 'N/A')}")
            context_parts.append("")
    
    # Add call relationships
    if "call_graphs" in graph_data:
        context_parts.append("## Function Call Relationships")
        for graph_name, call_graph in graph_data["call_graphs"].items():
            if call_graph:
                context_parts.append(f"### Graph: {graph_name}")
                for caller, callees in call_graph.items():
                    if callees:
                        context_parts.append(f"- **{caller}** calls: {', '.join(callees)}")
                context_parts.append("")
    
    # Add called-by relationships
    if "called_by" in graph_data:
        context_parts.append("## Function Called By Relationships")
        for graph_name, called_by in graph_data["called_by"].items():
            if called_by:
                context_parts.append(f"### Graph: {graph_name}")
                for callee, callers in called_by.items():
                    if callers:
                        context_parts.append(f"- **{callee}** is called by: {', '.join(callers)}")
                context_parts.append("")
    
    return "\n".join(context_parts)

def enhance_prompt_with_graphs(original_text: str, graph_context: str) -> str:
    """Enhance the original SWEbench prompt with graph information"""
    
    # Split into system and user messages (SWEbench format)
    parts = original_text.split("\n", 1)
    if len(parts) == 2:
        system_message, user_message = parts
    else:
        system_message = ""
        user_message = original_text
    
    # Enhanced system message with graph context
    enhanced_system = f"""You are an expert software engineer. You have access to detailed information about the codebase's function relationships and call graphs.

{graph_context}

{system_message}"""
    
    # Return in SWEbench format
    return f"{enhanced_system}\n{user_message}"

def run_swebench_with_graphs(
    dataset_name_or_path: str,
    split: str,
    model_name_or_path: str,
    output_dir: str,
    graph_index_path: str,
    shard_id: int = 0,
    num_shards: int = 1,
    model_args: Optional[Dict] = None,
    max_cost: Optional[float] = None,
):
    """
    Run SWEbench evaluation with enhanced graph information.
    
    Args:
        dataset_name_or_path: Path to SWEbench dataset
        split: Dataset split to evaluate
        model_name_or_path: LLM model to use
        output_dir: Directory for outputs
        graph_index_path: Path to graph index JSON file
        shard_id: Shard ID for parallel processing
        num_shards: Total number of shards
        model_args: Additional model arguments
        max_cost: Maximum cost limit
    """
    
    # Load graph information
    print(f"Loading graph information from {graph_index_path}")
    graph_data = load_graph_index(graph_index_path)
    
    if not graph_data:
        print("Warning: No graph data found, running standard SWEbench evaluation")
    
    # Create graph context
    graph_context = create_graph_context(graph_data)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load dataset
    from datasets import load_dataset, load_from_disk
    
    if os.path.exists(dataset_name_or_path):
        test_dataset = load_from_disk(dataset_name_or_path)
    else:
        test_dataset = load_dataset(dataset_name_or_path, split=split)
    
    # Filter dataset by shard
    if num_shards > 1:
        test_dataset = test_dataset.shard(num_shards, shard_id)
    
    # Enhance prompts with graph information
    def enhance_dataset(dataset):
        """Enhance dataset prompts with graph context"""
        enhanced_dataset = []
        
        for item in dataset:
            enhanced_item = item.copy()
            enhanced_item["text"] = enhance_prompt_with_graphs(
                item["text"], 
                graph_context
            )
            enhanced_dataset.append(enhanced_item)
        
        return enhanced_dataset
    
    print("Enhancing dataset with graph information...")
    enhanced_dataset = enhance_dataset(test_dataset)
    
    # Create output file
    output_file = os.path.join(output_dir, f"results_{shard_id}.jsonl")
    
    # Run inference based on model type
    if "claude" in model_name_or_path.lower():
        print(f"Running Anthropic inference with {model_name_or_path}")
        anthropic_inference(
            enhanced_dataset,
            model_name_or_path,
            output_file,
            model_args or {},
            set(),  # existing_ids
            max_cost,
        )
    else:
        print(f"Running OpenAI inference with {model_name_or_path}")
        openai_inference(
            enhanced_dataset,
            model_name_or_path,
            output_file,
            model_args or {},
            set(),  # existing_ids
            max_cost,
        )
    
    print(f"Results saved to {output_file}")

def main():
    """Main entry point with command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run SWEbench with graph-enhanced prompts")
    parser.add_argument("--dataset", required=True, help="SWEbench dataset path")
    parser.add_argument("--split", default="test", help="Dataset split")
    parser.add_argument("--model", required=True, help="LLM model name")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--graph-index", required=True, help="Path to graph index JSON")
    parser.add_argument("--shard-id", type=int, default=0, help="Shard ID")
    parser.add_argument("--num-shards", type=int, default=1, help="Total shards")
    parser.add_argument("--max-cost", type=float, help="Maximum cost limit")
    parser.add_argument("--temperature", type=float, default=0.2, help="Model temperature")
    parser.add_argument("--top-p", type=float, default=0.95, help="Model top-p")
    
    args = parser.parse_args()
    
    model_args = {
        "temperature": args.temperature,
        "top_p": args.top_p,
    }
    
    run_swebench_with_graphs(
        dataset_name_or_path=args.dataset,
        split=args.split,
        model_name_or_path=args.model,
        output_dir=args.output_dir,
        graph_index_path=args.graph_index,
        shard_id=args.shard_id,
        num_shards=args.num_shards,
        model_args=model_args,
        max_cost=args.max_cost,
    )

if __name__ == "__main__":
    main() 