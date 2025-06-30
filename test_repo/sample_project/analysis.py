"""
Analysis module that combines data processing and math utilities.
"""

from .math_utils import calculate_sum, calculate_average
from .data_processor import DataProcessor, process_dataset

def analyze_data(data):
    """Perform comprehensive analysis on the data."""
    # First get basic statistics
    stats = process_dataset(data)
    
    # Then get normalized data
    processor = DataProcessor(data)
    normalized = processor.normalize_data()
    
    # Calculate additional metrics
    total = calculate_sum(data)
    mean = calculate_average(data)
    
    return {
        'basic_stats': stats,
        'normalized_data': normalized,
        'total': total,
        'mean': mean
    }

def compare_datasets(data1, data2):
    """Compare two datasets using various metrics."""
    stats1 = process_dataset(data1)
    stats2 = process_dataset(data2)
    
    return {
        'dataset1': stats1,
        'dataset2': stats2,
        'mean_difference': abs(stats1['average'] - stats2['average'])
    } 