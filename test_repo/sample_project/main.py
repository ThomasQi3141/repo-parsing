"""
Main module demonstrating the usage of all other modules.
"""

from .math_utils import calculate_average, calculate_standard_deviation
from .data_processor import DataProcessor
from .analysis import analyze_data, compare_datasets

def main():
    # Sample data
    data1 = [1, 2, 3, 4, 5]
    data2 = [2, 4, 6, 8, 10]
    
    # Demonstrate math utilities
    print("Math Utilities:")
    print(f"Average of data1: {calculate_average(data1)}")
    print(f"Standard deviation of data1: {calculate_standard_deviation(data1)}")
    
    # Demonstrate data processing
    print("\nData Processing:")
    processor = DataProcessor(data1)
    stats = processor.get_statistics()
    print(f"Statistics: {stats}")
    
    # Demonstrate analysis
    print("\nAnalysis:")
    analysis = analyze_data(data1)
    print(f"Analysis results: {analysis}")
    
    # Demonstrate comparison
    print("\nComparison:")
    comparison = compare_datasets(data1, data2)
    print(f"Comparison results: {comparison}")

if __name__ == "__main__":
    main() 