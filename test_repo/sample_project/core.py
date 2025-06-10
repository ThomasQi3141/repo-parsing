"""
Core functionality for the sample project.
"""

def calculate_sum(numbers):
    """
    Calculate the sum of a list of numbers.
    
    Args:
        numbers (list): List of numbers to sum
        
    Returns:
        float: Sum of all numbers
    """
    return sum(numbers)

def calculate_average(numbers):
    """
    Calculate the average of a list of numbers.
    
    Args:
        numbers (list): List of numbers
        
    Returns:
        float: Average of all numbers
    """
    if not numbers:
        return 0
    return sum(numbers) / len(numbers) 