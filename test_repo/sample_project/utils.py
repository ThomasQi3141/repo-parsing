"""
Utility functions for the sample project.
"""

import json
from typing import Any, Dict

def save_to_json(data: Dict[str, Any], filename: str) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data (dict): Data to save
        filename (str): Name of the file to save to
    """
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def load_from_json(filename: str) -> Dict[str, Any]:
    """
    Load data from a JSON file.
    
    Args:
        filename (str): Name of the file to load from
        
    Returns:
        dict: Loaded data
    """
    with open(filename, 'r') as f:
        return json.load(f) 