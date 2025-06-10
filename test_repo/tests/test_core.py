"""
Tests for the core module.
"""

import unittest
from sample_project.core import calculate_sum, calculate_average

class TestCore(unittest.TestCase):
    def test_calculate_sum(self):
        self.assertEqual(calculate_sum([1, 2, 3, 4, 5]), 15)
        self.assertEqual(calculate_sum([]), 0)
        
    def test_calculate_average(self):
        self.assertEqual(calculate_average([1, 2, 3, 4, 5]), 3)
        self.assertEqual(calculate_average([]), 0)

if __name__ == '__main__':
    unittest.main() 