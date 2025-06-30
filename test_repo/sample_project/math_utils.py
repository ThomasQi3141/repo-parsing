"""
Math utility functions for the sample project.
"""

def calculate_sum(numbers):
    """Calculate the sum of a list of numbers."""
    return sum(numbers)

def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

def calculate_standard_deviation(numbers):
    """Calculate the standard deviation of a list of numbers."""
    if not numbers:
        return 0
    mean = calculate_average(numbers)
    squared_diff_sum = sum((x - mean) ** 2 for x in numbers)
    return (squared_diff_sum / len(numbers)) ** 0.5 