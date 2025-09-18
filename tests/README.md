# ControlBot Tests

This directory contains tests for the ControlBot project.

## Smoke Tests

The `test_smoke.py` file contains basic smoke tests that verify:

- All modules can be imported correctly
- Required dependencies are available
- Essential files exist
- Application fails gracefully without proper configuration
- Basic functionality works as expected

## Running Tests

### Local Testing

Run all tests locally:
```bash
python run_tests.py
```

Or run just the smoke tests:
```bash
python -m pytest tests/test_smoke.py -v
```

### GitHub Actions

Tests are automatically run on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

The CI pipeline includes:
- Python 3.11 and 3.12 compatibility
- Dependency installation
- Code linting with ruff
- Type checking with mypy
- Smoke tests
- Startup validation

## Test Structure

- `test_smoke.py` - Basic functionality tests
- `__init__.py` - Package initialization

## Adding New Tests

When adding new tests:

1. Follow the existing naming convention
2. Add appropriate docstrings
3. Use descriptive test names
4. Include both positive and negative test cases
5. Mock external dependencies when appropriate
