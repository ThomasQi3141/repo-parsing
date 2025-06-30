"""
Data processing module that uses math utilities.
"""

from .math_utils import calculate_average, calculate_standard_deviation

class DataProcessor:
    def __init__(self, data):
        self.data = data
    
    def get_statistics(self):
        """Calculate basic statistics for the data."""
        return {
            'average': calculate_average(self.data),
            'std_dev': calculate_standard_deviation(self.data)
        }
    
    def normalize_data(self):
        """Normalize the data using z-score."""
        avg = calculate_average(self.data)
        std = calculate_standard_deviation(self.data)
        if std == 0:
            return self.data
        return [(x - avg) / std for x in self.data]

def process_dataset(data):
    """Process a dataset and return its statistics."""
    processor = DataProcessor(data)
    return processor.get_statistics() 