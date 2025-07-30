# Sample Project

A demonstration of a well-structured Python package.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from sample_project.core import calculate_sum, calculate_average

# Calculate sum of numbers
result = calculate_sum([1, 2, 3, 4, 5])
print(result)  # Output: 15

# Calculate average
avg = calculate_average([1, 2, 3, 4, 5])
print(avg)  # Output: 3.0
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

This project uses:

- Black for code formatting
- Flake8 for linting
- MyPy for type checking

## License

MIT License
